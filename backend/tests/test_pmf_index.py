"""
Unit tests for PmfIndex and dims_from_report.

All tests are offline — no LLM, no network, no filesystem side-effects beyond
temp files created inside each test.

Test plan
---------
1. score() with a known fixture -> hand-verifiable value, bounds 0..100, band ordering
2. calibrated status string when cv_auc = 0.72
3. cv_auc = 0.50 -> "uncalibrated — separation not demonstrated"
4. missing weights file -> {value: None, band: None, ...} no crash
5. dims_from_report on a hand-built report dict -> 5 dims match expected
6. band clamping at edges (very low / very high logit)
7. confidence band widths (low=18, med=10, high=5)
"""

from __future__ import annotations

import json
import math
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.swarm.pmf_index import PmfIndex, dims_from_report


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_weights(cv_auc: float = 0.72) -> dict:
    """Build a minimal but realistic weights dict.

    Chosen values make the hand-computation easy:
      dim_order: [engagement_rate, sentiment_score, segment_fit,
                  objection_severity, silence_penalty]
      coef:      [1.0, 0.5, 0.5, -0.5, -0.5]
      intercept: 0.0
      scaler_mean:  [0.5, 0.0, 0.5, 0.5, 0.5]
      scaler_scale: [0.5, 1.0, 0.5, 0.5, 0.5]

    For dims = {engagement_rate=0.5, sentiment_score=0.0,
                segment_fit=0.5, objection_severity=0.5, silence_penalty=0.5}
    each z = (x - mean) / scale = 0.0 for every dim.
    logit = 0.0 + 0.0 = 0.0  =>  p = 0.5  =>  value = 50.0
    """
    return {
        "index_version": "1.0",
        "dim_order": [
            "engagement_rate",
            "sentiment_score",
            "segment_fit",
            "objection_severity",
            "silence_penalty",
        ],
        "coef": [1.0, 0.5, 0.5, -0.5, -0.5],
        "intercept": 0.0,
        "scaler_mean": [0.5, 0.0, 0.5, 0.5, 0.5],
        "scaler_scale": [0.5, 1.0, 0.5, 0.5, 0.5],
        "cv_auc": cv_auc,
        "n": 1052,
        "n_hits": 490,
        "n_flops": 562,
        "generated_at": "2026-06-05T00:00:00Z",
    }


def _write_weights(path: str, cv_auc: float = 0.72) -> None:
    with open(path, "w") as fh:
        json.dump(_make_weights(cv_auc), fh)


def _idx_from_tmp(cv_auc: float = 0.72) -> tuple[PmfIndex, str]:
    """Return a fresh PmfIndex pointing at a temp weights file + the temp dir."""
    tmp = tempfile.mkdtemp()
    weights_path = os.path.join(tmp, "index_weights_v1.json")
    _write_weights(weights_path, cv_auc)
    return PmfIndex(weights_path=weights_path), tmp


# ---------------------------------------------------------------------------
# Neutral dims (all at mean -> logit=0 -> value=50)
# ---------------------------------------------------------------------------

_NEUTRAL_DIMS = {
    "engagement_rate": 0.5,
    "sentiment_score": 0.0,
    "segment_fit": 0.5,
    "objection_severity": 0.5,
    "silence_penalty": 0.5,
}


# ---------------------------------------------------------------------------
# Test 1 + 2: known fixture, calibrated status
# ---------------------------------------------------------------------------

class TestScoreKnownValue:
    def test_neutral_dims_gives_50(self):
        idx, _ = _idx_from_tmp(cv_auc=0.72)
        result = idx.score(_NEUTRAL_DIMS, confidence="low")
        assert result["value"] == 50.0

    def test_value_in_0_100(self):
        idx, _ = _idx_from_tmp(cv_auc=0.72)
        result = idx.score(_NEUTRAL_DIMS, confidence="low")
        assert 0.0 <= result["value"] <= 100.0

    def test_band_is_list_of_two(self):
        idx, _ = _idx_from_tmp(cv_auc=0.72)
        result = idx.score(_NEUTRAL_DIMS, confidence="low")
        assert isinstance(result["band"], list)
        assert len(result["band"]) == 2

    def test_band_ordering_low_le_value_le_high(self):
        idx, _ = _idx_from_tmp(cv_auc=0.72)
        result = idx.score(_NEUTRAL_DIMS, confidence="low")
        lo, hi = result["band"]
        assert lo <= result["value"] <= hi

    def test_index_version_string(self):
        idx, _ = _idx_from_tmp(cv_auc=0.72)
        result = idx.score(_NEUTRAL_DIMS, confidence="low")
        assert result["index_version"] == "1.0"

    def test_calibrated_status_string_when_auc_072(self):
        idx, _ = _idx_from_tmp(cv_auc=0.72)
        result = idx.score(_NEUTRAL_DIMS, confidence="low")
        assert result["calibration_status"] == "calibrated v1 · YC-matured · AUC 0.72"

    def test_hand_computed_non_neutral_dims(self):
        """
        dims: engagement_rate=1.0 (z=(1.0-0.5)/0.5=1.0)
              sentiment_score=1.0 (z=(1.0-0.0)/1.0=1.0)
              segment_fit=0.5    (z=0.0)
              objection_severity=0.5 (z=0.0)
              silence_penalty=0.5    (z=0.0)
        logit = 0 + 1.0*1.0 + 0.5*1.0 + 0 + 0 + 0 = 1.5
        p = 1/(1+exp(-1.5)) ≈ 0.8176...
        value = round(81.76..., 1) = 81.8
        """
        idx, _ = _idx_from_tmp(cv_auc=0.72)
        dims = {**_NEUTRAL_DIMS, "engagement_rate": 1.0, "sentiment_score": 1.0}
        result = idx.score(dims, confidence="high")
        expected_logit = 1.5
        expected_p = 1.0 / (1.0 + math.exp(-expected_logit))
        expected_value = round(expected_p * 100.0, 1)
        assert result["value"] == expected_value


# ---------------------------------------------------------------------------
# Test 3: degenerate AUC -> uncalibrated status
# ---------------------------------------------------------------------------

class TestDegenerateAUC:
    @pytest.mark.parametrize("auc", [0.45, 0.50, 0.55])
    def test_degenerate_auc_gives_uncalibrated_status(self, auc):
        idx, _ = _idx_from_tmp(cv_auc=auc)
        result = idx.score(_NEUTRAL_DIMS, confidence="low")
        assert result["calibration_status"] == "uncalibrated — separation not demonstrated"

    def test_degenerate_auc_still_returns_value(self):
        """Degenerate AUC doesn't suppress the value — only relabels status."""
        idx, _ = _idx_from_tmp(cv_auc=0.50)
        result = idx.score(_NEUTRAL_DIMS, confidence="low")
        assert result["value"] == 50.0

    def test_auc_just_above_degenerate_is_calibrated(self):
        idx, _ = _idx_from_tmp(cv_auc=0.56)
        result = idx.score(_NEUTRAL_DIMS, confidence="low")
        assert result["calibration_status"].startswith("calibrated")

    def test_auc_just_below_degenerate_is_calibrated(self):
        idx, _ = _idx_from_tmp(cv_auc=0.44)
        result = idx.score(_NEUTRAL_DIMS, confidence="low")
        assert result["calibration_status"].startswith("calibrated")


# ---------------------------------------------------------------------------
# Test 4: missing weights file
# ---------------------------------------------------------------------------

class TestMissingWeightsFile:
    def test_missing_file_returns_none_value(self):
        idx = PmfIndex(weights_path="/tmp/__no_such_weights_file_ever__.json")
        result = idx.score(_NEUTRAL_DIMS, confidence="low")
        assert result["value"] is None

    def test_missing_file_returns_none_band(self):
        idx = PmfIndex(weights_path="/tmp/__no_such_weights_file_ever__.json")
        result = idx.score(_NEUTRAL_DIMS, confidence="low")
        assert result["band"] is None

    def test_missing_file_returns_none_index_version(self):
        idx = PmfIndex(weights_path="/tmp/__no_such_weights_file_ever__.json")
        result = idx.score(_NEUTRAL_DIMS, confidence="low")
        assert result["index_version"] is None

    def test_missing_file_calibration_status(self):
        idx = PmfIndex(weights_path="/tmp/__no_such_weights_file_ever__.json")
        result = idx.score(_NEUTRAL_DIMS, confidence="low")
        assert result["calibration_status"] == "uncalibrated — no weights"

    def test_missing_file_does_not_crash(self):
        idx = PmfIndex(weights_path="/tmp/__no_such_weights_file_ever__.json")
        # Must not raise
        result = idx.score(_NEUTRAL_DIMS, confidence="high")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Test 5: dims_from_report
# ---------------------------------------------------------------------------

class TestDimsFromReport:
    def _make_report(self) -> dict:
        return {
            "action_split": {"post": 10, "comment": 20, "upvote": 10, "ignore": 60},
            "sentiment_split": {"positive": 40.0, "neutral": 30.0, "negative": 30.0},
            "icp_fit": {
                "founders": {"count": 30, "avg_sentiment": 0.5},   # positive
                "investors": {"count": 20, "avg_sentiment": -0.3},  # negative
                "engineers": {"count": 50, "avg_sentiment": 0.2},   # positive
            },
            "top_objections": [
                {"category": "pricing too high", "count": 10},  # FUNDAMENTAL 1.0
                {"category": "unclear messaging", "count": 10}, # FRAMING 0.5
            ],
            "silent_share_pct": 60.0,
        }

    def test_engagement_rate(self):
        report = self._make_report()
        # total = 10+20+10+60 = 100
        # engagement = (20+10+0.5*10)/100 = 35/100 = 0.35
        dims = dims_from_report(report)
        assert abs(dims["engagement_rate"] - 0.35) < 1e-5

    def test_sentiment_score(self):
        report = self._make_report()
        # (40-30)/100 = 0.10
        dims = dims_from_report(report)
        assert abs(dims["sentiment_score"] - 0.10) < 1e-5

    def test_segment_fit(self):
        report = self._make_report()
        # positive segments (avg_sentiment > 0.1): founders(30) + engineers(50) = 80
        # total = 100
        # segment_fit = 80/100 = 0.80
        dims = dims_from_report(report)
        assert abs(dims["segment_fit"] - 0.80) < 1e-5

    def test_objection_severity(self):
        report = self._make_report()
        # pricing(FUNDAMENTAL 1.0)*10 + unclear(FRAMING 0.5)*10 = 15 / 20 = 0.75
        dims = dims_from_report(report)
        assert abs(dims["objection_severity"] - 0.75) < 1e-5

    def test_silence_penalty(self):
        report = self._make_report()
        # 60.0 / 100 = 0.60
        dims = dims_from_report(report)
        assert abs(dims["silence_penalty"] - 0.60) < 1e-5

    def test_all_five_keys_present(self):
        dims = dims_from_report(self._make_report())
        expected = {"engagement_rate", "sentiment_score", "segment_fit",
                    "objection_severity", "silence_penalty"}
        assert set(dims.keys()) == expected

    def test_empty_report_does_not_crash(self):
        dims = dims_from_report({})
        assert isinstance(dims, dict)
        assert len(dims) == 5

    def test_dims_all_in_range(self):
        dims = dims_from_report(self._make_report())
        for key, val in dims.items():
            assert 0.0 <= val <= 1.0 or key == "sentiment_score", (
                f"{key}={val} out of expected [0,1] (sentiment_score may be negative)"
            )


# ---------------------------------------------------------------------------
# Test 6: band clamping at edges
# ---------------------------------------------------------------------------

class TestBandClamping:
    def test_high_value_band_hi_clamped_to_100(self):
        """With logit >> 0 the point value will be near 100; band[1] must stay <= 100."""
        idx, _ = _idx_from_tmp(cv_auc=0.72)
        # All dims at their best extreme: engagement=1, sentiment=1, segment=1, objection=0, silence=0
        dims = {
            "engagement_rate": 1.0,
            "sentiment_score": 1.0,
            "segment_fit": 1.0,
            "objection_severity": 0.0,
            "silence_penalty": 0.0,
        }
        result = idx.score(dims, confidence="low")
        lo, hi = result["band"]
        assert hi <= 100.0
        assert lo >= 0.0

    def test_low_value_band_lo_clamped_to_0(self):
        """With logit << 0 the point value will be near 0; band[0] must stay >= 0."""
        idx, _ = _idx_from_tmp(cv_auc=0.72)
        dims = {
            "engagement_rate": 0.0,
            "sentiment_score": -1.0,
            "segment_fit": 0.0,
            "objection_severity": 1.0,
            "silence_penalty": 1.0,
        }
        result = idx.score(dims, confidence="low")
        lo, hi = result["band"]
        assert lo >= 0.0
        assert hi <= 100.0


# ---------------------------------------------------------------------------
# Test 7: confidence band widths
# ---------------------------------------------------------------------------

class TestConfidenceBandWidths:
    def _neutral_score(self, confidence: str) -> dict:
        idx, _ = _idx_from_tmp(cv_auc=0.72)
        return idx.score(_NEUTRAL_DIMS, confidence=confidence)

    def test_low_confidence_band_width_is_36(self):
        r = self._neutral_score("low")
        lo, hi = r["band"]
        # value=50 -> band=[32.0, 68.0] -> width = 36
        assert abs((hi - lo) - 36.0) < 0.2

    def test_med_confidence_band_width_is_20(self):
        r = self._neutral_score("med")
        lo, hi = r["band"]
        assert abs((hi - lo) - 20.0) < 0.2

    def test_high_confidence_band_width_is_10(self):
        r = self._neutral_score("high")
        lo, hi = r["band"]
        assert abs((hi - lo) - 10.0) < 0.2

    def test_unknown_confidence_falls_back_to_low(self):
        idx, _ = _idx_from_tmp(cv_auc=0.72)
        r = idx.score(_NEUTRAL_DIMS, confidence="ultra")
        lo, hi = r["band"]
        # Should use low-width (36)
        assert abs((hi - lo) - 36.0) < 0.2
