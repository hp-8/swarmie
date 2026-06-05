"""
Backtest metrics for the PMF Readiness Index calibration harness.

All functions are pure, stdlib-only (no numpy/sklearn/scipy).

AUC algorithm: Mann-Whitney U via rank method.
  1. Assign ranks to all scores (1-based, ties get averaged ranks).
  2. Sum the ranks of the positive class (hits, label=1) → R1.
  3. U1 = R1 - n1*(n1+1)/2, where n1 = number of hits.
  4. AUC = U1 / (n1 * n0), where n0 = number of flops.

  Edge: if only one class is present, return 0.5 (convention: random classifier).
  The caller should treat this value as "undefined / degenerate" and check
  that both classes are represented before citing the result.
"""

from __future__ import annotations


def _ranks(values: list[float]) -> list[float]:
    """Return averaged ranks (1-based) for a list of floats, handling ties."""
    n = len(values)
    # pair (value, original_index), sort by value
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks: list[float] = [0.0] * n
    i = 0
    while i < n:
        j = i
        # find run of equal values
        while j < n and indexed[j][1] == indexed[i][1]:
            j += 1
        # average rank for the tie group (1-based: positions i+1 … j)
        avg = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg
        i = j
    return ranks


def auc(scores: list[float], labels: list[int]) -> float:
    """
    ROC AUC via Mann-Whitney U / rank method.

    Parameters
    ----------
    scores : list of float
        Predicted scores (higher = more likely to be a hit).
    labels : list of int
        Ground-truth binary labels: 1 = hit, 0 = flop.

    Returns
    -------
    float
        AUC in [0, 1].  Returns 0.5 if only one class is present in *labels*
        (degenerate / undefined; treat as random-classifier baseline, not as
        a calibration claim).
    """
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have the same length")

    n1 = sum(1 for lbl in labels if lbl == 1)
    n0 = sum(1 for lbl in labels if lbl == 0)

    if n1 == 0 or n0 == 0:
        # Single-class input: AUC is undefined; return 0.5 by convention.
        return 0.5

    r = _ranks(scores)
    r1 = sum(r[i] for i, lbl in enumerate(labels) if lbl == 1)
    u1 = r1 - n1 * (n1 + 1) / 2.0
    return u1 / (n1 * n0)


def point_biserial(scores: list[float], labels: list[int]) -> float:
    """
    Point-biserial correlation between a continuous score and a binary label.

    r_pb = (M1 - M0) / s_total * sqrt(n1 * n0 / n^2)

    where M1, M0 are group means, s_total is the population std of all scores,
    and n1, n0 are group sizes.

    Returns 0.0 if the total std is zero (all scores identical) or if one
    class is absent.
    """
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have the same length")

    n = len(scores)
    n1 = sum(1 for lbl in labels if lbl == 1)
    n0 = n - n1

    if n1 == 0 or n0 == 0:
        return 0.0

    mean_all = sum(scores) / n
    var_all = sum((s - mean_all) ** 2 for s in scores) / n
    s_total = var_all ** 0.5

    if s_total == 0.0:
        return 0.0

    scores1 = [scores[i] for i, lbl in enumerate(labels) if lbl == 1]
    scores0 = [scores[i] for i, lbl in enumerate(labels) if lbl == 0]

    m1 = sum(scores1) / n1
    m0 = sum(scores0) / n0

    return (m1 - m0) / s_total * (n1 * n0 / n ** 2) ** 0.5


def hit_rate_at_threshold(
    scores: list[float], labels: list[int], threshold: float
) -> float:
    """
    Precision at a score threshold (hit-rate@threshold).

    Of the cases with score >= threshold, returns the fraction that are hits
    (label == 1).  Returns 0.0 if no case meets the threshold.
    """
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have the same length")

    above = [(scores[i], labels[i]) for i in range(len(scores)) if scores[i] >= threshold]
    if not above:
        return 0.0

    hits_above = sum(1 for _, lbl in above if lbl == 1)
    return hits_above / len(above)


def mean_std(values: list[float]) -> tuple[float, float]:
    """
    Return (mean, population std) for a list of floats.

    Population std (divides by N, not N-1) is used for aggregating an index
    across N repeat runs where the full population of runs is observed.

    Raises ValueError if *values* is empty.
    """
    if not values:
        raise ValueError("values must not be empty")

    n = len(values)
    m = sum(values) / n
    variance = sum((v - m) ** 2 for v in values) / n
    return m, variance ** 0.5
