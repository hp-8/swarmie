"""
Tests for roast_reporter.deterministic_report — the synthesis-free report half
used by the PMF Index backtest feature extractor.

Verifies it emits every field the 5 index dims need, with no LLM call, and that
dims_from_report consumes its output cleanly.
"""

from __future__ import annotations

from app.services.swarm.pmf_index import dims_from_report
from app.services.swarm.roast_reporter import deterministic_report
from app.services.swarm.swarm_runner import AgentReaction


def _reaction(action: str, segment: str, sentiment: float = 0.0, text: str = "",
              objections: list[str] | None = None, ignore_cat: str = "") -> AgentReaction:
    return AgentReaction(
        agent_id="a", archetype_id="arch", segment=segment, name="n", tone="t",
        action=action, text=text, objections=objections or [],
        sentiment=sentiment, ignore_reason_category=ignore_cat,
    )


def _sample_reactions() -> list[AgentReaction]:
    return [
        _reaction("comment", "devs", 0.6, "love this", ["pricing unclear"]),
        _reaction("post", "devs", 0.4, "would use it"),
        _reaction("comment", "pms", -0.5, "don't see the need", ["no demand"]),
        _reaction("upvote", "devs", 0.2),
        _reaction("ignore", "creators", 0.0, ignore_cat="unclear_value"),
        _reaction("ignore", "creators", 0.0),
    ]


def test_deterministic_report_has_all_dim_source_fields():
    rep = deterministic_report(_sample_reactions())
    for key in ("sentiment_split", "action_split", "top_objections",
                "icp_fit", "silent_share_pct"):
        assert key in rep, f"missing {key}"


def test_action_split_counts_match():
    rep = deterministic_report(_sample_reactions())
    assert rep["action_split"]["comment"] == 2
    assert rep["action_split"]["post"] == 1
    assert rep["action_split"]["upvote"] == 1
    assert rep["action_split"]["ignore"] == 2


def test_silent_share_reflects_ignores():
    # 2 of 6 reactions are ignores -> ~33.3%
    rep = deterministic_report(_sample_reactions())
    assert 33.0 <= rep["silent_share_pct"] <= 33.4


def test_dims_from_report_consumes_deterministic_output():
    rep = deterministic_report(_sample_reactions())
    dims = dims_from_report(rep)
    assert set(dims) == {
        "engagement_rate", "sentiment_score", "segment_fit",
        "objection_severity", "silence_penalty",
    }
    for v in dims.values():
        assert isinstance(v, float)
    # engagement: speakers + upvotes present -> positive
    assert dims["engagement_rate"] > 0.0
    # silence_penalty = silent_share_pct/100 ~ 0.33
    assert 0.30 <= dims["silence_penalty"] <= 0.34


def test_empty_reactions_no_crash():
    rep = deterministic_report([])
    dims = dims_from_report(rep)
    assert all(isinstance(v, float) for v in dims.values())
