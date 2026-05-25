"""
Roast API — fast founder-validation pipeline.

POST /api/roast            create + start a new roast job
GET  /api/roast/<job_id>   poll job status + result (when complete)
GET  /api/roast/<job_id>/stream   SSE feed of agent reactions as they land
DELETE /api/roast/<job_id> cancel + drop job (best-effort)

Jobs live in-process (no DB). They are short-lived (60s typical).
Production deployment will need a real job store (Redis) — out of scope today.
"""

from __future__ import annotations

import asyncio
import json
import logging
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from flask import Blueprint, Response, jsonify, request, stream_with_context

from ..config import Config
from ..services.swarm import (
    AgentReaction,
    ArchetypeGenerator,
    CHAT_SOFT_CAP,
    PitchParser,
    RoastReporter,
    SwarmRunner,
    chat_with_agent,
)
from ..utils.llm import UsageTracker

logger = logging.getLogger("swarmie.api.roast")

roast_bp = Blueprint("roast", __name__)


# ---------- in-process job store ----------

@dataclass
class RoastJob:
    job_id: str
    status: str = "pending"  # pending | parsing | generating_archetypes | running_swarm | reporting | completed | failed | cancelled
    progress: float = 0.0  # 0..1
    pitch_text: str = ""
    n_agents: int = 0
    error: str | None = None
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    # accumulating outputs
    parsed_pitch: dict | None = None
    archetypes: list[dict] = field(default_factory=list)
    reactions: list[dict] = field(default_factory=list)
    report: dict | None = None
    usage: dict | None = None

    # streaming
    event_queue: queue.Queue[dict] = field(default_factory=queue.Queue)
    cancelled: threading.Event = field(default_factory=threading.Event)

    # per-agent chat history: agent_id -> list[{role, content}]
    chats: dict[str, list[dict[str, str]]] = field(default_factory=dict)

    def to_dict(self, include_full: bool = False) -> dict[str, Any]:
        out: dict[str, Any] = {
            "job_id": self.job_id,
            "status": self.status,
            "progress": round(self.progress, 3),
            "n_agents": self.n_agents,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
        }
        if include_full or self.status == "completed":
            out["parsed_pitch"] = self.parsed_pitch
            out["archetypes"] = self.archetypes
            out["reactions"] = self.reactions
            out["report"] = self.report
            out["usage"] = self.usage
        return out


class _JobStore:
    def __init__(self):
        self._jobs: dict[str, RoastJob] = {}
        self._lock = threading.Lock()

    def create(self, pitch_text: str, n_agents: int) -> RoastJob:
        job_id = f"roast_{uuid.uuid4().hex[:16]}"
        job = RoastJob(job_id=job_id, pitch_text=pitch_text, n_agents=n_agents)
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> RoastJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def drop(self, job_id: str) -> bool:
        with self._lock:
            return self._jobs.pop(job_id, None) is not None

    def gc(self, max_age_seconds: int = 3600) -> int:
        """Drop jobs older than max_age_seconds. Returns count dropped."""
        now = time.time()
        dropped = 0
        with self._lock:
            stale_ids = [
                jid for jid, j in self._jobs.items()
                if (j.finished_at or j.started_at) < now - max_age_seconds
            ]
            for jid in stale_ids:
                del self._jobs[jid]
                dropped += 1
        return dropped


_store = _JobStore()


# ---------- background pipeline ----------

def _push_event(job: RoastJob, event_type: str, payload: Any) -> None:
    """Append an SSE-shaped event to the job queue."""
    try:
        job.event_queue.put_nowait({"type": event_type, "data": payload})
    except queue.Full:
        pass  # drop event if consumer is slow; status endpoint still works


def _run_pipeline(job: RoastJob) -> None:
    """Run the full pipeline on a background thread. Updates job in place."""
    print(f"[{job.job_id}] pipeline thread STARTED", flush=True)
    tracker = UsageTracker()
    t0 = time.time()

    def _stage(name: str, fraction: float) -> float:
        job.status = name
        job.progress = fraction
        _push_event(job, "status", {"status": name, "progress": fraction})
        elapsed = time.time() - t0
        print(f"[{job.job_id}] STAGE='{name}' elapsed={elapsed:.1f}s", flush=True)
        return time.time()

    try:
        # Stage 1 — parse pitch
        t = _stage("parsing", 0.05)
        parser = PitchParser(tracker=tracker)
        pitch = parser.parse(job.pitch_text)
        job.parsed_pitch = pitch.to_dict()
        _push_event(job, "parsed_pitch", pitch.to_dict())
        logger.info(f"[{job.job_id}] parsing done in {time.time()-t:.1f}s")
        if job.cancelled.is_set():
            raise RuntimeError("cancelled")

        # Stage 2 — generate archetypes
        t = _stage("generating_archetypes", 0.15)
        archgen = ArchetypeGenerator(tracker=tracker)
        archetypes = archgen.generate(pitch, n_archetypes=12)
        job.archetypes = [a.to_dict() for a in archetypes]
        _push_event(job, "archetypes", [a.to_dict() for a in archetypes])
        logger.info(
            f"[{job.job_id}] archetypes done in {time.time()-t:.1f}s "
            f"(got {len(archetypes)})"
        )
        if job.cancelled.is_set():
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

        runner = SwarmRunner(tracker=tracker)
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

        if job.cancelled.is_set():
            raise RuntimeError("cancelled")

        # Stage 4 — synthesize report
        t = _stage("reporting", 0.9)
        reporter = RoastReporter(tracker=tracker)
        report = reporter.report(pitch, reactions)
        job.report = report.to_dict()
        _push_event(job, "report", report.to_dict())
        logger.info(f"[{job.job_id}] report done in {time.time()-t:.1f}s")

        # Done
        job.status = "completed"
        job.progress = 1.0
        job.usage = tracker.summary()
        job.finished_at = time.time()
        _push_event(job, "status", {"status": job.status, "progress": 1.0})
        _push_event(job, "usage", job.usage)
        _push_event(job, "done", {"job_id": job.job_id})

    except Exception as exc:
        if job.cancelled.is_set():
            job.status = "cancelled"
        else:
            job.status = "failed"
            job.error = str(exc)
            logger.exception("roast pipeline failed for %s", job.job_id)
        job.finished_at = time.time()
        job.usage = tracker.summary()
        _push_event(job, "status", {"status": job.status, "error": job.error})


# ---------- routes ----------

@roast_bp.route("", methods=["POST"])
def create_roast():
    """Start a new roast job.

    Body: {"pitch": "<text>", "n_agents": <int, optional>}
    Returns: {"job_id": ...}
    """
    body = request.get_json(silent=True) or {}
    pitch_text = (body.get("pitch") or "").strip()
    if not pitch_text:
        return jsonify({"error": "pitch is required"}), 400
    if len(pitch_text) > 20000:
        return jsonify({"error": "pitch too long (max 20000 chars)"}), 400

    n_agents = int(body.get("n_agents") or Config.ROAST_AGENT_COUNT)
    n_agents = max(10, min(n_agents, 500))  # clamp 10..500

    job = _store.create(pitch_text=pitch_text, n_agents=n_agents)
    print(f"[{job.job_id}] creating background thread (n_agents={n_agents})", flush=True)
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
    return jsonify(job.to_dict()), 200


@roast_bp.route("/<job_id>/stream", methods=["GET"])
def stream_roast(job_id: str):
    """Server-sent events feed of pipeline events.

    Event types: status, parsed_pitch, archetypes, reaction, report, usage, done.
    Client should disconnect on `done` or on `status` with status == 'failed'/'cancelled'.
    """
    job = _store.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404

    @stream_with_context
    def generate():
        # Emit current snapshot so reconnecting clients catch up.
        yield _sse({"type": "status", "data": {
            "status": job.status, "progress": job.progress,
        }})
        while True:
            try:
                event = job.event_queue.get(timeout=30)
                yield _sse(event)
                if event["type"] == "done" or (
                    event["type"] == "status"
                    and event["data"].get("status") in ("failed", "cancelled")
                ):
                    return
            except queue.Empty:
                yield ": keepalive\n\n"
                if job.status in ("completed", "failed", "cancelled"):
                    return

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # nginx: disable buffering
    })


@roast_bp.route("/<job_id>", methods=["DELETE"])
def cancel_roast(job_id: str):
    """Cancel + drop a job (best-effort)."""
    job = _store.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    job.cancelled.set()
    _store.drop(job_id)
    return jsonify({"ok": True}), 200


def _sse(event: dict) -> str:
    """Format an SSE message."""
    return f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"


@roast_bp.route("/<job_id>/agents/<agent_id>/chat", methods=["POST"])
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
    except Exception as exc:
        logger.exception("chat failed for %s/%s", job_id, agent_id)
        return jsonify({"error": str(exc)}), 500

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    user_turns += 1

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
