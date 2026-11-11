"""Paid runs route to Claude; free runs stay on the OpenAI-compatible provider."""

from types import SimpleNamespace

import pytest

from app.config import Config
from app.utils import llm as llm_mod
from app.utils.llm import LLM, UsageTracker, paid_run


def _resp(text="{\"ok\": true}", stop_reason="end_turn", model="claude-haiku-5-5"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        stop_details=SimpleNamespace(category="cyber") if stop_reason == "refusal" else None,
        content=[SimpleNamespace(type="thinking", text=""), SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(input_tokens=1000, output_tokens=200),
        model=model,
    )


@pytest.fixture
def env(monkeypatch):
    # No free-provider key at all (as in CI): paid runs must not need one.
    monkeypatch.setattr(Config, "LLM_API_KEY", None)
    for k in ("LLM_API_KEY", "LLM_CHEAP_API_KEY", "LLM_DEEP_API_KEY", "LLM_SYNTH_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("LLM_PAID_CHEAP_MODEL_NAME", "claude-haiku-5-5")
    token = paid_run.set(True)
    yield monkeypatch
    paid_run.reset(token)


def test_free_run_does_not_use_claude(monkeypatch):
    monkeypatch.setattr(Config, "LLM_API_KEY", "free-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert LLM(tier="cheap")._claude is None


def test_paid_run_uses_claude_and_tracks_cost(env):
    calls = {}

    def create(**req):
        calls.update(req)
        return _resp()

    tracker = UsageTracker()
    client = LLM(tier="cheap", tracker=tracker)
    client._claude = SimpleNamespace(messages=SimpleNamespace(create=create))

    out = client.chat_json([
        {"role": "system", "content": "You are a reviewer."},
        {"role": "user", "content": "Pitch"},
    ], max_tokens=800)

    assert out == {"ok": True}
    assert calls["model"] == "claude-haiku-5-5"
    assert calls["system"].startswith("You are a reviewer.") and "JSON" in calls["system"]
    assert all(m["role"] != "system" for m in calls["messages"])
    assert calls["max_tokens"] >= 16000
    assert calls["output_config"] == {"effort": "low"}
    assert "temperature" not in calls
    assert tracker.total_cost_usd == pytest.approx((1000 * 0.10 + 200 * 0.50) / 1e6)


def test_paid_run_refusal_raises(env):
    client = LLM(tier="cheap")
    client._claude = SimpleNamespace(messages=SimpleNamespace(create=lambda **r: _resp(stop_reason="refusal")))
    with pytest.raises(RuntimeError, match="declined"):
        client.chat([{"role": "user", "content": "x"}])


def test_non_haiku_requests_server_side_fallback(env):
    env.setenv("LLM_PAID_SYNTH_MODEL_NAME", "claude-opus-5-5")
    calls = {}
    client = LLM(tier="synth")

    def beta_create(**req):
        calls.update(req)
        return _resp(text="memo", model="claude-opus-5-5")

    client._claude = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=beta_create)))
    assert client.chat([{"role": "user", "content": "x"}]) == "memo"
    assert calls["fallbacks"] == "default"
    assert "output_config" not in calls  # synth keeps the model's default effort
    assert llm_mod._lookup_price("claude-opus-5-5") == (4.00, 20.00)
