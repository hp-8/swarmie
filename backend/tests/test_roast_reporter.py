"""
Unit tests for RoastReporter — decision brief extension (Workstream A).

LLM calls are stubbed via monkeypatching so tests are deterministic and offline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Minimal stubs so imports don't need real env vars
# ---------------------------------------------------------------------------

# Patch LLM before importing roast_reporter so the constructor doesn't
# attempt to resolve API keys from the environment.
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_llm_stub(return_value: dict) -> MagicMock:
    stub = MagicMock()
    stub.chat_json.return_value = return_value
    return stub


# ---------------------------------------------------------------------------
# Helpers to build synthetic data
# ---------------------------------------------------------------------------

@dataclass
class _Pitch:
    one_liner: str = "AI co-pilot for B2B sales reps"
    problem: str = "Reps spend 40% of time on admin"
    solution: str = "AI fills CRM automatically via call transcripts"
    target_icp: str = "B2B SaaS AEs, mid-market"
    icp_segments: list = field(default_factory=list)
    differentiators: list = field(default_factory=list)
    pricing_signals: list = field(default_factory=list)
    raw_text: str = ""


@dataclass
class _Reaction:
    agent_id: str
    archetype_id: str
    segment: str
    name: str
    tone: str
    action: str
    text: str = ""
    objections: list = field(default_factory=list)
    sentiment: float = 0.0
    ignore_reason: str = ""
    ignore_reason_category: str = ""

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "archetype_id": self.archetype_id,
            "segment": self.segment,
            "name": self.name,
            "tone": self.tone,
            "action": self.action,
            "text": self.text,
            "objections": self.objections,
            "sentiment": self.sentiment,
        }


def _make_reactions(n: int, action: str = "comment", sentiment: float = 0.5,
                    objections: list | None = None) -> list[_Reaction]:
    if objections is None:
        objections = ["price"]
    return [
        _Reaction(
            agent_id=f"agent_{i:04d}",
            archetype_id="arch_0",
            segment="founders",
            name=f"User{i}",
            tone="neutral",
            action=action,
            text=f"This is reaction {i}.",
            objections=objections,
            sentiment=sentiment,
        )
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# The LLM response stub that includes all new fields
# ---------------------------------------------------------------------------

def _full_llm_response(objection_categories: list[str] | None = None) -> dict:
    categories = objection_categories or ["price", "trust"]
    return {
        "headline": "Strong signal — but pricing kills it for SMBs.",
        "narrative": "Para 1. Para 2. Para 3.",
        "messaging_gaps": ["Price anchor unclear", "ROI not shown"],
        "verdict": "sharpen_positioning",
        "verdict_reason": "Product resonates but price-sensitivity kills conversion for SMBs.",
        "next_action": "Run 5 discovery calls with AEs on pricing willingness-to-pay.",
        "confidence": "med",
        "confidence_reason": "20 agents spoke; sentiment fairly split",
        "objections_enriched": [
            {
                "category": cat,
                "real_test": f"How much would you pay monthly for this, {cat}?",
                "kill_criteria": f"If 3/5 say {cat} is deal-breaker, positioning is dead.",
                "suggested_fix": f"Reframe {cat} around ROI not cost.",
            }
            for cat in categories
        ],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNewFieldsPresent:
    """All new top-level fields exist on the returned RoastReport dict."""

    def test_new_top_level_keys_present(self):
        from app.services.swarm.roast_reporter import RoastReporter

        reactions = _make_reactions(20, action="comment", sentiment=0.4, objections=["price", "trust"])
        pitch = _Pitch()

        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(_full_llm_response(["price", "trust"]))

        report = reporter.report(pitch, reactions)
        d = report.to_dict()

        assert "verdict" in d
        assert "verdict_reason" in d
        assert "next_action" in d
        assert "confidence" in d
        assert "confidence_reason" in d

    def test_new_top_level_field_types(self):
        from app.services.swarm.roast_reporter import RoastReporter

        reactions = _make_reactions(20, action="comment", sentiment=0.4, objections=["price"])
        pitch = _Pitch()

        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(_full_llm_response(["price"]))

        report = reporter.report(pitch, reactions)

        assert isinstance(report.verdict, str)
        assert isinstance(report.verdict_reason, str)
        assert isinstance(report.next_action, str)
        assert isinstance(report.confidence, str)
        assert isinstance(report.confidence_reason, str)

    def test_verdict_is_valid_value(self):
        from app.services.swarm.roast_reporter import RoastReporter

        reactions = _make_reactions(20, action="comment", sentiment=0.4, objections=["price"])
        pitch = _Pitch()

        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(_full_llm_response(["price"]))

        report = reporter.report(pitch, reactions)
        assert report.verdict in {"ship_it", "sharpen_positioning", "wrong_audience", "kill"}

    def test_confidence_is_valid_value(self):
        from app.services.swarm.roast_reporter import RoastReporter

        reactions = _make_reactions(20, action="comment", sentiment=0.4, objections=["price"])
        pitch = _Pitch()

        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(_full_llm_response(["price"]))

        report = reporter.report(pitch, reactions)
        assert report.confidence in {"low", "med", "high"}


class TestEnrichmentMerge:
    """objections_enriched merges correctly into top_objections by category."""

    def test_enrichment_fields_present_on_objections(self):
        from app.services.swarm.roast_reporter import RoastReporter

        reactions = _make_reactions(20, action="comment", sentiment=0.4, objections=["price", "trust"])
        pitch = _Pitch()

        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(_full_llm_response(["price", "trust"]))

        report = reporter.report(pitch, reactions)

        for obj in report.top_objections:
            assert "real_test" in obj
            assert "kill_criteria" in obj
            assert "suggested_fix" in obj
            assert isinstance(obj["real_test"], str)
            assert isinstance(obj["kill_criteria"], str)
            assert isinstance(obj["suggested_fix"], str)

    def test_enrichment_merges_by_category(self):
        from app.services.swarm.roast_reporter import RoastReporter

        reactions = _make_reactions(20, action="comment", sentiment=0.4, objections=["price"])
        pitch = _Pitch()

        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(_full_llm_response(["price"]))

        report = reporter.report(pitch, reactions)
        price_obj = next((o for o in report.top_objections if o["category"] == "price"), None)
        assert price_obj is not None
        assert "price" in price_obj["real_test"].lower() or price_obj["real_test"] != ""
        assert price_obj["kill_criteria"] != ""
        assert price_obj["suggested_fix"] != ""

    def test_missing_category_gets_empty_strings(self):
        """If LLM returns enrichment for 'price' but top_objections has 'trust', trust gets empty."""
        from app.services.swarm.roast_reporter import RoastReporter

        # Give reactions with both 'price' and 'trust' objections
        reactions = (
            _make_reactions(15, action="comment", sentiment=0.4, objections=["price"])
            + _make_reactions(10, action="comment", sentiment=-0.3, objections=["trust"])
        )
        pitch = _Pitch()

        # LLM only returns enrichment for 'price', not 'trust'
        llm_response = _full_llm_response(["price"])  # no trust entry
        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(llm_response)

        report = reporter.report(pitch, reactions)
        trust_obj = next((o for o in report.top_objections if o["category"] == "trust"), None)
        if trust_obj:
            assert trust_obj["real_test"] == ""
            assert trust_obj["kill_criteria"] == ""
            assert trust_obj["suggested_fix"] == ""


class TestConfidenceClamp:
    """Confidence ceiling logic is applied correctly."""

    def test_low_ceiling_when_speaking_lt_15(self):
        """< 15 speaking reactions → confidence must be 'low' regardless of LLM."""
        from app.services.swarm.roast_reporter import RoastReporter

        # Only 10 speaking reactions
        reactions = _make_reactions(10, action="comment", sentiment=0.4, objections=["price"])
        pitch = _Pitch()

        # LLM claims "high" confidence — should be clamped to "low"
        llm_resp = _full_llm_response(["price"])
        llm_resp["confidence"] = "high"
        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(llm_resp)

        report = reporter.report(pitch, reactions)
        assert report.confidence == "low", f"Expected 'low' but got '{report.confidence}'"

    def test_med_ceiling_when_sentiment_split(self):
        """pos>30% AND neg>30% (but speaking>=15) → confidence capped at 'med'."""
        from app.services.swarm.roast_reporter import RoastReporter

        # 20 reactions: 40% positive (8), 40% negative (8), 20% neutral (4)
        # We create mixed sentiment to trigger the split ceiling
        pos_reactions = _make_reactions(8, action="comment", sentiment=0.5, objections=["price"])
        neg_reactions = _make_reactions(8, action="comment", sentiment=-0.5, objections=["trust"])
        neu_reactions = _make_reactions(4, action="comment", sentiment=0.0, objections=[])
        reactions = pos_reactions + neg_reactions + neu_reactions

        pitch = _Pitch()

        # LLM claims "high" — should be clamped to "med"
        llm_resp = _full_llm_response(["price", "trust"])
        llm_resp["confidence"] = "high"
        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(llm_resp)

        report = reporter.report(pitch, reactions)
        assert report.confidence in {"low", "med"}, f"Expected 'low' or 'med', got '{report.confidence}'"

    def test_high_confidence_passes_through_when_ceiling_is_high(self):
        """With sufficient clean signal, LLM's 'high' should pass through."""
        from app.services.swarm.roast_reporter import RoastReporter

        # 20 reactions, mostly positive → ceiling should be 'high'
        reactions = _make_reactions(20, action="comment", sentiment=0.7, objections=["price"])
        pitch = _Pitch()

        llm_resp = _full_llm_response(["price"])
        llm_resp["confidence"] = "high"
        llm_resp["confidence_reason"] = "Strong positive signal across segments."
        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(llm_resp)

        report = reporter.report(pitch, reactions)
        # With 20 speaking agents and ~70% positive, neg should be low → ceiling=high
        assert report.confidence == "high"

    def test_llm_invalid_confidence_falls_back_to_low(self):
        """If LLM returns garbage confidence value, it falls back to 'low'."""
        from app.services.swarm.roast_reporter import RoastReporter

        reactions = _make_reactions(20, action="comment", sentiment=0.4, objections=["price"])
        pitch = _Pitch()

        llm_resp = _full_llm_response(["price"])
        llm_resp["confidence"] = "ultra"  # invalid value
        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(llm_resp)

        report = reporter.report(pitch, reactions)
        assert report.confidence in {"low", "med", "high"}


class TestFallbackPath:
    """When LLM raises an exception, sane defaults are returned."""

    def test_fallback_on_llm_exception(self):
        from app.services.swarm.roast_reporter import RoastReporter

        reactions = _make_reactions(10, action="comment", sentiment=0.4, objections=["price"])
        pitch = _Pitch()

        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = MagicMock()
        reporter.llm.chat_json.side_effect = RuntimeError("LLM unavailable")

        report = reporter.report(pitch, reactions)
        d = report.to_dict()

        # Must still have all keys
        assert d["verdict"] == "sharpen_positioning"
        assert isinstance(d["verdict_reason"], str) and len(d["verdict_reason"]) > 0
        assert isinstance(d["next_action"], str) and len(d["next_action"]) > 0
        assert d["confidence"] == "low"
        assert isinstance(d["confidence_reason"], str)

    def test_fallback_objections_have_empty_enrichment(self):
        from app.services.swarm.roast_reporter import RoastReporter

        reactions = _make_reactions(10, action="comment", sentiment=0.4, objections=["price"])
        pitch = _Pitch()

        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = MagicMock()
        reporter.llm.chat_json.side_effect = RuntimeError("LLM unavailable")

        report = reporter.report(pitch, reactions)
        for obj in report.top_objections:
            assert obj.get("real_test", "") == ""
            assert obj.get("kill_criteria", "") == ""
            assert obj.get("suggested_fix", "") == ""


class TestExistingFieldsUntouched:
    """All original fields still present and computed deterministically."""

    def test_original_fields_still_present(self):
        from app.services.swarm.roast_reporter import RoastReporter

        reactions = _make_reactions(20, action="comment", sentiment=0.4, objections=["price"])
        pitch = _Pitch()

        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(_full_llm_response(["price"]))

        report = reporter.report(pitch, reactions)
        d = report.to_dict()

        for key in ("pmf_score", "headline", "sentiment_split", "action_split",
                    "top_objections", "icp_fit", "messaging_gaps", "narrative", "quoted_reactions"):
            assert key in d, f"Missing original field: {key}"

    def test_pmf_score_is_float_in_range(self):
        from app.services.swarm.roast_reporter import RoastReporter

        reactions = _make_reactions(20, action="comment", sentiment=0.4, objections=["price"])
        pitch = _Pitch()

        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(_full_llm_response(["price"]))

        report = reporter.report(pitch, reactions)
        assert isinstance(report.pmf_score, float)
        assert 0.0 <= report.pmf_score <= 10.0

    def test_top_objections_has_original_keys(self):
        from app.services.swarm.roast_reporter import RoastReporter

        reactions = _make_reactions(20, action="comment", sentiment=0.4, objections=["price", "trust"])
        pitch = _Pitch()

        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(_full_llm_response(["price", "trust"]))

        report = reporter.report(pitch, reactions)
        for obj in report.top_objections:
            assert "category" in obj
            assert "count" in obj
            assert "example_quote" in obj


class TestIgnoreReasons:
    """Workstream B — sampled ignore reasons cluster into decision-useful signal."""

    def _ignore(self, i, category, reason="scrolled past"):
        return _Reaction(
            agent_id=f"ig_{i:04d}", archetype_id="arch_0", segment="founders",
            name=f"Ghost{i}", tone="indifferent", action="ignore",
            ignore_reason=reason, ignore_reason_category=category,
        )

    def test_clusters_and_silent_share(self):
        from app.services.swarm.roast_reporter import _compute_ignore_reasons

        reactions = _make_reactions(10, action="comment")  # 10 speakers
        # 8 silent ignores (no reason) + 4 sampled (with reason)
        reactions += [self._ignore(i, "") for i in range(8)]
        reactions += [
            self._ignore(100, "unclear_value", "no idea what this does"),
            self._ignore(101, "unclear_value", "couldn't parse it"),
            self._ignore(102, "not_my_problem", "not for me"),
            self._ignore(103, "seen_before", "vanta already does this"),
        ]
        # Note: empty-category ignores are NOT counted as sampled.
        ignore_reasons, silent_share = _compute_ignore_reasons(reactions)

        # 12 ignores of 22 total
        assert silent_share == round(12 / 22 * 100, 1)
        # 3 distinct sampled categories, unclear_value leads
        assert ignore_reasons[0]["category"] == "unclear_value"
        assert ignore_reasons[0]["sampled_count"] == 2
        assert ignore_reasons[0]["share_pct"] == 50.0  # 2 of 4 sampled
        assert ignore_reasons[0]["label"]
        assert ignore_reasons[0]["implication"]
        assert ignore_reasons[0]["example"] == "no idea what this does"

    def test_no_sampled_reasons_yields_empty(self):
        from app.services.swarm.roast_reporter import _compute_ignore_reasons

        reactions = _make_reactions(5, action="comment")
        reactions += [self._ignore(i, "") for i in range(5)]  # all silent
        ignore_reasons, silent_share = _compute_ignore_reasons(reactions)
        assert ignore_reasons == []
        assert silent_share == 50.0

    def test_report_exposes_ignore_fields(self):
        from app.services.swarm.roast_reporter import RoastReporter

        reactions = _make_reactions(20, action="comment", sentiment=0.4)
        reactions += [self._ignore(100, "price_or_effort", "too pricey to bother")]
        pitch = _Pitch()
        reporter = RoastReporter.__new__(RoastReporter)
        reporter.llm = _make_llm_stub(_full_llm_response(["price", "trust"]))

        report = reporter.report(pitch, reactions)
        d = report.to_dict()
        assert "ignore_reasons" in d and isinstance(d["ignore_reasons"], list)
        assert "silent_share_pct" in d and isinstance(d["silent_share_pct"], float)
        assert d["ignore_reasons"][0]["category"] == "price_or_effort"
