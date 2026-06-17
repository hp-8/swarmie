"""Tests for the roast job store (in-memory + Redis backends).

The Redis backend is exercised against a tiny in-process fake that implements
only the commands RedisJobStore uses — enough to verify key naming, JSON
serialization, event ordering and TTL refresh without a real Redis.
"""

import json

from app.services.job_store import (
    InMemoryJobStore,
    RedisJobStore,
    RoastJob,
    make_store,
)


# --------------------------------------------------------------------------
# RoastJob serialization
# --------------------------------------------------------------------------

def test_roastjob_state_roundtrip_drops_transient_bytes():
    job = RoastJob(
        job_id="roast_abc", status="running_swarm", progress=0.5,
        pitch_text="we sell X", swarm_type="investor", source="deck",
        n_agents=42, deck_bytes=b"%PDF-1.4 raw",
        reactions=[{"agent_id": "a1"}], chats={"a1": [{"role": "user", "content": "hi"}]},
    )
    state = job.to_state()
    assert "deck_bytes" not in state  # transient: never serialized

    restored = RoastJob.from_state(state)
    assert restored.job_id == "roast_abc"
    assert restored.status == "running_swarm"
    assert restored.n_agents == 42
    assert restored.reactions == [{"agent_id": "a1"}]
    assert restored.chats == {"a1": [{"role": "user", "content": "hi"}]}
    assert restored.deck_bytes is None


# --------------------------------------------------------------------------
# In-memory backend
# --------------------------------------------------------------------------

def test_inmemory_create_get_drop():
    store = InMemoryJobStore()
    job = store.create(RoastJob(job_id="roast_1"))
    assert store.get("roast_1") is job
    assert store.get("missing") is None
    assert store.drop("roast_1") is True
    assert store.get("roast_1") is None
    assert store.drop("roast_1") is False


def test_inmemory_event_log_replay_by_cursor():
    store = InMemoryJobStore()
    store.create(RoastJob(job_id="roast_1"))
    store.append_event("roast_1", {"type": "status", "data": {"status": "parsing"}})
    store.append_event("roast_1", {"type": "reaction", "data": {"agent_id": "a1"}})

    assert len(store.get_events("roast_1", 0)) == 2
    # cursor advances: only new events after index 2
    assert store.get_events("roast_1", 2) == []
    store.append_event("roast_1", {"type": "done", "data": {}})
    tail = store.get_events("roast_1", 2)
    assert len(tail) == 1 and tail[0]["type"] == "done"


def test_inmemory_cancel_flag():
    store = InMemoryJobStore()
    store.create(RoastJob(job_id="roast_1"))
    assert store.is_cancelled("roast_1") is False
    store.set_cancelled("roast_1")
    assert store.is_cancelled("roast_1") is True


# --------------------------------------------------------------------------
# Redis backend (against a minimal fake client)
# --------------------------------------------------------------------------

class _FakePipeline:
    def __init__(self, client):
        self._client = client
        self._ops = []

    def rpush(self, key, value):
        self._ops.append(("rpush", key, value))
        return self

    def expire(self, key, ttl):
        self._ops.append(("expire", key, ttl))
        return self

    def execute(self):
        for op in self._ops:
            if op[0] == "rpush":
                self._client.rpush(op[1], op[2])
            elif op[0] == "expire":
                self._client.expire(op[1], op[2])
        self._ops = []


class _FakeRedis:
    def __init__(self):
        self.kv = {}
        self.lists = {}
        self.ttls = {}

    def set(self, key, value, ex=None):
        self.kv[key] = value
        if ex is not None:
            self.ttls[key] = ex

    def get(self, key):
        return self.kv.get(key)

    def delete(self, *keys):
        n = 0
        for k in keys:
            if k in self.kv or k in self.lists:
                n += 1
            self.kv.pop(k, None)
            self.lists.pop(k, None)
            self.ttls.pop(k, None)
        return n

    def rpush(self, key, value):
        self.lists.setdefault(key, []).append(value)

    def lrange(self, key, start, end):
        items = self.lists.get(key, [])
        if end == -1:
            return items[start:]
        return items[start:end + 1]

    def expire(self, key, ttl):
        self.ttls[key] = ttl

    def exists(self, key):
        return 1 if (key in self.kv or key in self.lists) else 0

    def pipeline(self):
        return _FakePipeline(self)


def test_redis_persist_get_uses_namespaced_key_and_json():
    fake = _FakeRedis()
    store = RedisJobStore(fake, ttl_seconds=999)
    store.create(RoastJob(job_id="roast_x", status="parsing", n_agents=7))

    assert "roast:job:roast_x" in fake.kv
    assert fake.ttls["roast:job:roast_x"] == 999
    assert json.loads(fake.kv["roast:job:roast_x"])["n_agents"] == 7

    got = store.get("roast_x")
    assert got is not None and got.status == "parsing" and got.n_agents == 7
    assert store.get("nope") is None


def test_redis_event_log_and_cancel():
    fake = _FakeRedis()
    store = RedisJobStore(fake, ttl_seconds=10)
    store.create(RoastJob(job_id="roast_x"))

    store.append_event("roast_x", {"type": "status", "data": {"status": "parsing"}})
    store.append_event("roast_x", {"type": "done", "data": {}})
    events = store.get_events("roast_x", 0)
    assert [e["type"] for e in events] == ["status", "done"]
    assert store.get_events("roast_x", 2) == []
    assert fake.ttls["roast:ev:roast_x"] == 10

    assert store.is_cancelled("roast_x") is False
    store.set_cancelled("roast_x")
    assert store.is_cancelled("roast_x") is True

    assert store.drop("roast_x") is True
    assert store.get("roast_x") is None


def test_redis_get_returns_none_on_corrupt_state():
    fake = _FakeRedis()
    fake.set("roast:job:bad", "{not json")
    store = RedisJobStore(fake, ttl_seconds=10)
    assert store.get("bad") is None


# --------------------------------------------------------------------------
# Factory
# --------------------------------------------------------------------------

def test_make_store_falls_back_to_inmemory_without_url():
    assert isinstance(make_store(None, 3600), InMemoryJobStore)
    assert isinstance(make_store("", 3600), InMemoryJobStore)


def test_make_store_falls_back_when_redis_unreachable():
    # Bogus URL → connection/ping fails → in-memory fallback (never raises).
    store = make_store("redis://127.0.0.1:1/0", 3600)
    assert isinstance(store, InMemoryJobStore)
