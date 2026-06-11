"""
Cost-cap watchdog tests — no real LLM calls.

Proves the ROAST_MAX_COST_USD ceiling actually aborts a run mid-flight:
fake LLMs record cost into the shared UsageTracker then hold (long sleep);
the watchdog must cancel the in-flight tasks and the run must surface
CostCeilingExceeded (a regular Exception the pipeline can map to a clean,
user-facing "failed" status) instead of leaking asyncio.CancelledError.
"""

from __future__ import annotations

import asyncio
import time

import pytest

from app.api.roast import _public_error_message
from app.services.swarm import Archetype, CostCeilingExceeded, ParsedPitch, SwarmRunner
from app.utils.llm import Usage, UsageTracker


class _FakeLLM:
    """Duck-typed LLM stub: adds cost to the tracker, then holds the task open."""

    def __init__(self, tracker: UsageTracker, cost_per_call: float, hold_seconds: float):
        self.tracker = tracker
        self.cost_per_call = cost_per_call
        self.hold_seconds = hold_seconds
        self.calls_started = 0
        self.calls_finished = 0

    async def achat_json(self, messages, **kwargs):
        self.calls_started += 1
        self.tracker.add(Usage(cost_usd=self.cost_per_call, model="fake", tier="cheap"))
        if self.hold_seconds:
            await asyncio.sleep(self.hold_seconds)
        self.calls_finished += 1
        return {"text": "looks fine i guess", "objections": [], "sentiment": 0.1}


def _talkative_archetype() -> Archetype:
    """Every sampled agent comments → every agent triggers an LLM call."""
    return Archetype(
        id="arch_test",
        segment="indie hackers",
        name="ChattyDev",
        persona="Comments on everything.",
        tone="skeptical",
        objection_bias=["price"],
        action_likelihood={"post": 0.0, "comment": 1.0, "upvote": 0.0, "ignore": 0.0},
        weight=1.0,
    )


def _make_runner(tracker: UsageTracker, fake: _FakeLLM, max_cost_usd: float) -> SwarmRunner:
    runner = SwarmRunner(
        tracker=tracker,
        cheap_tier_llm=fake,
        deep_tier_llm=fake,
        max_cost_usd=max_cost_usd,
    )
    runner.WATCHDOG_POLL_SECONDS = 0.05  # fast polls so the test stays quick
    return runner


def test_watchdog_cancels_run_when_cost_cap_exceeded():
    tracker = UsageTracker()
    # 12 agents x $0.06 = $0.72 committed almost immediately; cap is $0.10.
    fake = _FakeLLM(tracker, cost_per_call=0.06, hold_seconds=30.0)
    runner = _make_runner(tracker, fake, max_cost_usd=0.10)

    started = time.time()
    with pytest.raises(CostCeilingExceeded):
        asyncio.run(
            runner.run(
                pitch=ParsedPitch(one_liner="test pitch"),
                archetypes=[_talkative_archetype()],
                n_agents=12,
                concurrency=12,
            )
        )
    elapsed = time.time() - started

    assert elapsed < 5, f"watchdog should abort fast, took {elapsed:.1f}s"
    assert tracker.total_cost_usd > 0.10, "cap must actually have been exceeded"
    assert fake.calls_started >= 2
    assert fake.calls_finished == 0, "in-flight calls must be cancelled, not awaited out"


def test_run_completes_normally_under_cost_cap():
    tracker = UsageTracker()
    fake = _FakeLLM(tracker, cost_per_call=0.0001, hold_seconds=0.0)
    runner = _make_runner(tracker, fake, max_cost_usd=1.00)

    reactions = asyncio.run(
        runner.run(
            pitch=ParsedPitch(one_liner="test pitch"),
            archetypes=[_talkative_archetype()],
            n_agents=10,
            concurrency=10,
        )
    )

    assert len(reactions) == 10
    assert fake.calls_finished == 10
    assert all(r.text for r in reactions)


# ---------------------------------------------------------------------------
# Error-message mapping (what the client ultimately sees in job.error / SSE)
# ---------------------------------------------------------------------------

def test_cost_cap_error_maps_to_friendly_message():
    msg = _public_error_message(CostCeilingExceeded("run aborted: cost $1.2345 exceeded ceiling $1.0000"))
    assert "cost limit" in msg
    assert "fewer agents" in msg
    assert "$" not in msg  # no internal numbers leak


def test_provider_error_maps_to_generic_message():
    raw = RuntimeError(
        "LLM call failed after 3 retries: Error code: 401 - invalid api key sk-LEAK"
    )
    msg = _public_error_message(raw)
    assert "sk-LEAK" not in msg
    assert "401" not in msg
    assert "try again" in msg.lower()


def test_user_facing_deck_error_kept_verbatim():
    raw = RuntimeError("Couldn't read the deck: file is encrypted. Paste the text instead.")
    assert _public_error_message(raw) == str(raw)
