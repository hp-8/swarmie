"""
Roast job store — pluggable persistence for the roast pipeline.

Two backends, chosen at import time by whether ``REDIS_URL`` is set:

  - InMemoryJobStore (default): jobs + event logs live in process RAM.
    Identical to the original behaviour; used for local dev, tests and any
    deploy without Redis configured.
  - RedisJobStore: jobs, the per-job SSE event log, and the cancel flag all
    live in Redis with a TTL. Survives a worker restart / redeploy / idle
    spin-down, which is what kills the in-memory store and produces the
    "job not found" 404 on the /stream and poll endpoints.

The background pipeline still runs in-process (a daemon thread in the web
worker). Redis here is a *state store*, not a task queue: a mid-run worker
crash still ends that live run, but the job state persists and reconnecting
clients see a clean terminal state instead of a 404. Stale non-terminal jobs
(thread died, no terminal event) are surfaced as failed via ``stale_seconds``.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("swarmie.job_store")

# Bumped on every event push so the SSE consumer can replay from a cursor.
_TERMINAL_STATUSES = ("completed", "failed", "cancelled")


@dataclass
class RoastJob:
    """Working state for a single roast run.

    The pipeline thread mutates this object in place; the store persists a
    snapshot (``to_state``) at each meaningful transition. ``deck_bytes`` is
    transient (raw upload) and is never serialized.
    """

    job_id: str
    status: str = "pending"
    progress: float = 0.0
    pitch_text: str = ""
    swarm_type: str = ""
    source: str = "text"  # "text" | "deck"
    n_agents: int = 0
    error: str | None = None
    deck_bytes: bytes | None = None  # transient, never persisted
    deck_slides: list[dict] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    parsed_pitch: dict | None = None
    archetypes: list[dict] = field(default_factory=list)
    reactions: list[dict] = field(default_factory=list)
    report: dict | None = None
    usage: dict | None = None

    # per-agent chat history: agent_id -> list[{role, content}]
    chats: dict[str, list[dict[str, str]]] = field(default_factory=dict)

    def to_dict(self, include_full: bool = False) -> dict[str, Any]:
        out: dict[str, Any] = {
            "job_id": self.job_id,
            "status": self.status,
            "progress": round(self.progress, 3),
            "swarm_type": self.swarm_type,
            "source": self.source,
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
            out["deck_slides"] = self.deck_slides
        return out

    def to_state(self) -> dict[str, Any]:
        """Full serializable snapshot (everything except transient fields)."""
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "pitch_text": self.pitch_text,
            "swarm_type": self.swarm_type,
            "source": self.source,
            "n_agents": self.n_agents,
            "error": self.error,
            "deck_slides": self.deck_slides,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "parsed_pitch": self.parsed_pitch,
            "archetypes": self.archetypes,
            "reactions": self.reactions,
            "report": self.report,
            "usage": self.usage,
            "chats": self.chats,
        }

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> "RoastJob":
        job = cls(job_id=state["job_id"])
        for key, value in state.items():
            if hasattr(job, key):
                setattr(job, key, value)
        return job


class InMemoryJobStore:
    """Process-local store. Jobs vanish on restart (original behaviour)."""

    def __init__(self) -> None:
        self._jobs: dict[str, RoastJob] = {}
        self._events: dict[str, list[dict]] = {}
        self._cancelled: set[str] = set()
        self._lock = threading.Lock()

    def create(self, job: RoastJob) -> RoastJob:
        with self._lock:
            self._jobs[job.job_id] = job
            self._events.setdefault(job.job_id, [])
        return job

    def get(self, job_id: str) -> RoastJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def persist(self, job: RoastJob) -> None:
        # The pipeline mutates the live object the store already holds.
        with self._lock:
            self._jobs[job.job_id] = job

    def drop(self, job_id: str) -> bool:
        with self._lock:
            self._events.pop(job_id, None)
            self._cancelled.discard(job_id)
            return self._jobs.pop(job_id, None) is not None

    def append_event(self, job_id: str, event: dict) -> None:
        with self._lock:
            self._events.setdefault(job_id, []).append(event)

    def get_events(self, job_id: str, start: int) -> list[dict]:
        with self._lock:
            return list(self._events.get(job_id, [])[start:])

    def set_cancelled(self, job_id: str) -> None:
        with self._lock:
            self._cancelled.add(job_id)

    def is_cancelled(self, job_id: str) -> bool:
        with self._lock:
            return job_id in self._cancelled


class RedisJobStore:
    """Redis-backed store. State survives restarts; keys carry a TTL."""

    def __init__(self, client, ttl_seconds: int) -> None:
        self._r = client
        self._ttl = ttl_seconds

    def _job_key(self, job_id: str) -> str:
        return f"roast:job:{job_id}"

    def _events_key(self, job_id: str) -> str:
        return f"roast:ev:{job_id}"

    def _cancel_key(self, job_id: str) -> str:
        return f"roast:cancel:{job_id}"

    def create(self, job: RoastJob) -> RoastJob:
        self.persist(job)
        return job

    def get(self, job_id: str) -> RoastJob | None:
        raw = self._r.get(self._job_key(job_id))
        if raw is None:
            return None
        try:
            return RoastJob.from_state(json.loads(raw))
        except (json.JSONDecodeError, KeyError):
            logger.warning("corrupt job state for %s", job_id)
            return None

    def persist(self, job: RoastJob) -> None:
        self._r.set(self._job_key(job.job_id), json.dumps(job.to_state()), ex=self._ttl)

    def drop(self, job_id: str) -> bool:
        deleted = self._r.delete(
            self._job_key(job_id), self._events_key(job_id), self._cancel_key(job_id)
        )
        return bool(deleted)

    def append_event(self, job_id: str, event: dict) -> None:
        key = self._events_key(job_id)
        pipe = self._r.pipeline()
        pipe.rpush(key, json.dumps(event))
        pipe.expire(key, self._ttl)
        pipe.execute()

    def get_events(self, job_id: str, start: int) -> list[dict]:
        raw = self._r.lrange(self._events_key(job_id), start, -1)
        out = []
        for item in raw:
            try:
                out.append(json.loads(item))
            except json.JSONDecodeError:
                continue
        return out

    def set_cancelled(self, job_id: str) -> None:
        self._r.set(self._cancel_key(job_id), "1", ex=self._ttl)

    def is_cancelled(self, job_id: str) -> bool:
        return bool(self._r.exists(self._cancel_key(job_id)))


def make_store(redis_url: str | None, ttl_seconds: int):
    """Pick a backend. Redis when a URL is given and reachable, else in-memory."""
    if not redis_url:
        logger.info("roast job store: in-memory (no REDIS_URL)")
        return InMemoryJobStore()
    try:
        import redis  # imported lazily so the dep is optional in dev/test

        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        client.ping()
        logger.info("roast job store: Redis (ttl=%ss)", ttl_seconds)
        return RedisJobStore(client, ttl_seconds)
    except Exception:
        logger.exception("Redis unavailable — falling back to in-memory job store")
        return InMemoryJobStore()
