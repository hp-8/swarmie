"""
Unit tests for the Launch swarm reporter — verdict vocab + launch_brief.

LLM calls stubbed by patching the module LLM symbol. Offline + deterministic.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.swarm import SWARMS, get_swarm, LaunchReporter
from app.services.swarm.pitch_parser import ParsedPitch
from app.services.swarm.swarm_runner import AgentReaction


def _reactions() -> list[AgentReaction]:
    return [
        AgentReaction(agent_id="a1", archetype_id="ph", segment="Product Hunt maker",
                      name="MakerMax", tone="curious", action="comment",
                      text="clean landing, but how is this different from X?",
                      objections=["me_too"], sentiment=0.1),
        AgentReaction(agent_id="a2", archetype_id="hn", segment="HN skeptic",
                      name="ShowHNSkeptic", tone="skeptical", action="comment",
                      text="show hn needs a demo, not a waitlist", objections=["show_hn_rigor"], sentiment=-0.4),
        AgentReaction(agent_id="a3", archetype_id="ph", segment="Product Hunt maker",
                      name="Lurker", tone="indifferent", action="ignore",
                      ignore_reason="not my community", ignore_reason_category="not_my_community"),
    ]


_NARRATIVE = {
    "headline": "Communities will push on differentiation",
    "narrative": "Launch reads as me-too on HN.",
    "messaging_gaps": ["lead with the wedge"],
    "verdict": "sharpen",
    "verdict_reason": "me-too risk on HN",
    "next_action": "ship a live demo before Show HN",
    "confidence": "low",
    "confidence_reason": "few spoke",
    "objections_enriched": [],
}
_BRIEF = {
    "questions": ["how is this different from X?"],
    "confusion": ["unclear what the core action is"],
    "risks": ["Show HN without a demo flops"],
    "themes": ["differentiation", "demo-or-die"],
    "playbook": [{"trigger": "me-too", "response": "open with the one thing only you do"}],
    "next_actions": ["record a 60s demo", "rewrite the tagline around the wedge"],
}


def test_registry_has_launch():
    assert "launch" in SWARMS
    assert get_swarm("launch").reporter_cls is LaunchReporter


def _stub(side_effect):
    inst = MagicMock()
    inst.chat_json.side_effect = side_effect
    return MagicMock(return_value=inst)


def test_launch_report_produces_brief_and_verdict():
    with patch("app.services.swarm.roast_reporter.LLM", _stub([_NARRATIVE, _BRIEF])):
        report = LaunchReporter().report(ParsedPitch(one_liner="x", problem="p", solution="s"), _reactions())
    assert report.verdict == "sharpen"
    assert report.launch_brief is not None
    lb = report.launch_brief
    assert lb["questions"] == ["how is this different from X?"]
    assert lb["playbook"][0]["trigger"] == "me-too"
    assert "differentiation" in lb["themes"]
    assert len(lb["next_actions"]) == 2


def test_launch_verdict_clamped_to_vocab():
    bad = dict(_NARRATIVE, verdict="ship_it")  # invalid for launch
    with patch("app.services.swarm.roast_reporter.LLM", _stub([bad, _BRIEF])):
        report = LaunchReporter().report(ParsedPitch(one_liner="x", problem="p", solution="s"), _reactions())
    assert report.verdict in {"go", "sharpen", "hold"}


def test_launch_brief_bad_json_falls_back():
    def boom(*a, **k):
        raise ValueError("not json")
    # narrative succeeds, brief call raises -> empty brief, no crash
    inst = MagicMock()
    inst.chat_json.side_effect = [_NARRATIVE, ValueError("bad")]
    with patch("app.services.swarm.roast_reporter.LLM", MagicMock(return_value=inst)):
        report = LaunchReporter().report(ParsedPitch(one_liner="x", problem="p", solution="s"), _reactions())
    assert report.launch_brief is not None
    assert report.launch_brief["questions"] == []
    assert report.launch_brief["playbook"] == []
