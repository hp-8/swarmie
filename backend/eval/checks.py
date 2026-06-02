"""
Deterministic scoring checks for eval harness.

All checks accept a RoastReport dict (from report.to_dict()) and a golden
case spec dict. Returns (passed: bool, detail: str).
"""

from __future__ import annotations
from typing import Any


# Required top-level keys and their expected types
_REQUIRED_SCHEMA: dict[str, type] = {
    "pmf_score": float,
    "headline": str,
    "sentiment_split": dict,
    "action_split": dict,
    "top_objections": list,
    "icp_fit": dict,
    "messaging_gaps": list,
    "narrative": str,
    "quoted_reactions": list,
    "verdict": str,
    "verdict_reason": str,
    "next_action": str,
    "confidence": str,
    "confidence_reason": str,
    "ignore_reasons": list,
    "silent_share_pct": float,
}

_VALID_CONFIDENCES = {"low", "med", "high"}

# Per-swarm-type valid verdicts (matches reporter classes)
_VALID_VERDICTS: dict[str, set[str]] = {
    "validate": {"ship_it", "sharpen_positioning", "wrong_audience", "kill"},
    "investor": {"fundable", "sharpen_story", "wrong_stage", "not_fundable"},
    "launch": {"go", "sharpen", "hold"},
}


def check_schema(report: dict, swarm_type: str = "validate") -> tuple[bool, str]:
    """All required keys present with correct types."""
    missing = []
    wrong_type = []
    for key, expected_type in _REQUIRED_SCHEMA.items():
        if key not in report:
            missing.append(key)
        elif not isinstance(report[key], expected_type):
            wrong_type.append(f"{key}={type(report[key]).__name__} (expected {expected_type.__name__})")
    if missing or wrong_type:
        parts = []
        if missing:
            parts.append(f"missing keys: {missing}")
        if wrong_type:
            parts.append(f"wrong types: {wrong_type}")
        return False, "; ".join(parts)
    return True, "all required keys present with correct types"


def check_verdict(report: dict, case: dict) -> tuple[bool, str]:
    """Verdict is in the expected set for this case."""
    verdict = report.get("verdict", "")
    expected = case["expected_verdicts"]
    swarm_type = case.get("swarm_type", "validate")
    valid_all = _VALID_VERDICTS.get(swarm_type, set())

    if verdict not in valid_all:
        return False, f"verdict '{verdict}' not valid for swarm_type '{swarm_type}' (valid: {valid_all})"
    if verdict in expected:
        return True, f"verdict '{verdict}' in expected set {expected}"
    return False, f"verdict '{verdict}' not in expected set {expected} (but is a valid enum value)"


def check_objection_themes(report: dict, case: dict, threshold: float = 0.5) -> tuple[bool, str]:
    """
    At least `threshold` fraction of required_objection_themes have a matching
    keyword found somewhere in top_objections (category or example_quote).

    'Match' = any keyword from the inner list appears (case-insensitive) in
    any objection category or example_quote string in the report.
    """
    required = case.get("required_objection_themes", [])
    if not required:
        return True, "no objection themes to check"

    top_objs = report.get("top_objections", [])
    # Build a single string corpus from all objection categories + quotes
    corpus = " ".join(
        (str(o.get("category", "")) + " " + str(o.get("example_quote", ""))).lower()
        for o in top_objs
    )

    matched = 0
    details = []
    for theme_kws in required:
        hit = any(kw.lower() in corpus for kw in theme_kws)
        if hit:
            matched += 1
            details.append(f"[hit] {theme_kws}")
        else:
            details.append(f"[miss] {theme_kws}")

    ratio = matched / len(required)
    passed = ratio >= threshold
    return passed, (
        f"{matched}/{len(required)} themes matched (threshold {threshold:.0%}): "
        + "; ".join(details)
    )


def check_pmf_direction(report: dict, case: dict) -> tuple[bool, str]:
    """PMF score is consistent with expected direction."""
    direction = case.get("pmf_direction", "neutral")
    score = report.get("pmf_score", 0.0)
    if not isinstance(score, (int, float)):
        return False, f"pmf_score is not numeric: {score}"
    score = float(score)
    if not (0.0 <= score <= 10.0):
        return False, f"pmf_score {score} out of range [0, 10]"

    if direction == "positive":
        passed = score >= 4.5
        return passed, f"pmf_score={score:.1f} {'OK' if passed else 'BELOW'} positive threshold 4.5"
    elif direction == "negative":
        passed = score < 6.0
        return passed, f"pmf_score={score:.1f} {'OK' if passed else 'ABOVE'} negative ceiling 6.0"
    else:  # neutral
        return True, f"pmf_score={score:.1f} (neutral — no direction check)"


def check_confidence_ceiling(report: dict, case: dict) -> tuple[bool, str]:
    """Confidence does not exceed the case's declared ceiling."""
    ceiling = case.get("confidence_ceiling", "high")
    confidence = report.get("confidence", "low")
    rank = {"low": 0, "med": 1, "high": 2}
    if confidence not in rank:
        return False, f"confidence '{confidence}' not a valid enum (low/med/high)"
    ceiling_rank = rank.get(ceiling, 2)
    conf_rank = rank[confidence]
    passed = conf_rank <= ceiling_rank
    return passed, f"confidence='{confidence}' {'<=' if passed else '>'} ceiling='{ceiling}'"


def check_sentiment_split_sums(report: dict, **_) -> tuple[bool, str]:
    """Sentiment split percentages sum to ~100 (within 1 point)."""
    ss = report.get("sentiment_split", {})
    total = sum(ss.values()) if isinstance(ss, dict) else 0
    passed = abs(total - 100.0) <= 1.5
    return passed, f"sentiment_split sum={total:.1f} ({'OK' if passed else 'WRONG — should be ~100'})"


def check_action_split_non_negative(report: dict, **_) -> tuple[bool, str]:
    """All action_split counts are non-negative integers."""
    asp = report.get("action_split", {})
    bad = [(k, v) for k, v in asp.items() if not isinstance(v, int) or v < 0]
    if bad:
        return False, f"action_split has invalid values: {bad}"
    return True, f"action_split ok: {asp}"


def check_narrative_non_empty(report: dict, **_) -> tuple[bool, str]:
    """Narrative and headline are non-empty strings."""
    narrative = str(report.get("narrative", "")).strip()
    headline = str(report.get("headline", "")).strip()
    issues = []
    if not narrative:
        issues.append("narrative is empty")
    if not headline:
        issues.append("headline is empty")
    if issues:
        return False, "; ".join(issues)
    return True, f"headline ({len(headline)} chars), narrative ({len(narrative)} chars)"


def run_all_checks(report: dict, case: dict) -> list[dict[str, Any]]:
    """Run every deterministic check. Returns list of result dicts."""
    swarm_type = case.get("swarm_type", "validate")
    results = []

    checks = [
        ("schema", lambda: check_schema(report, swarm_type)),
        ("verdict", lambda: check_verdict(report, case)),
        ("objection_themes", lambda: check_objection_themes(report, case)),
        ("pmf_direction", lambda: check_pmf_direction(report, case)),
        ("confidence_ceiling", lambda: check_confidence_ceiling(report, case)),
        ("sentiment_split_sums", lambda: check_sentiment_split_sums(report)),
        ("action_split_non_negative", lambda: check_action_split_non_negative(report)),
        ("narrative_non_empty", lambda: check_narrative_non_empty(report)),
    ]

    for name, fn in checks:
        try:
            passed, detail = fn()
        except Exception as exc:
            passed, detail = False, f"check raised exception: {exc}"
        results.append({"check": name, "passed": passed, "detail": detail})

    return results
