"""
Tests for eval.backtest.runner — NO network, NO real LLM.

All three test classes use only injected/canned data:
  - TestExtractDims:   hand-built report dict → assert 6 values match hand-computed numbers.
  - TestRunFunction:   injected fake report_fn → assert row count, keys, class balance.
  - TestBuildSample:   deterministic seed → same ids on two calls.

The real pipeline (PitchParser, SwarmRunner, etc.) is never imported in this module.
"""

from __future__ import annotations

import os
import sys

# Boot guard: Config requires SECRET_KEY before any app.* import.
os.environ.setdefault("SECRET_KEY", "test-secret-key")

# Make backend/ the import root (mirrors conftest.py pattern in this repo).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from eval.backtest.runner import extract_dims, run, build_sample, run_case


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_report(
    *,
    positive: float = 40.0,
    neutral: float = 30.0,
    negative: float = 30.0,
    post: int = 5,
    comment: int = 15,
    upvote: int = 10,
    ignore: int = 20,
    segments: dict | None = None,
    top_objections: list | None = None,
    silent_share_pct: float = 40.0,
) -> dict:
    """Construct a minimal RoastReport dict for testing."""
    if segments is None:
        segments = {
            "founders": {"count": 30, "avg_sentiment": 0.3},
            "investors": {"count": 10, "avg_sentiment": -0.2},
        }
    if top_objections is None:
        top_objections = [
            {"category": "pricing too high", "count": 4},
            {"category": "unclear messaging", "count": 4},
        ]
    return {
        "sentiment_split": {
            "positive": positive,
            "neutral":  neutral,
            "negative": negative,
        },
        "action_split": {
            "post":    post,
            "comment": comment,
            "upvote":  upvote,
            "ignore":  ignore,
        },
        "icp_fit": segments,
        "top_objections": top_objections,
        "silent_share_pct": silent_share_pct,
    }


# ---------------------------------------------------------------------------
# TestExtractDims — hand-computed assertions
# ---------------------------------------------------------------------------

class TestExtractDims:
    """extract_dims: values must match formulas documented in the spec."""

    def test_engagement_rate_formula(self):
        """engagement_rate = (comment + post + 0.5*upvote) / total_actions."""
        report = _make_report(post=5, comment=15, upvote=10, ignore=20)
        # total = 5+15+10+20 = 50
        # numerator = 15 + 5 + 0.5*10 = 25
        # rate = 25/50 = 0.5
        dims = extract_dims(report)
        assert abs(dims["engagement_rate"] - 0.5) < 1e-6

    def test_sentiment_score_formula(self):
        """sentiment_score = (positive - negative) / 100."""
        report = _make_report(positive=60.0, negative=20.0)
        # (60 - 20) / 100 = 0.4
        dims = extract_dims(report)
        assert abs(dims["sentiment_score"] - 0.4) < 1e-6

    def test_sentiment_score_negative(self):
        report = _make_report(positive=10.0, negative=70.0)
        # (10 - 70) / 100 = -0.6
        dims = extract_dims(report)
        assert abs(dims["sentiment_score"] - (-0.6)) < 1e-6

    def test_segment_fit_size_weighted(self):
        """segment_fit = count of agents in segments with avg_sentiment > 0.1 / total agents."""
        report = _make_report(segments={
            "founders":  {"count": 30, "avg_sentiment": 0.3},   # qualifies
            "investors": {"count": 10, "avg_sentiment": -0.2},  # does not qualify
        })
        # positive agents = 30, total = 40
        # segment_fit = 30/40 = 0.75
        dims = extract_dims(report)
        assert abs(dims["segment_fit"] - 0.75) < 1e-6

    def test_segment_fit_threshold_boundary(self):
        """avg_sentiment == 0.1 is NOT > 0.1 (strict inequality)."""
        report = _make_report(segments={
            "a": {"count": 20, "avg_sentiment": 0.1},   # at boundary — does NOT qualify
            "b": {"count": 20, "avg_sentiment": 0.11},  # qualifies
        })
        # positive = 20, total = 40 → 0.5
        dims = extract_dims(report)
        assert abs(dims["segment_fit"] - 0.5) < 1e-6

    def test_objection_severity_delegated(self):
        """objection_severity matches compute_objection_severity from roast_reporter."""
        # pricing (FUNDAMENTAL 1.0) × 4 + unclear (FRAMING 0.5) × 4
        # = (4.0 + 2.0) / 8 = 0.75
        report = _make_report(top_objections=[
            {"category": "pricing objection", "count": 4},
            {"category": "unclear messaging", "count": 4},
        ])
        dims = extract_dims(report)
        assert abs(dims["objection_severity"] - 0.75) < 1e-5

    def test_silence_penalty_delegated(self):
        """silence_penalty = clamp(silent_share_pct / 100, 0, 1)."""
        report = _make_report(silent_share_pct=60.0)
        dims = extract_dims(report)
        assert abs(dims["silence_penalty"] - 0.6) < 1e-6

    def test_all_6_keys_present(self):
        report = _make_report()
        dims = extract_dims(report)
        expected_keys = {
            "engagement_rate",
            "sentiment_score",
            "segment_fit",
            "objection_severity",
            "silence_penalty",
        }
        assert set(dims.keys()) == expected_keys

    def test_bounds_sanity(self):
        """All 5 numeric dimensions must be within [-1, 1]."""
        report = _make_report()
        dims = extract_dims(report)
        # engagement_rate, segment_fit, objection_severity, silence_penalty → [0,1]
        for key in ("engagement_rate", "segment_fit", "objection_severity", "silence_penalty"):
            assert 0.0 <= dims[key] <= 1.0, f"{key} out of [0,1]: {dims[key]}"
        # sentiment_score → [-1, 1]
        assert -1.0 <= dims["sentiment_score"] <= 1.0, f"sentiment_score out of [-1,1]: {dims['sentiment_score']}"

    def test_zero_actions_guard(self):
        """All-zero action_split must not raise (total guard clamps to 1)."""
        report = _make_report(post=0, comment=0, upvote=0, ignore=0)
        dims = extract_dims(report)
        assert dims["engagement_rate"] == 0.0

    def test_empty_icp_fit_guard(self):
        """Empty icp_fit must not raise (total_seg_agents guard clamps to 1)."""
        report = _make_report(segments={})
        dims = extract_dims(report)
        assert dims["segment_fit"] == 0.0

    def test_empty_top_objections(self):
        """Empty top_objections → objection_severity = 0.0."""
        report = _make_report(top_objections=[])
        dims = extract_dims(report)
        assert dims["objection_severity"] == 0.0

    def test_full_silence(self):
        """100% silence → silence_penalty = 1.0."""
        report = _make_report(silent_share_pct=100.0)
        dims = extract_dims(report)
        assert dims["silence_penalty"] == 1.0

    def test_no_silence(self):
        """0% silence → silence_penalty = 0.0."""
        report = _make_report(silent_share_pct=0.0)
        dims = extract_dims(report)
        assert dims["silence_penalty"] == 0.0

    def test_all_negative_sentiment(self):
        report = _make_report(positive=0.0, negative=100.0)
        dims = extract_dims(report)
        assert abs(dims["sentiment_score"] - (-1.0)) < 1e-6

    def test_all_positive_sentiment(self):
        report = _make_report(positive=100.0, negative=0.0)
        dims = extract_dims(report)
        assert abs(dims["sentiment_score"] - 1.0) < 1e-6

    def test_missing_fields_default_gracefully(self):
        """A nearly-empty report dict should not raise."""
        dims = extract_dims({})
        assert set(dims.keys()) == {
            "engagement_rate", "sentiment_score", "segment_fit",
            "objection_severity", "silence_penalty",
        }
        for val in dims.values():
            assert isinstance(val, float)


# ---------------------------------------------------------------------------
# TestRunFunction — injected fake report_fn
# ---------------------------------------------------------------------------

class TestRunFunction:
    """run() with a fake report_fn: assert row count, keys, label presence."""

    @staticmethod
    def _fake_report_fn(pitch_text: str) -> dict:
        """Returns a deterministic canned report regardless of input."""
        return _make_report()

    def _make_mini_sample(self, n_hits: int = 3, n_flops: int = 3) -> list[dict]:
        hits  = [{"id": f"h{i}", "label": 1, "text": f"pitch hit {i}"}  for i in range(n_hits)]
        flops = [{"id": f"f{i}", "label": 0, "text": f"pitch flop {i}"} for i in range(n_flops)]
        return hits + flops

    def test_row_count_single_repeat(self):
        sample = self._make_mini_sample(3, 3)
        rows = run(sample, repeats=1, report_fn=self._fake_report_fn)
        assert len(rows) == 6

    def test_row_count_multiple_repeats(self):
        sample = self._make_mini_sample(2, 2)
        rows = run(sample, repeats=3, report_fn=self._fake_report_fn)
        assert len(rows) == 12  # 4 cases × 3 repeats

    def test_each_row_has_required_keys(self):
        sample = self._make_mini_sample(1, 1)
        rows = run(sample, repeats=1, report_fn=self._fake_report_fn)
        required = {
            "id", "label", "run_idx",
            "engagement_rate", "sentiment_score", "segment_fit",
            "objection_severity", "silence_penalty",
        }
        for row in rows:
            assert required.issubset(set(row.keys())), f"Missing keys in row: {row}"

    def test_labels_are_preserved(self):
        sample = self._make_mini_sample(3, 3)
        rows = run(sample, repeats=1, report_fn=self._fake_report_fn)
        hit_rows  = [r for r in rows if r["label"] == 1]
        flop_rows = [r for r in rows if r["label"] == 0]
        assert len(hit_rows) == 3
        assert len(flop_rows) == 3

    def test_balanced_classes(self):
        """With equal n_hits and n_flops in sample, rows stay balanced."""
        sample = self._make_mini_sample(5, 5)
        rows = run(sample, repeats=2, report_fn=self._fake_report_fn)
        hit_rows  = [r for r in rows if r["label"] == 1]
        flop_rows = [r for r in rows if r["label"] == 0]
        assert len(hit_rows) == len(flop_rows) == 10

    def test_run_idx_values(self):
        """run_idx should be 0..repeats-1 for each case."""
        sample = self._make_mini_sample(1, 0)
        repeats = 4
        rows = run(sample, repeats=repeats, report_fn=self._fake_report_fn)
        assert sorted(r["run_idx"] for r in rows) == list(range(repeats))

    def test_failure_in_report_fn_skips_row(self):
        """A crashing report_fn skips that row; other rows still collected."""
        call_count = {"n": 0}

        def _sometimes_fails(pitch_text: str) -> dict:
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise RuntimeError("simulated LLM failure")
            return _make_report()

        sample = self._make_mini_sample(2, 0)
        rows = run(sample, repeats=1, report_fn=_sometimes_fails)
        # 2 calls total; 1 fails → only 1 row collected
        assert len(rows) == 1

    def test_dims_from_canned_report_match_extract_dims(self):
        """Values in rows must match what extract_dims would return for the canned report."""
        expected = extract_dims(_make_report())
        sample = self._make_mini_sample(1, 0)
        rows = run(sample, repeats=1, report_fn=self._fake_report_fn)
        row = rows[0]
        for key, val in expected.items():
            assert abs(row[key] - val) < 1e-9, f"Mismatch on {key}: {row[key]} != {val}"

    def test_run_case_direct(self):
        """run_case returns the same 5-dim dict as extract_dims."""
        expected = extract_dims(_make_report())
        dims = run_case("any pitch text", report_fn=self._fake_report_fn)
        assert dims == expected


# ---------------------------------------------------------------------------
# TestBuildSample — deterministic seed, requires yc_all.json (skip if absent)
# ---------------------------------------------------------------------------

class TestBuildSample:
    """build_sample: deterministic for fixed seed; skip if corpus not present."""

    @pytest.fixture(autouse=True)
    def _skip_without_corpus(self):
        """Skip all tests in this class if yc_all.json is not cached locally."""
        from pathlib import Path
        data_path = (
            Path(__file__).parent.parent / "eval" / "backtest" / "data" / "yc_all.json"
        )
        if not data_path.exists():
            pytest.skip(
                "yc_all.json not present — run `python -m eval.backtest.corpus` to cache"
            )

    def test_deterministic_same_seed(self):
        """Two calls with the same seed return the same ids in the same order."""
        s1 = build_sample(n_per_class=10, seed=42)
        s2 = build_sample(n_per_class=10, seed=42)
        assert [c["id"] for c in s1] == [c["id"] for c in s2]

    def test_different_seeds_differ(self):
        """Different seeds should (almost certainly) return different samples."""
        s1 = build_sample(n_per_class=10, seed=1)
        s2 = build_sample(n_per_class=10, seed=2)
        ids1 = {c["id"] for c in s1}
        ids2 = {c["id"] for c in s2}
        # Allow up to 50% overlap — they should not be identical
        assert ids1 != ids2

    def test_returns_list_of_dicts(self):
        sample = build_sample(n_per_class=5, seed=42)
        assert isinstance(sample, list)
        assert all(isinstance(c, dict) for c in sample)

    def test_each_case_has_required_keys(self):
        sample = build_sample(n_per_class=5, seed=42)
        required = {"id", "name", "former_names", "text", "label", "status", "batch"}
        for case in sample:
            assert required.issubset(set(case.keys())), f"Missing keys: {case}"

    def test_text_is_non_empty_string(self):
        """Decontamination should have filtered empty texts."""
        sample = build_sample(n_per_class=5, seed=42)
        for case in sample:
            assert isinstance(case["text"], str)
            assert len(case["text"]) >= 15, f"Text too short: {case['text']!r}"

    def test_balanced_classes(self):
        """Should return equal hits and flops when corpus has enough of each."""
        n = 10
        sample = build_sample(n_per_class=n, seed=42)
        hits  = [c for c in sample if c["label"] == 1]
        flops = [c for c in sample if c["label"] == 0]
        assert len(hits) == n
        assert len(flops) == n

    def test_labels_are_binary(self):
        sample = build_sample(n_per_class=5, seed=42)
        for case in sample:
            assert case["label"] in (0, 1), f"Unexpected label: {case['label']}"
