"""
Tests for backend/eval/backtest/metrics.py

Hand-computed fixture verification:

AUC derivations (Mann-Whitney U / rank method):
  - scores=[1,2,3,4], labels=[0,0,1,1]:
      Hits at scores 3,4; flops at 1,2.
      Ranks: 1→1, 2→2, 3→3, 4→4. R1 = 3+4 = 7.
      U1 = 7 - 2*3/2 = 7 - 3 = 4. AUC = 4/(2*2) = 1.0.

  - scores=[1,2,3,4], labels=[1,1,0,0]:
      Hits at scores 1,2; flops at 3,4. U1 = (1+2) - 3 = 0. AUC = 0/4 = 0.0.

  - scores=[1,2,3,4], labels=[0,1,0,1]:
      Hit items: score=2 (rank 2), score=4 (rank 4). R1=6.
      U1 = 6 - 2*3/2 = 6 - 3 = 3. AUC = 3/4 = 0.75.

  - scores=[1,1,2,2], labels=[0,1,0,1] (ties):
      Tied group at 1 → avg rank (1+2)/2 = 1.5 each.
      Tied group at 2 → avg rank (3+4)/2 = 3.5 each.
      Item layout: idx0→score1/label0, idx1→score1/label1, idx2→score2/label0, idx3→score2/label1.
      R1 = rank[1] + rank[3] = 1.5 + 3.5 = 5.
      U1 = 5 - 2*3/2 = 5 - 3 = 2. AUC = 2/(2*2) = 0.5.
"""

import math
import pytest

from eval.backtest.metrics import (
    auc,
    hit_rate_at_threshold,
    mean_std,
    point_biserial,
)


# ---------------------------------------------------------------------------
# auc
# ---------------------------------------------------------------------------


class TestAuc:
    def test_perfect_separation(self):
        """All hits score above all flops → AUC == 1.0."""
        assert auc([1, 2, 3, 4], [0, 0, 1, 1]) == pytest.approx(1.0)

    def test_reversed_separation(self):
        """All hits score below all flops → AUC == 0.0."""
        assert auc([1, 2, 3, 4], [1, 1, 0, 0]) == pytest.approx(0.0)

    def test_interleaved_fixture(self):
        """Interleaved fixture; hand-computed AUC = 0.75."""
        assert auc([1, 2, 3, 4], [0, 1, 0, 1]) == pytest.approx(0.75)

    def test_tie_handling(self):
        """Tied scores use averaged ranks; hand-computed AUC = 0.5."""
        assert auc([1, 1, 2, 2], [0, 1, 0, 1]) == pytest.approx(0.5)

    def test_single_class_all_hits_returns_half(self):
        """Single class (all hits) → 0.5 with no crash."""
        assert auc([1.0, 2.0, 3.0], [1, 1, 1]) == pytest.approx(0.5)

    def test_single_class_all_flops_returns_half(self):
        """Single class (all flops) → 0.5 with no crash."""
        assert auc([0.5, 1.5], [0, 0]) == pytest.approx(0.5)

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            auc([1, 2, 3], [0, 1])

    def test_random_three_pairs(self):
        """
        scores=[2,1,3], labels=[1,0,1].
        Sorted: 1→rank1(label0), 2→rank2(label1), 3→rank3(label1).
        R1 = 2+3 = 5. U1 = 5 - 2*3/2 = 2. AUC = 2/(2*1) = 1.0.
        """
        assert auc([2, 1, 3], [1, 0, 1]) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# point_biserial
# ---------------------------------------------------------------------------


class TestPointBiserial:
    def test_positive_when_hits_score_higher(self):
        """r_pb > 0 when hits have higher scores than flops."""
        r = point_biserial([1, 2, 3, 4], [0, 0, 1, 1])
        assert r > 0.0

    def test_negative_when_hits_score_lower(self):
        """r_pb < 0 when hits have lower scores than flops."""
        r = point_biserial([1, 2, 3, 4], [1, 1, 0, 0])
        assert r < 0.0

    def test_zero_when_no_difference(self):
        """r_pb == 0 when groups have identical means."""
        # hits at 1,4 (mean 2.5) flops at 2,3 (mean 2.5)
        r = point_biserial([1, 2, 3, 4], [1, 0, 0, 1])
        assert r == pytest.approx(0.0, abs=1e-10)

    def test_known_value(self):
        """
        scores=[1,2,3,4], labels=[0,0,1,1].
        M1 = (3+4)/2 = 3.5, M0 = (1+2)/2 = 1.5.
        mean_all = 2.5, var = ((1.5^2 + 0.5^2 + 0.5^2 + 1.5^2)/4) = 5/4=1.25, s=sqrt(1.25).
        r_pb = (3.5-1.5)/sqrt(1.25) * sqrt(2*2/16) = 2/sqrt(1.25) * sqrt(0.25)
             = 2/sqrt(1.25) * 0.5 = 1/sqrt(1.25) ≈ 0.8944.
        """
        expected = 1.0 / math.sqrt(1.25)
        assert point_biserial([1, 2, 3, 4], [0, 0, 1, 1]) == pytest.approx(expected)

    def test_all_same_scores_returns_zero(self):
        assert point_biserial([5, 5, 5, 5], [0, 1, 0, 1]) == pytest.approx(0.0)

    def test_single_class_returns_zero(self):
        assert point_biserial([1, 2, 3], [1, 1, 1]) == pytest.approx(0.0)

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            point_biserial([1, 2], [0])


# ---------------------------------------------------------------------------
# hit_rate_at_threshold
# ---------------------------------------------------------------------------


class TestHitRateAtThreshold:
    def test_all_above_threshold_all_hits(self):
        assert hit_rate_at_threshold([3, 4, 5], [1, 1, 1], threshold=3.0) == pytest.approx(1.0)

    def test_mixed_above_threshold(self):
        # scores >= 3: indices 2,3 with labels 0,1 → 1 hit out of 2 → 0.5
        assert hit_rate_at_threshold([1, 2, 3, 4], [1, 0, 0, 1], threshold=3.0) == pytest.approx(0.5)

    def test_no_case_above_threshold_returns_zero(self):
        assert hit_rate_at_threshold([1, 2, 3], [1, 1, 1], threshold=10.0) == pytest.approx(0.0)

    def test_boundary_inclusive(self):
        # threshold == score value: score=3 should be included
        assert hit_rate_at_threshold([3], [1], threshold=3.0) == pytest.approx(1.0)

    def test_all_hits_below_threshold(self):
        # above threshold: only flop
        assert hit_rate_at_threshold([1, 2, 5], [1, 1, 0], threshold=4.0) == pytest.approx(0.0)

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            hit_rate_at_threshold([1, 2], [0], threshold=1.0)


# ---------------------------------------------------------------------------
# mean_std
# ---------------------------------------------------------------------------


class TestMeanStd:
    def test_known_values(self):
        """[1,2,3,4,5]: mean=3, population std=sqrt(2)."""
        m, s = mean_std([1.0, 2.0, 3.0, 4.0, 5.0])
        assert m == pytest.approx(3.0)
        assert s == pytest.approx(math.sqrt(2.0))

    def test_single_value(self):
        m, s = mean_std([7.0])
        assert m == pytest.approx(7.0)
        assert s == pytest.approx(0.0)

    def test_uniform_values_zero_std(self):
        m, s = mean_std([4.0, 4.0, 4.0])
        assert m == pytest.approx(4.0)
        assert s == pytest.approx(0.0)

    def test_two_values(self):
        """[0, 10]: mean=5, pop std=5."""
        m, s = mean_std([0.0, 10.0])
        assert m == pytest.approx(5.0)
        assert s == pytest.approx(5.0)

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            mean_std([])
