"""Free-path latency guards: reasoning off on OpenRouter, timeouts go to fallback."""

from types import SimpleNamespace

import httpx
import pytest
from openai import APITimeoutError, BadRequestError

from app.config import Config
from app.utils.llm import LLM


def _ok(text="hi"):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
        usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2),
    )


class FakeCompletions:
    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def create(self, **payload):
        self.calls.append(payload)
        out = self.outcomes.pop(0)
        if isinstance(out, Exception):
            raise out
        return out


def _client(completions):
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


@pytest.fixture
def openrouter(monkeypatch):
    monkeypatch.setattr(Config, "LLM_API_KEY", "sk-or-test")
    monkeypatch.setattr(Config, "LLM_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setattr(Config, "LLM_MODEL_NAME", "nvidia/nemotron-3.5-super-vl:free")
    for k in ("LLM_REASONING", "LLM_FALLBACK_API_KEY", "LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL_NAME",
              "LLM_CHEAP_BASE_URL", "LLM_CHEAP_API_KEY", "LLM_CHEAP_MODEL_NAME"):
        monkeypatch.delenv(k, raising=False)
    return monkeypatch


def test_openrouter_requests_reasoning_off(openrouter):
    llm = LLM(tier="cheap")
    fake = FakeCompletions(_ok())
    llm._sync = _client(fake)
    assert llm.chat([{"role": "user", "content": "x"}]) == "hi"
    assert fake.calls[0]["extra_body"] == {"reasoning": {"enabled": False}}


def test_reasoning_can_be_left_on(openrouter):
    openrouter.setenv("LLM_REASONING", "on")
    llm = LLM(tier="cheap")
    fake = FakeCompletions(_ok())
    llm._sync = _client(fake)
    llm.chat([{"role": "user", "content": "x"}])
    assert "extra_body" not in fake.calls[0]


def test_timeout_skips_straight_to_fallback(openrouter):
    openrouter.setenv("LLM_FALLBACK_API_KEY", "gem")
    openrouter.setenv("LLM_FALLBACK_MODEL_NAME", "gemini-3.6-flash")
    llm = LLM(tier="cheap")
    primary = FakeCompletions(APITimeoutError(request=httpx.Request("POST", "http://x")))
    fallback = FakeCompletions(_ok("from fallback"))
    llm._sync = _client(primary)
    llm._fallback_sync = _client(fallback)
    assert llm.chat([{"role": "user", "content": "x"}]) == "from fallback"
    assert len(primary.calls) == 1  # no retries against the slow model
    assert "extra_body" not in fallback.calls[0]
    assert fallback.calls[0]["model"] == "gemini-3.6-flash"


def test_rejected_reasoning_switch_is_dropped(openrouter):
    resp = httpx.Response(400, request=httpx.Request("POST", "http://x"))
    llm = LLM(tier="cheap")
    fake = FakeCompletions(BadRequestError("reasoning not supported", response=resp, body=None), _ok())
    llm._sync = _client(fake)
    assert llm.chat([{"role": "user", "content": "x"}]) == "hi"
    assert "extra_body" in fake.calls[0] and "extra_body" not in fake.calls[1]
    assert llm._extra is None
