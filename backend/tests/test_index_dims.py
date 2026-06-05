"""
Unit tests for compute_objection_severity and compute_silence_penalty.

Both functions are pure, deterministic, stdlib-only helpers introduced as
part of the PMF Readiness Index (Component 1, spec 2026-06-05).

No LLM, no I/O, no fixtures — all tests run offline.
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.swarm.roast_reporter import (
    compute_objection_severity,
    compute_silence_penalty,
)


# ---------------------------------------------------------------------------
# compute_objection_severity
# ---------------------------------------------------------------------------


class TestComputeObjectionSeverity:
    def test_empty_list_returns_zero(self):
        assert compute_objection_severity([]) == 0.0

    def test_all_fundamental_objections_near_one(self):
        objections = [
            {"category": "pricing too high", "count": 10},
            {"category": "demand unclear", "count": 5},
        ]
        result = compute_objection_severity(objections)
        # All map to FUNDAMENTAL (1.0), so severity = 1.0
        assert result == 1.0

    def test_all_cosmetic_objections_near_point_two(self):
        objections = [
            {"category": "UI is too plain", "count": 8},
            {"category": "naming is confusing", "count": 4},
        ]
        result = compute_objection_severity(objections)
        # All map to COSMETIC (0.2), so severity = 0.2
        assert result == 0.2

    def test_unknown_category_defaults_to_framing(self):
        objections = [
            {"category": "something completely novel", "count": 3},
        ]
        result = compute_objection_severity(objections)
        # No keyword match → default FRAMING (0.5)
        assert result == 0.5

    def test_mixed_weighted_by_count(self):
        # Hand-computed:
        #   "pricing" (FUNDAMENTAL 1.0) × 4 = 4.0
        #   "unclear messaging" (FRAMING 0.5) × 4 = 2.0
        #   (unclear matches first in the keyword order — "unclear" maps to 0.5)
        #   total_count = 8
        #   severity = (4.0 + 2.0) / 8 = 0.75
        objections = [
            {"category": "pricing objection", "count": 4},
            {"category": "unclear messaging", "count": 4},
        ]
        result = compute_objection_severity(objections)
        assert abs(result - 0.75) < 1e-5

    def test_mixed_fundamental_and_cosmetic(self):
        # "demand" (1.0) × 6 = 6.0
        # "UI issues" (0.2) × 4 = 0.8
        # total = 10, severity = 6.8 / 10 = 0.68
        objections = [
            {"category": "demand is weak", "count": 6},
            {"category": "UI issues", "count": 4},
        ]
        result = compute_objection_severity(objections)
        assert abs(result - 0.68) < 1e-5

    def test_all_zero_counts_returns_zero(self):
        objections = [
            {"category": "pricing", "count": 0},
            {"category": "naming", "count": 0},
        ]
        assert compute_objection_severity(objections) == 0.0

    def test_framing_keywords_match_correctly(self):
        for cat in ["positioning issue", "messaging gap", "differentiation unclear", "who is this for"]:
            result = compute_objection_severity([{"category": cat, "count": 1}])
            assert result == 0.5, f"expected FRAMING (0.5) for category '{cat}', got {result}"

    def test_cosmetic_keywords_match_correctly(self):
        for cat in ["onboarding too long", "minor complaint", "naming confusion"]:
            result = compute_objection_severity([{"category": cat, "count": 1}])
            assert result == 0.2, f"expected COSMETIC (0.2) for category '{cat}', got {result}"

    def test_fundamental_keywords_match_correctly(self):
        for cat in ["no problem exists", "won't pay this price", "market size concern", "demand validation"]:
            result = compute_objection_severity([{"category": cat, "count": 1}])
            assert result == 1.0, f"expected FUNDAMENTAL (1.0) for category '{cat}', got {result}"

    def test_single_objection_count_one(self):
        # Single fundamental objection with count=1
        objections = [{"category": "willingness to pay is low", "count": 1}]
        assert compute_objection_severity(objections) == 1.0

    def test_result_bounded_zero_to_one(self):
        # Fuzz-style: any realistic input must stay in [0, 1]
        cases = [
            [{"category": "demand", "count": 100}],
            [{"category": "ui", "count": 100}],
            [{"category": "unknown xyz", "count": 50}],
            [{"category": "pricing", "count": 1}, {"category": "naming", "count": 1}],
        ]
        for objections in cases:
            result = compute_objection_severity(objections)
            assert 0.0 <= result <= 1.0, f"out of bounds for {objections}: {result}"


# ---------------------------------------------------------------------------
# compute_silence_penalty
# ---------------------------------------------------------------------------


class TestComputeSilencePenalty:
    def test_zero_returns_zero(self):
        assert compute_silence_penalty(0) == 0.0

    def test_hundred_returns_one(self):
        assert compute_silence_penalty(100) == 1.0

    def test_fifty_returns_half(self):
        assert abs(compute_silence_penalty(50) - 0.5) < 1e-6

    def test_out_of_range_high_clamped_to_one(self):
        assert compute_silence_penalty(150) == 1.0

    def test_negative_clamped_to_zero(self):
        assert compute_silence_penalty(-10) == 0.0

    def test_monotonic_increase(self):
        vals = [compute_silence_penalty(p) for p in range(0, 101, 10)]
        assert vals == sorted(vals), "penalty should be monotonically non-decreasing"

    def test_result_bounded_zero_to_one(self):
        for pct in [-100, -1, 0, 25, 50, 75, 100, 101, 200]:
            result = compute_silence_penalty(pct)
            assert 0.0 <= result <= 1.0, f"out of bounds for pct={pct}: {result}"

    def test_exact_quarter(self):
        assert abs(compute_silence_penalty(25) - 0.25) < 1e-6

    def test_exact_three_quarters(self):
        assert abs(compute_silence_penalty(75) - 0.75) < 1e-6
