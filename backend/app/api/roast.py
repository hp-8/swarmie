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
    PitchParser,
    RoastReporter,
    SwarmRunner,
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
    tracker = UsageTracker()
    try:
        # Stage 1 — parse pitch
        job.status = "parsing"
        job.progress = 0.05
        _push_event(job, "status", {"status": job.status, "progress": job.progress})

        parser = PitchParser(tracker=tracker)
        pitch = parser.parse(job.pitch_text)
        job.parsed_pitch = pitch.to_dict()
        _push_event(job, "parsed_pitch", pitch.to_dict())
        if job.cancelled.is_set():
            raise RuntimeError("cancelled")

        # Stage 2 — generate archetypes
        job.status = "generating_archetypes"
        job.progress = 0.15
        _push_event(job, "status", {"status": job.status, "progress": job.progress})

        archgen = ArchetypeGenerator(tracker=tracker)
        archetypes = archgen.generate(pitch, n_archetypes=20)
        job.archetypes = [a.to_dict() for a in archetypes]
        _push_event(job, "archetypes", [a.to_dict() for a in archetypes])
        if job.cancelled.is_set():
            raise RuntimeError("cancelled")

        # Stage 3 — run swarm
        job.status = "running_swarm"
        job.progress = 0.25
        _push_event(job, "status", {"status": job.status, "progress": job.progress})

        completed = 0
        total = job.n_agents

        def _on_reaction(r: AgentReaction) -> None:
            nonlocal completed
            completed += 1
            job.reactions.append(r.to_dict())
            job.progress = 0.25 + (completed / max(total, 1)) * 0.6
            _push_event(job, "reaction", r.to_dict())

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
                )
            )
        finally:
            loop.close()

        if job.cancelled.is_set():
            raise RuntimeError("cancelled")

        # Stage 4 — synthesize report
        job.status = "reporting"
        job.progress = 0.9
        _push_event(job, "status", {"status": job.status, "progress": job.progress})

        reporter = RoastReporter(tracker=tracker)
        report = reporter.report(pitch, reactions)
        job.report = report.to_dict()
        _push_event(job, "report", report.to_dict())

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
    thread = threading.Thread(target=_run_pipeline, args=(job,), daemon=True)
    thread.start()

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
