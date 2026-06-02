"""
Offline smoke tests for the eval harness.

These run the deterministic-only portions (canned reactions + stubbed LLM)
and verify that every golden case passes the schema and deterministic checks.
No API key required — all LLM calls are stubbed.

Run with:
    .venv/bin/python -m pytest tests/test_eval_smoke.py -q
"""

from __future__ import annotations

import os
import sys

import pytest

# Ensure backend root is on the path
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def all_golden_cases():
    from eval.golden_set import GOLDEN_CASES
    return GOLDEN_CASES


@pytest.fixture(scope="session")
def canned_registry():
    from eval.canned_reactions import CANNED
    return CANNED


# ---------------------------------------------------------------------------
# Golden set integrity
# ---------------------------------------------------------------------------

class TestGoldenSetIntegrity:
    def test_golden_cases_non_empty(self, all_golden_cases):
        assert len(all_golden_cases) >= 4, "Need at least 4 golden cases"

    def test_each_case_has_required_fields(self, all_golden_cases):
        required = {"id", "swarm_type", "pitch_text", "expected_verdicts",
                    "required_objection_themes", "pmf_direction"}
        for case in all_golden_cases:
            missing = required - set(case.keys())
            assert not missing, f"Case '{case.get('id')}' missing fields: {missing}"

    def test_swarm_type_is_valid(self, all_golden_cases):
        valid = {"validate", "investor", "launch"}
        for case in all_golden_cases:
            assert case["swarm_type"] in valid, (
                f"Case '{case['id']}' has invalid swarm_type '{case['swarm_type']}'"
            )

    def test_expected_verdicts_match_swarm_type(self, all_golden_cases):
        valid_verdicts = {
            "validate": {"ship_it", "sharpen_positioning", "wrong_audience", "kill"},
            "investor": {"fundable", "sharpen_story", "wrong_stage", "not_fundable"},
            "launch": {"go", "sharpen", "hold"},
        }
        for case in all_golden_cases:
            st = case["swarm_type"]
            for v in case["expected_verdicts"]:
                assert v in valid_verdicts[st], (
                    f"Case '{case['id']}': verdict '{v}' not valid for swarm_type '{st}'"
                )

    def test_pitch_text_non_empty(self, all_golden_cases):
        for case in all_golden_cases:
            assert len(case["pitch_text"].strip()) > 50, (
                f"Case '{case['id']}' pitch_text is too short"
            )

    def test_canned_reactions_exist_for_each_case(self, all_golden_cases, canned_registry):
        for case in all_golden_cases:
            assert case["id"] in canned_registry, (
                f"No canned reactions for case '{case['id']}'"
            )
            assert len(canned_registry[case["id"]]) >= 10, (
                f"Case '{case['id']}' has fewer than 10 canned reactions"
            )


# ---------------------------------------------------------------------------
# Canned reaction integrity
# ---------------------------------------------------------------------------

class TestCannedReactions:
    def test_reactions_have_required_fields(self, canned_registry):
        required = {"agent_id", "archetype_id", "segment", "name", "tone",
                    "action", "text", "objections", "sentiment"}
        for case_id, reactions in canned_registry.items():
            for i, r in enumerate(reactions):
                d = r.to_dict()
                missing = required - set(d.keys())
                assert not missing, (
                    f"Case '{case_id}' reaction {i}: missing fields {missing}"
                )

    def test_actions_are_valid(self, canned_registry):
        valid = {"post", "comment", "upvote", "ignore"}
        for case_id, reactions in canned_registry.items():
            for r in reactions:
                assert r.action in valid, (
                    f"Case '{case_id}': reaction {r.agent_id} has invalid action '{r.action}'"
                )

    def test_sentiment_is_numeric_in_range(self, canned_registry):
        for case_id, reactions in canned_registry.items():
            for r in reactions:
                assert isinstance(r.sentiment, (int, float)), (
                    f"Case '{case_id}': sentiment must be numeric"
                )
                assert -1.0 <= r.sentiment <= 1.0, (
                    f"Case '{case_id}': sentiment {r.sentiment} out of [-1, 1]"
                )

    def test_speaking_reactions_have_text(self, canned_registry):
        """comment/post reactions should have text."""
        for case_id, reactions in canned_registry.items():
            for r in reactions:
                if r.action in ("comment", "post"):
                    assert r.text.strip(), (
                        f"Case '{case_id}': {r.action} reaction {r.agent_id} has empty text"
                    )


# ---------------------------------------------------------------------------
# Deterministic checks module
# ---------------------------------------------------------------------------

class TestDeterministicChecks:
    def _make_valid_report(self, verdict="sharpen_positioning", pmf=5.5,
                           confidence="low", swarm_type="validate"):
        return {
            "pmf_score": float(pmf),
            "headline": "Test headline.",
            "sentiment_split": {"positive": 40.0, "neutral": 30.0, "negative": 30.0},
            "action_split": {"post": 5, "comment": 15, "upvote": 10, "ignore": 10},
            "top_objections": [
                {"category": "price", "count": 10, "example_quote": "too expensive",
                 "real_test": "", "kill_criteria": "", "suggested_fix": ""},
            ],
            "icp_fit": {"founders": {"count": 20, "avg_sentiment": 0.2,
                                      "dominant_action": "comment", "speaking_count": 15}},
            "messaging_gaps": ["Clarify pricing"],
            "narrative": "Para1. Para2. Para3.",
            "quoted_reactions": [],
            "verdict": verdict,
            "verdict_reason": "Test reason.",
            "next_action": "Interview 5 users.",
            "confidence": confidence,
            "confidence_reason": "20 agents spoke.",
            "ignore_reasons": [],
            "silent_share_pct": 25.0,
        }

    def test_schema_check_passes_valid_report(self):
        from eval.checks import check_schema
        report = self._make_valid_report()
        passed, detail = check_schema(report, "validate")
        assert passed, f"Schema check failed unexpectedly: {detail}"

    def test_schema_check_fails_missing_key(self):
        from eval.checks import check_schema
        report = self._make_valid_report()
        del report["verdict"]
        passed, detail = check_schema(report, "validate")
        assert not passed
        assert "verdict" in detail

    def test_verdict_check_passes_when_in_expected_set(self):
        from eval.checks import check_verdict
        case = {"expected_verdicts": {"ship_it", "sharpen_positioning"}, "swarm_type": "validate"}
        report = self._make_valid_report(verdict="sharpen_positioning")
        passed, _ = check_verdict(report, case)
        assert passed

    def test_verdict_check_fails_wrong_verdict(self):
        from eval.checks import check_verdict
        case = {"expected_verdicts": {"ship_it"}, "swarm_type": "validate"}
        report = self._make_valid_report(verdict="kill")
        passed, _ = check_verdict(report, case)
        assert not passed

    def test_verdict_check_fails_invalid_enum(self):
        from eval.checks import check_verdict
        case = {"expected_verdicts": {"ship_it"}, "swarm_type": "validate"}
        report = self._make_valid_report(verdict="fundable")  # wrong swarm type
        passed, detail = check_verdict(report, case)
        assert not passed

    def test_objection_themes_hit(self):
        from eval.checks import check_objection_themes
        report = self._make_valid_report()
        # 'price' is in top_objections category
        case = {"required_objection_themes": [["price", "cost"]]}
        passed, detail = check_objection_themes(report, case, threshold=1.0)
        assert passed, detail

    def test_objection_themes_miss(self):
        from eval.checks import check_objection_themes
        report = self._make_valid_report()
        case = {"required_objection_themes": [["nonexistent_keyword_xyz"]]}
        passed, _ = check_objection_themes(report, case, threshold=1.0)
        assert not passed

    def test_pmf_direction_positive(self):
        from eval.checks import check_pmf_direction
        report = self._make_valid_report(pmf=6.5)
        case = {"pmf_direction": "positive"}
        passed, _ = check_pmf_direction(report, case)
        assert passed

    def test_pmf_direction_positive_fails_low(self):
        from eval.checks import check_pmf_direction
        report = self._make_valid_report(pmf=3.0)
        case = {"pmf_direction": "positive"}
        passed, _ = check_pmf_direction(report, case)
        assert not passed

    def test_pmf_direction_negative(self):
        from eval.checks import check_pmf_direction
        report = self._make_valid_report(pmf=2.5)
        case = {"pmf_direction": "negative"}
        passed, _ = check_pmf_direction(report, case)
        assert passed

    def test_confidence_ceiling_respected(self):
        from eval.checks import check_confidence_ceiling
        report = self._make_valid_report(confidence="low")
        case = {"confidence_ceiling": "low"}
        passed, _ = check_confidence_ceiling(report, case)
        assert passed

    def test_confidence_exceeds_ceiling(self):
        from eval.checks import check_confidence_ceiling
        report = self._make_valid_report(confidence="high")
        case = {"confidence_ceiling": "low"}
        passed, _ = check_confidence_ceiling(report, case)
        assert not passed

    def test_sentiment_split_sums(self):
        from eval.checks import check_sentiment_split_sums
        report = self._make_valid_report()
        passed, _ = check_sentiment_split_sums(report)
        assert passed

    def test_sentiment_split_wrong_sum(self):
        from eval.checks import check_sentiment_split_sums
        report = self._make_valid_report()
        report["sentiment_split"] = {"positive": 80.0, "neutral": 30.0, "negative": 30.0}
        passed, _ = check_sentiment_split_sums(report)
        assert not passed


# ---------------------------------------------------------------------------
# Full synth run — every golden case must pass the deterministic bar
# ---------------------------------------------------------------------------

class TestSynthRunAllCases:
    """
    Integration: run each golden case in synth mode and assert it passes.
    This is the main offline CI gate.
    """

    @pytest.mark.parametrize("case_id", [
        "tally_validate",
        "onetap_investor",
        "clarity_launch",
        "weak_b2b_saas",
        "strong_dev_tool",
        "wrong_audience_b2c",
    ])
    def test_synth_case_passes(self, case_id):
        from eval.golden_set import get_case
        from eval.run import run_synth_case, PASS_BAR

        case = get_case(case_id)
        assert case is not None, f"Golden case '{case_id}' not found"

        result = run_synth_case(case, verbose=False)

        assert "error" not in result, (
            f"Case '{case_id}' raised an error in synth mode: {result.get('error')}"
        )
        score = result.get("score", 0.0)
        assert score >= PASS_BAR, (
            f"Case '{case_id}' scored {score:.0%} < pass bar {PASS_BAR:.0%}.\n"
            f"Failing checks: {[r for r in result['check_results'] if not r['passed']]}"
        )

    def test_all_golden_cases_produce_valid_reports(self, all_golden_cases):
        """Bulk check: no case should error out."""
        from eval.run import run_synth_case
        for case in all_golden_cases:
            result = run_synth_case(case, verbose=False)
            assert "error" not in result, (
                f"Case '{case['id']}' errored: {result.get('error')}"
            )
            assert "report_summary" in result, (
                f"Case '{case['id']}' missing report_summary"
            )
