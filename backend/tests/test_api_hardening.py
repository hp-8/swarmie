"""
API hardening tests — rate limiting, CORS allowlist, JSON error handling.

No LLM calls: rate-limit tests use requests that fail validation (400/404)
before any pipeline work starts; the limiter counts them all the same because
hits are deducted before the view runs.
"""

from __future__ import annotations

import pytest

from app import create_app
from app.config import Config, _csv
from app.extensions import limiter


def _make_app(**overrides):
    """Fresh app from the real factory; per-test config via Config subclass."""

    class _TestConfig(Config):
        TESTING = True

    for key, value in overrides.items():
        setattr(_TestConfig, key, value)
    return create_app(_TestConfig)


@pytest.fixture(autouse=True)
def _reset_limiter_storage():
    """Limiter storage is process-global (memory://); isolate counters per test."""
    try:
        limiter.reset()
    except Exception:
        pass
    yield


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def test_roast_create_rate_limit_fires_with_json_error(monkeypatch):
    monkeypatch.setattr(Config, "RATE_LIMIT_ROAST", "2 per hour")
    app = _make_app(RATELIMIT_ENABLED=True)
    client = app.test_client()

    # First two requests pass the limiter (fail validation with 400 — no pipeline).
    for _ in range(2):
        resp = client.post("/api/roast", json={})
        assert resp.status_code == 400

    resp = client.post("/api/roast", json={})
    assert resp.status_code == 429
    body = resp.get_json()
    assert body is not None, "429 must be JSON"
    assert set(body.keys()) == {"error"}
    assert "roast limit" in body["error"]
    assert "try again" in body["error"].lower()
    assert "Traceback" not in resp.get_data(as_text=True)


def test_chat_rate_limit_fires_with_json_error(monkeypatch):
    monkeypatch.setattr(Config, "RATE_LIMIT_CHAT", "2 per hour")
    app = _make_app(RATELIMIT_ENABLED=True)
    client = app.test_client()

    url = "/api/roast/nope/agents/agent_0001/chat"
    for _ in range(2):
        resp = client.post(url, json={"message": "hi"})
        assert resp.status_code == 404  # unknown job; still counts against the limit

    resp = client.post(url, json={"message": "hi"})
    assert resp.status_code == 429
    body = resp.get_json()
    assert body is not None
    assert "chat limit" in body["error"]


def test_stream_and_read_endpoints_are_not_rate_limited(monkeypatch):
    """A roast legitimately holds one long SSE connection + polls; never 429 these."""
    monkeypatch.setattr(Config, "RATE_LIMIT_ROAST", "1 per hour")
    monkeypatch.setattr(Config, "RATE_LIMIT_CHAT", "1 per hour")
    app = _make_app(RATELIMIT_ENABLED=True)
    client = app.test_client()

    for _ in range(10):
        assert client.get("/api/roast/swarms").status_code == 200
        assert client.get("/api/roast/unknown-job").status_code == 404
        assert client.get("/api/roast/unknown-job/stream").status_code == 404
        assert client.get("/api/roast/unknown-job/agents/a1/chat").status_code == 404


def test_rate_limiting_disabled_in_test_env_by_default(monkeypatch):
    """conftest sets RATE_LIMIT_ENABLED=false → suite never trips limits."""
    monkeypatch.setattr(Config, "RATE_LIMIT_ROAST", "1 per hour")
    app = _make_app()  # plain Config: RATELIMIT_ENABLED is False under pytest
    client = app.test_client()

    for _ in range(5):
        resp = client.post("/api/roast", json={})
        assert resp.status_code == 400  # validation error, never 429


# ---------------------------------------------------------------------------
# CORS allowlist
# ---------------------------------------------------------------------------

def test_cors_reflects_allowlisted_origin():
    app = _make_app()
    client = app.test_client()

    resp = client.get("/api/roast/swarms", headers={"Origin": "https://swarmie.vercel.app"})
    assert resp.headers.get("Access-Control-Allow-Origin") == "https://swarmie.vercel.app"

    resp = client.get("/api/roast/swarms", headers={"Origin": "http://localhost:3000"})
    assert resp.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"


def test_cors_rejects_unlisted_origin():
    app = _make_app()
    client = app.test_client()

    resp = client.get("/api/roast/swarms", headers={"Origin": "https://evil.example.com"})
    assert resp.status_code == 200  # CORS is enforced by the browser, not the server
    assert "Access-Control-Allow-Origin" not in resp.headers


def test_cors_allowlist_is_config_driven():
    app = _make_app(CORS_ORIGINS=["https://only.example"])
    client = app.test_client()

    resp = client.get("/api/roast/swarms", headers={"Origin": "https://only.example"})
    assert resp.headers.get("Access-Control-Allow-Origin") == "https://only.example"

    resp = client.get("/api/roast/swarms", headers={"Origin": "https://swarmie.vercel.app"})
    assert "Access-Control-Allow-Origin" not in resp.headers


def test_cors_origins_env_parsing(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", " https://a.example , https://b.example ,")
    assert _csv("CORS_ORIGINS", "unused") == ["https://a.example", "https://b.example"]

    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert _csv("CORS_ORIGINS", "https://swarmie.vercel.app,http://localhost:3000") == [
        "https://swarmie.vercel.app",
        "http://localhost:3000",
    ]


# ---------------------------------------------------------------------------
# Error handling — JSON envelope, no traceback leaks
# ---------------------------------------------------------------------------

def test_unhandled_exception_returns_json_500_without_traceback():
    app = _make_app()

    @app.route("/api/boom")
    def boom():
        raise RuntimeError("SECRET-INTERNALS-do-not-leak")

    client = app.test_client()
    resp = client.get("/api/boom")

    assert resp.status_code == 500
    body = resp.get_json()
    assert body is not None, "500 must be JSON"
    assert set(body.keys()) == {"error"}
    assert "try again" in body["error"].lower()
    text = resp.get_data(as_text=True)
    assert "SECRET-INTERNALS-do-not-leak" not in text
    assert "Traceback" not in text


def test_http_errors_keep_existing_behavior():
    """The catch-all must not hijack handled HTTP errors (e.g. JSON 404s)."""
    app = _make_app()
    client = app.test_client()

    resp = client.get("/api/roast/does-not-exist")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "job not found"}
