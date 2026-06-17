"""
Roast API — fast founder-validation pipeline.

POST /api/roast            create + start a new roast job
GET  /api/roast/<job_id>   poll job status + result (when complete)
GET  /api/roast/<job_id>/stream   SSE feed of agent reactions as they land
DELETE /api/roast/<job_id> cancel + drop job (best-effort)

Job state + the SSE event log live in the job store (see services/job_store):
Redis when REDIS_URL is set (survives worker restart / redeploy / idle
spin-down), in-process otherwise. The pipeline still runs in a daemon thread
in this web worker — Redis is a state store, not a task queue.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
import uuid
from typing import Any

from flask import Blueprint, Response, jsonify, request, stream_with_context

from ..config import Config
from ..extensions import limiter
from ..services.job_store import RoastJob, make_store
from ..services.swarm import (
    AgentReaction,
    CHAT_SOFT_CAP,
    CostCeilingExceeded,
    DEFAULT_SWARM,
    DeckEvaluator,
    DeckExtractor,
    DeckLoadError,
    SWARMS,
    chat_with_agent,
    get_swarm,
    load_pdf,
)
from ..utils.llm import UsageTracker

logger = logging.getLogger("swarmie.api.roast")

roast_bp = Blueprint("roast", __name__)


# ---------- job store ----------

# Redis-backed when REDIS_URL is set (survives worker restart / redeploy /
# idle spin-down — the cause of "job not found" 404s); in-process otherwise.
_store = make_store(Config.REDIS_URL, Config.ROAST_JOB_TTL)


def _new_job(pitch_text: str, n_agents: int, swarm_type: str = DEFAULT_SWARM,
             source: str = "text", deck_bytes: bytes | None = None) -> RoastJob:
    job_id = f"roast_{uuid.uuid4().hex[:16]}"
    return _store.create(RoastJob(
        job_id=job_id, pitch_text=pitch_text, n_agents=n_agents,
        swarm_type=swarm_type, source=source, deck_bytes=deck_bytes,
    ))


def _is_stale(job: RoastJob) -> bool:
    """A non-terminal job whose pipeline thread died (e.g. with the worker):
    no progress for ROAST_STALE_SECONDS. Surfaced as failed instead of stuck."""
    if job.status in ("completed", "failed", "cancelled"):
        return False
    return (time.time() - (job.finished_at or job.started_at)) > Config.ROAST_STALE_SECONDS


# ---------- background pipeline ----------

# Pipeline errors raised with a message written FOR the user keep it verbatim;
# everything else (provider failures, retry exhaustion, bugs) maps to a generic
# line so internals never reach the client. Raw tracebacks are always logged.
_USER_FACING_ERROR_PREFIXES = ("Couldn't read the deck", "cancelled")


def _public_error_message(exc: Exception) -> str:
    """User-safe error string for job.error / SSE status events."""
    if isinstance(exc, CostCeilingExceeded):
        return (
            "This run was stopped early because it hit the per-run cost limit. "
            "Try again with fewer agents."
        )
    msg = str(exc)
    if msg.startswith(_USER_FACING_ERROR_PREFIXES):
        return msg
    return (
        "The run hit an unexpected error on our end (the AI provider may be "
        "overloaded). Please try again in a few minutes."
    )


def _push_event(job: RoastJob, event_type: str, payload: Any) -> None:
    """Append an SSE-shaped event to the job's replayable event log."""
    _store.append_event(job.job_id, {"type": event_type, "data": payload})


def _run_pipeline(job: RoastJob) -> None:
    """Run the full pipeline on a background thread. Updates job in place."""
    print(f"[{job.job_id}] pipeline thread STARTED", flush=True)
    spec = get_swarm(job.swarm_type)
    tracker = UsageTracker()
    t0 = time.time()

    def _stage(name: str, fraction: float) -> float:
        job.status = name
        job.progress = fraction
        _store.persist(job)  # checkpoint status before the (slow) stage work
        _push_event(job, "status", {"status": name, "progress": fraction})
        elapsed = time.time() - t0
        print(f"[{job.job_id}] STAGE='{name}' elapsed={elapsed:.1f}s", flush=True)
        return time.time()

    try:
        # Stage 1 — parse pitch (text) OR read deck (PDF upload)
        t = _stage("parsing", 0.05)
        deck_slides: list = []
        if job.source == "deck":
            try:
                pages = load_pdf(job.deck_bytes or b"")
            except DeckLoadError as exc:
                raise RuntimeError(f"Couldn't read the deck: {exc}. Paste the text instead.")
            finally:
                job.deck_bytes = None  # discard raw bytes immediately (privacy)
            deck_read = DeckExtractor(tracker=tracker).extract(pages)
            pitch = deck_read.pitch
            deck_slides = deck_read.slides
            job.deck_slides = [s.to_dict() for s in deck_slides]
            _push_event(job, "deck_slides", job.deck_slides)
        else:
            parser = spec.parser_cls(tracker=tracker)
            pitch = parser.parse(job.pitch_text)
        job.parsed_pitch = pitch.to_dict()
        _store.persist(job)
        _push_event(job, "parsed_pitch", pitch.to_dict())
        logger.info(f"[{job.job_id}] parsing done in {time.time()-t:.1f}s")
        if _store.is_cancelled(job.job_id):
            raise RuntimeError("cancelled")

        # Stage 2 — generate archetypes
        t = _stage("generating_archetypes", 0.15)
        archgen = spec.archgen_cls(tracker=tracker)
        archetypes = archgen.generate(pitch, n_archetypes=spec.n_archetypes)
        job.archetypes = [a.to_dict() for a in archetypes]
        _store.persist(job)
        _push_event(job, "archetypes", [a.to_dict() for a in archetypes])
        logger.info(
            f"[{job.job_id}] archetypes done in {time.time()-t:.1f}s "
            f"(got {len(archetypes)})"
        )
        if _store.is_cancelled(job.job_id):
            raise RuntimeError("cancelled")

        # Stage 3 — run swarm
        t = _stage("running_swarm", 0.25)
        completed = 0
        total = job.n_agents

        def _on_thinking(agent_id: str, arch, action: str) -> None:
            _push_event(job, "thinking", {
                "agent_id": agent_id,
                "archetype_id": arch.id,
                "segment": arch.segment,
                "name": arch.name,
                "tone": arch.tone,
                "action": action,
            })

        def _on_reaction(r: AgentReaction) -> None:
            nonlocal completed
            completed += 1
            job.reactions.append(r.to_dict())
            job.progress = 0.25 + (completed / max(total, 1)) * 0.6
            _push_event(job, "reaction", r.to_dict())
            if completed % 10 == 0:
                logger.info(
                    f"[{job.job_id}] swarm progress {completed}/{total} "
                    f"cost=${tracker.total_cost_usd:.4f}"
                )

        runner = spec.runner_cls(tracker=tracker)
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            reactions = loop.run_until_complete(
                runner.run(
                    pitch=pitch,
                    archetypes=archetypes,
                    n_agents=job.n_agents,
                    on_reaction=_on_reaction,
                    on_thinking=_on_thinking,
                )
            )
        finally:
            loop.close()
        logger.info(
            f"[{job.job_id}] swarm done in {time.time()-t:.1f}s "
            f"(got {len(reactions)} reactions)"
        )

        if _store.is_cancelled(job.job_id):
            raise RuntimeError("cancelled")

        # Stage 3.5 — deck diagnosis (deck uploads only): pitch-intelligence EVALUATE
        deck_diagnosis = None
        if job.source == "deck" and deck_slides:
            t = _stage("evaluating", 0.85)
            diagnosis = DeckEvaluator(tracker=tracker).evaluate(deck_slides, getattr(pitch, "stage", ""))
            deck_diagnosis = diagnosis.to_dict()
            _push_event(job, "deck_diagnosis", deck_diagnosis)
            logger.info(f"[{job.job_id}] deck diagnosis done in {time.time()-t:.1f}s")
            if _store.is_cancelled(job.job_id):
                raise RuntimeError("cancelled")

        # Stage 4 — synthesize report
        t = _stage("reporting", 0.9)
        reporter = spec.reporter_cls(tracker=tracker)
        report = reporter.report(pitch, reactions)
        if deck_diagnosis is not None:
            report.deck_diagnosis = deck_diagnosis
        job.report = report.to_dict()
        _push_event(job, "report", report.to_dict())
        logger.info(f"[{job.job_id}] report done in {time.time()-t:.1f}s")

        # Done — persist the full result (all reactions/report) before signalling.
        job.status = "completed"
        job.progress = 1.0
        job.usage = tracker.summary()
        job.finished_at = time.time()
        _store.persist(job)
        _push_event(job, "status", {"status": job.status, "progress": 1.0})
        _push_event(job, "usage", job.usage)
        _push_event(job, "done", {"job_id": job.job_id})

    except Exception as exc:
        if _store.is_cancelled(job.job_id):
            job.status = "cancelled"
        else:
            job.status = "failed"
            job.error = _public_error_message(exc)
            logger.exception("roast pipeline failed for %s", job.job_id)
        job.finished_at = time.time()
        job.usage = tracker.summary()
        _store.persist(job)
        _push_event(job, "status", {"status": job.status, "error": job.error})


# ---------- routes ----------

@roast_bp.route("/swarms", methods=["GET"])
def list_swarms():
    """List available swarms for the input picker."""
    return jsonify({
        "swarms": [SWARMS[k].to_dict() for k in SWARMS],
        "default": DEFAULT_SWARM,
    }), 200


MAX_DECK_BYTES = 25 * 1024 * 1024  # 25 MB


@roast_bp.route("", methods=["POST"])
@limiter.limit(lambda: Config.RATE_LIMIT_ROAST)  # callable: env/test overridable
def create_roast():
    """Start a new roast job.

    Two request shapes:
      - JSON:      {"pitch": "<text>", "n_agents": <int?>, "swarm_type": <str?>}
      - multipart: file=<deck.pdf>, swarm_type=investor, n_agents=<int?>  (deck path)
    Returns: {"job_id": ...}
    """
    upload = request.files.get("file") if request.files else None

    if upload is not None:
        # --- deck upload path (investor swarm) ---
        swarm_type = (request.form.get("swarm_type") or "investor").strip().lower()
        if swarm_type not in SWARMS:
            return jsonify({"error": f"unknown swarm_type '{swarm_type}'"}), 400

        filename = (upload.filename or "").lower()
        if not (filename.endswith(".pdf") or (upload.mimetype or "") == "application/pdf"):
            return jsonify({"error": "only PDF deck uploads are supported"}), 400

        data = upload.read()
        if not data:
            return jsonify({"error": "uploaded file is empty"}), 400
        if len(data) > MAX_DECK_BYTES:
            return jsonify({"error": "deck too large (max 25 MB)"}), 400

        try:
            n_agents = int(request.form.get("n_agents") or Config.ROAST_AGENT_COUNT)
        except (TypeError, ValueError):
            n_agents = Config.ROAST_AGENT_COUNT
        n_agents = max(10, min(n_agents, 500))

        job = _new_job(
            pitch_text="", n_agents=n_agents, swarm_type=swarm_type,
            source="deck", deck_bytes=data,
        )
    else:
        # --- pasted-text path ---
        body = request.get_json(silent=True) or {}
        pitch_text = (body.get("pitch") or "").strip()
        if not pitch_text:
            return jsonify({"error": "pitch is required"}), 400
        if len(pitch_text) > 20000:
            return jsonify({"error": "pitch too long (max 20000 chars)"}), 400

        swarm_type = (body.get("swarm_type") or DEFAULT_SWARM).strip().lower()
        if swarm_type not in SWARMS:
            return jsonify({"error": f"unknown swarm_type '{swarm_type}'"}), 400

        n_agents = int(body.get("n_agents") or Config.ROAST_AGENT_COUNT)
        n_agents = max(10, min(n_agents, 500))  # clamp 10..500

        job = _new_job(pitch_text=pitch_text, n_agents=n_agents, swarm_type=swarm_type)

    print(f"[{job.job_id}] creating background thread (n_agents={n_agents}, source={job.source})", flush=True)
    thread = threading.Thread(target=_run_pipeline, args=(job,), daemon=True)
    thread.start()
    print(f"[{job.job_id}] thread.start() returned; thread.is_alive={thread.is_alive()}", flush=True)

    return jsonify({"job_id": job.job_id, "status": job.status}), 202


@roast_bp.route("/<job_id>", methods=["GET"])
def get_roast(job_id: str):
    """Poll job status. Returns full result once status == 'completed'."""
    job = _store.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    if _is_stale(job):
        job.status = "failed"
        job.error = _STALE_ERROR
    return jsonify(job.to_dict()), 200


# Stream tuning: poll the event log this often for new events (also the
# keepalive cadence). Kept >=1s to stay within Redis free-tier command budgets.
_STREAM_POLL_SECONDS = 1.0
_STALE_ERROR = (
    "This run was interrupted before it finished (our server may have restarted). "
    "Please start a new roast."
)


@roast_bp.route("/<job_id>/stream", methods=["GET"])
def stream_roast(job_id: str):
    """Server-sent events feed of pipeline events.

    Replays the full event log from the start (so a reconnecting or late client
    catches up on everything), then tails new events. Event types: status,
    parsed_pitch, archetypes, thinking, reaction, deck_slides, deck_diagnosis,
    report, usage, done. Client disconnects on `done` or a failed/cancelled
    `status`.
    """
    job = _store.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404

    @stream_with_context
    def generate():
        # Initial snapshot so a client that connects before any event isn't blank.
        yield _sse({"type": "status", "data": {
            "status": job.status, "progress": job.progress,
        }})
        cursor = 0
        while True:
            events = _store.get_events(job_id, cursor)
            if events:
                cursor += len(events)
                for event in events:
                    yield _sse(event)
                    if event["type"] == "done" or (
                        event["type"] == "status"
                        and event["data"].get("status") in ("failed", "cancelled")
                    ):
                        return
                continue
            # No new events — keepalive + terminal/staleness checks.
            yield ": keepalive\n\n"
            snap = _store.get(job_id)
            if snap is None:
                return  # job expired / dropped
            if snap.status in ("completed", "failed", "cancelled"):
                return
            if _is_stale(snap):
                yield _sse({"type": "status", "data": {
                    "status": "failed", "error": _STALE_ERROR,
                }})
                return
            time.sleep(_STREAM_POLL_SECONDS)

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # nginx: disable buffering
    })


@roast_bp.route("/<job_id>", methods=["DELETE"])
def cancel_roast(job_id: str):
    """Cancel a job (best-effort). Sets the cancel flag the pipeline polls; the
    running pipeline then marks the job cancelled. The job state is left to
    expire via TTL so a reconnecting client sees `cancelled`, not a 404."""
    job = _store.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    _store.set_cancelled(job_id)
    if job.status in ("completed", "failed", "cancelled"):
        _store.drop(job_id)  # nothing running; safe to reclaim immediately
    return jsonify({"ok": True}), 200


def _sse(event: dict) -> str:
    """Format an SSE message."""
    return f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"


@roast_bp.route("/<job_id>/agents/<agent_id>/chat", methods=["POST"])
@limiter.limit(lambda: Config.RATE_LIMIT_CHAT)  # callable: env/test overridable
def chat_agent(job_id: str, agent_id: str):
    """Send a follow-up message to a specific agent.

    Body: {"message": "<text>"}
    Returns: {"reply": "<text>", "turns": <int>, "soft_cap": <int>, "over_cap": <bool>}
    """
    job = _store.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    if job.status != "completed":
        return jsonify({"error": "job not complete"}), 400

    body = request.get_json(silent=True) or {}
    message = (body.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message required"}), 400
    if len(message) > 2000:
        return jsonify({"error": "message too long (max 2000)"}), 400

    # locate reaction + archetype
    reaction = next((r for r in job.reactions if r.get("agent_id") == agent_id), None)
    if not reaction:
        return jsonify({"error": "agent not found"}), 404
    archetype = next((a for a in job.archetypes if a.get("id") == reaction.get("archetype_id")), None)
    if not archetype:
        return jsonify({"error": "archetype missing"}), 404

    history = job.chats.setdefault(agent_id, [])
    user_turns = sum(1 for t in history if t.get("role") == "user")

    tracker = UsageTracker()
    try:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            reply = loop.run_until_complete(
                chat_with_agent(
                    pitch=job.parsed_pitch or {},
                    archetype=archetype,
                    original_reaction=reaction,
                    history=history,
                    user_message=message,
                    tracker=tracker,
                )
            )
        finally:
            loop.close()
    except Exception:
        logger.exception("chat failed for %s/%s", job_id, agent_id)
        return jsonify({
            "error": "The agent couldn't reply just now (our AI provider hiccuped). "
                     "Please try again in a moment.",
        }), 500

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    user_turns += 1
    _store.persist(job)  # persist chat history (no-op for in-memory store)

    return jsonify({
        "reply": reply,
        "turns": user_turns,
        "soft_cap": CHAT_SOFT_CAP,
        "over_cap": user_turns > CHAT_SOFT_CAP,
        "cost_usd": round(tracker.total_cost_usd, 6),
    }), 200


@roast_bp.route("/<job_id>/agents/<agent_id>/chat", methods=["GET"])
def get_chat(job_id: str, agent_id: str):
    """Fetch existing chat history for an agent (used on reload)."""
    job = _store.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    history = job.chats.get(agent_id, [])
    user_turns = sum(1 for t in history if t.get("role") == "user")
    return jsonify({
        "history": history,
        "turns": user_turns,
        "soft_cap": CHAT_SOFT_CAP,
        "over_cap": user_turns > CHAT_SOFT_CAP,
    }), 200
