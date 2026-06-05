"""
Tests for eval/backtest/corpus.py — pinned against the cached yc_all.json snapshot.

Run: cd backend && python -m pytest tests/test_backtest_corpus.py -q
"""

import pytest

from eval.backtest.corpus import (
    DATA_PATH,
    batch_year,
    label_of,
    load_raw,
    load_tier1,
)

# The yc_all.json corpus cache is gitignored (data/ rule) — absent on a fresh
# CI checkout. Skip the whole module when it isn't cached locally; fetch it via
# the Colab notebook or `python -m eval.backtest.corpus`.
if not DATA_PATH.exists():
    pytest.skip(
        "yc_all.json corpus cache absent — gitignored; fetch to run these pins",
        allow_module_level=True,
    )


# ---------------------------------------------------------------------------
# load_raw
# ---------------------------------------------------------------------------

class TestLoadRaw:
    def test_length(self):
        """Pinned count: 5953 companies in the cached snapshot."""
        data = load_raw()
        assert len(data) == 5953

    def test_returns_list_of_dicts(self):
        data = load_raw()
        assert isinstance(data, list)
        assert isinstance(data[0], dict)


# ---------------------------------------------------------------------------
# batch_year
# ---------------------------------------------------------------------------

class TestBatchYear:
    def test_winter_2012(self):
        assert batch_year("Winter 2012") == 2012

    def test_summer_2018(self):
        assert batch_year("Summer 2018") == 2018

    def test_none_input(self):
        assert batch_year(None) is None

    def test_empty_string(self):
        assert batch_year("") is None

    def test_no_year(self):
        assert batch_year("Winter") is None


# ---------------------------------------------------------------------------
# label_of
# ---------------------------------------------------------------------------

class TestLabelOf:
    def test_acquired(self):
        assert label_of("Acquired") == 1

    def test_public(self):
        assert label_of("Public") == 1

    def test_inactive(self):
        assert label_of("Inactive") == 0

    def test_active_excluded(self):
        assert label_of("Active") is None

    def test_none_input(self):
        assert label_of(None) is None

    def test_unknown_status(self):
        assert label_of("Something Else") is None


# ---------------------------------------------------------------------------
# load_tier1 — pinned counts
# ---------------------------------------------------------------------------

class TestLoadTier1:
    """All counts are pinned against the cached yc_all.json snapshot."""

    @pytest.fixture(scope="class")
    def tier1(self):
        return load_tier1()

    @pytest.fixture(scope="class")
    def raw(self):
        return load_raw()

    def test_matured_total_count(self, raw):
        """1668 companies have batch_year <= 2018 (Active + hits + flops)."""
        count = sum(
            1 for c in raw
            if batch_year(c.get("batch")) is not None
            and batch_year(c.get("batch")) <= 2018
        )
        assert count == 1668

    def test_hit_count(self, tier1):
        """490 hits (Acquired + Public) in matured batches."""
        hits = [c for c in tier1 if c["label"] == 1]
        assert len(hits) == 490

    def test_flop_count(self, tier1):
        """562 flops (Inactive) in matured batches."""
        flops = [c for c in tier1 if c["label"] == 0]
        assert len(flops) == 562

    def test_excluded_active_count(self, raw):
        """616 Active companies in matured batches are excluded (censored)."""
        excluded = [
            c for c in raw
            if batch_year(c.get("batch")) is not None
            and batch_year(c.get("batch")) <= 2018
            and c.get("status") == "Active"
        ]
        assert len(excluded) == 616

    def test_tier1_total(self, tier1):
        """Tier-1 = hits + flops = 490 + 562 = 1052."""
        assert len(tier1) == 1052

    def test_all_labels_non_none(self, tier1):
        """Every returned case must have label in {0, 1}."""
        for case in tier1:
            assert case["label"] in {0, 1}

    def test_required_keys_present(self, tier1):
        required = {"id", "name", "former_names", "raw_text", "label", "status", "batch"}
        for case in tier1:
            assert required <= case.keys(), f"Missing keys in: {case}"

    def test_raw_text_is_string(self, tier1):
        for case in tier1:
            assert isinstance(case["raw_text"], str)

    def test_no_active_in_tier1(self, tier1):
        """Active companies must not appear in tier1."""
        for case in tier1:
            assert case["status"] != "Active"
