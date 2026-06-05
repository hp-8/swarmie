"""
PMF Readiness Index — runtime scorer.

Pure stdlib + math only. No sklearn, no numpy.

Loads calibrated weights from index_weights_v1.json (sibling of this file).
If the file is absent the scorer degrades gracefully: returns value=None with
calibration_status="uncalibrated — no weights".

Public surface
--------------
PmfIndex.score(dims, confidence) -> dict | None
dims_from_report(report)         -> dict   (5 numeric dims from a RoastReport dict)
"""

from __future__ import annotations

import json
import logging
import math
import os
from typing import Any

logger = logging.getLogger("swarmie.swarm.pmf_index")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
_WEIGHTS_PATH = os.path.join(_HERE, "index_weights_v1.json")

# ---------------------------------------------------------------------------
# Band half-widths per confidence level
# ---------------------------------------------------------------------------

_BAND_HALF: dict[str, float] = {
    "low": 18.0,
    "med": 10.0,
    "high": 5.0,
}

# AUC range that signals degenerate (no separation) calibration
_DEGENERATE_AUC_LO = 0.45
_DEGENERATE_AUC_HI = 0.55

# DIM_ORDER must match the JSON file
_EXPECTED_DIM_COUNT = 5


class PmfIndex:
    """Versioned PMF Readiness Index scorer.

    Usage::

        idx = PmfIndex()
        result = idx.score(dims, confidence="low")

    The instance caches loaded weights after the first call to ``score``.
    """

    def __init__(self, weights_path: str = _WEIGHTS_PATH) -> None:
        self._weights_path = weights_path
        self._weights: dict[str, Any] | None = None
        self._loaded: bool = False  # True even if weights file is missing

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, dims: dict[str, float], confidence: str = "low") -> dict[str, Any]:
        """Compute the PMF Readiness Index for a single run.

        Parameters
        ----------
        dims:
            Dict with exactly the 5 numeric dimension keys:
            engagement_rate, sentiment_score, segment_fit,
            objection_severity, silence_penalty.
        confidence:
            One of "low" | "med" | "high".  Controls the band half-width.

        Returns
        -------
        dict with keys:
            value              float | None   — 0..100 point estimate
            band               [lo, hi] | None
            index_version      str | None
            calibration_status str
        """
        weights = self._load_weights()

        if weights is None:
            return {
                "value": None,
                "band": None,
                "index_version": None,
                "calibration_status": "uncalibrated — no weights",
            }

        # --- compute logit ---
        dim_order: list[str] = weights["dim_order"]
        coef: list[float] = weights["coef"]
        intercept: float = weights["intercept"]
        scaler_mean: list[float] = weights["scaler_mean"]
        scaler_scale: list[float] = weights["scaler_scale"]
        cv_auc: float = weights["cv_auc"]
        index_version: str = weights["index_version"]

        logit = intercept
        for i, dim_name in enumerate(dim_order):
            x = float(dims.get(dim_name, 0.0))
            scale = scaler_scale[i]
            if scale == 0.0:
                z = 0.0
            else:
                z = (x - scaler_mean[i]) / scale
            logit += coef[i] * z

        p = 1.0 / (1.0 + math.exp(-logit))
        value = round(p * 100.0, 1)

        # --- band ---
        half = _BAND_HALF.get(confidence, _BAND_HALF["low"])
        lo = round(max(0.0, value - half), 1)
        hi = round(min(100.0, value + half), 1)

        # --- calibration status ---
        if _DEGENERATE_AUC_LO <= cv_auc <= _DEGENERATE_AUC_HI:
            calibration_status = "uncalibrated — separation not demonstrated"
        else:
            calibration_status = (
                f"calibrated v1 · YC-matured · AUC {cv_auc:.2f}"
            )

        return {
            "value": value,
            "band": [lo, hi],
            "index_version": index_version,
            "calibration_status": calibration_status,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_weights(self) -> dict[str, Any] | None:
        """Load and cache weights from the JSON file. Returns None if missing."""
        if self._loaded:
            return self._weights

        self._loaded = True
        if not os.path.exists(self._weights_path):
            logger.warning(
                "pmf_index: weights file not found at %s — index disabled",
                self._weights_path,
            )
            self._weights = None
            return None

        try:
            with open(self._weights_path, encoding="utf-8") as fh:
                data = json.load(fh)
            self._weights = data
            return data
        except Exception as exc:
            logger.warning("pmf_index: failed to load weights: %s", exc)
            self._weights = None
            return None


# ---------------------------------------------------------------------------
# Module-level singleton (used by roast_reporter)
# ---------------------------------------------------------------------------

_instance: PmfIndex | None = None


def _get_instance() -> PmfIndex:
    global _instance
    if _instance is None:
        _instance = PmfIndex()
    return _instance


def score(dims: dict[str, float], confidence: str = "low") -> dict[str, Any]:
    """Module-level convenience wrapper around the singleton PmfIndex."""
    return _get_instance().score(dims, confidence)


# ---------------------------------------------------------------------------
# dims_from_report
# ---------------------------------------------------------------------------

def dims_from_report(report: dict[str, Any]) -> dict[str, float]:
    """Compute the 5 numeric PMF Index dimensions from a RoastReport dict.

    Mirrors the formulas in roast_reporter._compute_pmf_score for the first
    three dims, then calls compute_objection_severity / compute_silence_penalty
    for the remaining two.

    Parameters
    ----------
    report:
        A dict produced by ``RoastReport.to_dict()``.

    Returns
    -------
    dict with keys:
        engagement_rate, sentiment_score, segment_fit,
        objection_severity, silence_penalty
    """
    # Import here to avoid circular import at module level; these are pure
    # functions with no side-effects.
    from .roast_reporter import compute_objection_severity, compute_silence_penalty

    action_split: dict[str, int] = report.get("action_split", {})
    sentiment_split: dict[str, float] = report.get("sentiment_split", {})
    icp_fit: dict[str, dict[str, Any]] = report.get("icp_fit", {})
    top_objections: list[dict[str, Any]] = report.get("top_objections", [])
    silent_share_pct: float = float(report.get("silent_share_pct", 0.0))

    # --- engagement_rate ---
    total_actions = sum(action_split.values()) or 1
    engagement_rate = (
        action_split.get("comment", 0)
        + action_split.get("post", 0)
        + 0.5 * action_split.get("upvote", 0)
    ) / total_actions

    # --- sentiment_score ---
    pos = float(sentiment_split.get("positive", 0.0))
    neg = float(sentiment_split.get("negative", 0.0))
    sentiment_score = (pos - neg) / 100.0

    # --- segment_fit ---
    total_seg_agents = sum(v.get("count", 0) for v in icp_fit.values()) or 1
    segment_fit = (
        sum(v.get("count", 0) for v in icp_fit.values() if v.get("avg_sentiment", 0.0) > 0.1)
        / total_seg_agents
    )

    # --- objection_severity ---
    objection_severity = compute_objection_severity(top_objections)

    # --- silence_penalty ---
    silence_penalty = compute_silence_penalty(silent_share_pct)

    return {
        "engagement_rate": round(engagement_rate, 6),
        "sentiment_score": round(sentiment_score, 6),
        "segment_fit": round(segment_fit, 6),
        "objection_severity": round(objection_severity, 6),
        "silence_penalty": round(silence_penalty, 6),
    }
