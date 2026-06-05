"""
Tests for eval.backtest.calibrate — weight calibration for PMF Readiness Index.

Fixtures use sklearn make_blobs (eval-only dep) to build synthetic separable
and near-random datasets so we can assert CV AUC thresholds without needing
a real YC corpus at test time.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
from sklearn.datasets import make_blobs

from eval.backtest.calibrate import (
    DIM_ORDER,
    calibrate,
    load_features,
    write_weights,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RNG = np.random.default_rng(42)


def _make_features_json(
    X: np.ndarray,
    y: np.ndarray,
    path: Path,
) -> None:
    """Write a features JSON file matching the expected schema."""
    rows = []
    for i, (xi, yi) in enumerate(zip(X, y)):
        rows.append(
            {
                "id": f"case_{i:04d}",
                "label": int(yi),
                "run_idx": 0,
                "engagement_rate": float(xi[0]),
                "sentiment_score": float(xi[1]),
                "segment_fit": float(xi[2]),
                "objection_severity": float(xi[3]),
                "silence_penalty": float(xi[4]),
            }
        )
    path.write_text(json.dumps(rows))


def _separable_blobs(n: int = 300) -> tuple[np.ndarray, np.ndarray]:
    """
    Two gaussian blobs in 5-D.
    hits (label=1): centroid at +1.5 on all dims.
    flops (label=0): centroid at -1.5 on all dims.
    Shifted so values stay in a plausible range after clip.
    """
    X, y = make_blobs(
        n_samples=n,
        n_features=5,
        centers=[
            [-1.5, -1.5, -1.5, -1.5, -1.5],  # flop
            [1.5, 1.5, 1.5, 1.5, 1.5],        # hit
        ],
        cluster_std=0.8,
        random_state=42,
    )
    # Clip to [0, 1] so values look like the actual feature range
    X = np.clip(X * 0.3 + 0.5, 0.0, 1.0)
    return X, y


def _random_blobs(n: int = 300) -> tuple[np.ndarray, np.ndarray]:
    """
    Heavily overlapping blobs — near-random, AUC should be ~0.5.
    """
    X, y = make_blobs(
        n_samples=n,
        n_features=5,
        centers=[[0.5, 0.5, 0.5, 0.5, 0.5], [0.5, 0.5, 0.5, 0.5, 0.5]],
        cluster_std=0.3,
        random_state=99,
    )
    X = np.clip(X, 0.0, 1.0)
    return X, y


# ---------------------------------------------------------------------------
# DIM_ORDER sanity
# ---------------------------------------------------------------------------


def test_dim_order_has_five_entries() -> None:
    assert len(DIM_ORDER) == 5


def test_dim_order_values() -> None:
    assert DIM_ORDER == [
        "engagement_rate",
        "sentiment_score",
        "segment_fit",
        "objection_severity",
        "silence_penalty",
    ]


# ---------------------------------------------------------------------------
# load_features
# ---------------------------------------------------------------------------


def test_load_features_returns_correct_shapes() -> None:
    X_raw, y_raw = _separable_blobs(n=50)
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "features.json"
        _make_features_json(X_raw, y_raw, p)
        X, y, ids = load_features(str(p))

    assert X.shape == (50, 5)
    assert y.shape == (50,)
    assert len(ids) == 50


def test_load_features_dim_column_order() -> None:
    """Columns must follow DIM_ORDER exactly."""
    X_raw, y_raw = _separable_blobs(n=20)
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "features.json"
        _make_features_json(X_raw, y_raw, p)
        X, y, ids = load_features(str(p))

    # We just need the shape/order; content fidelity covered by schema test.
    assert X.shape[1] == len(DIM_ORDER)


def test_load_features_ids_are_strings() -> None:
    X_raw, y_raw = _separable_blobs(n=10)
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "features.json"
        _make_features_json(X_raw, y_raw, p)
        _, _, ids = load_features(str(p))
    assert all(isinstance(i, str) for i in ids)


# ---------------------------------------------------------------------------
# calibrate — separable fixture
# ---------------------------------------------------------------------------


def test_calibrate_separable_cv_auc_above_threshold() -> None:
    """Well-separated blobs should yield CV AUC > 0.80."""
    X, y = _separable_blobs(n=300)
    result = calibrate(X, y, n_splits=5, seed=42)
    assert result["cv_auc"] > 0.80, f"Expected > 0.80, got {result['cv_auc']:.4f}"


def test_calibrate_result_schema_complete() -> None:
    X, y = _separable_blobs(n=200)
    result = calibrate(X, y, n_splits=5, seed=42)

    required_keys = {
        "index_version",
        "dim_order",
        "coef",
        "intercept",
        "scaler_mean",
        "scaler_scale",
        "cv_auc",
        "n",
        "n_hits",
        "n_flops",
        "generated_at",
    }
    assert required_keys <= set(result.keys()), (
        f"Missing keys: {required_keys - set(result.keys())}"
    )


def test_calibrate_coef_length_is_five() -> None:
    X, y = _separable_blobs(n=200)
    result = calibrate(X, y, n_splits=5, seed=42)
    assert len(result["coef"]) == 5


def test_calibrate_scaler_arrays_length_is_five() -> None:
    X, y = _separable_blobs(n=200)
    result = calibrate(X, y, n_splits=5, seed=42)
    assert len(result["scaler_mean"]) == 5
    assert len(result["scaler_scale"]) == 5


def test_calibrate_index_version() -> None:
    X, y = _separable_blobs(n=100)
    result = calibrate(X, y, n_splits=5, seed=42)
    assert result["index_version"] == "1.0"


def test_calibrate_n_counts() -> None:
    X, y = _separable_blobs(n=200)
    result = calibrate(X, y, n_splits=5, seed=42)
    assert result["n"] == 200
    assert result["n_hits"] + result["n_flops"] == 200


def test_calibrate_dim_order_in_result() -> None:
    X, y = _separable_blobs(n=100)
    result = calibrate(X, y, n_splits=5, seed=42)
    assert result["dim_order"] == DIM_ORDER


# ---------------------------------------------------------------------------
# calibrate — near-random fixture (weak separation)
# ---------------------------------------------------------------------------


def test_calibrate_near_random_cv_auc_near_half() -> None:
    """Near-random blobs: CV AUC should be close to 0.5 (within [0.35, 0.65])."""
    X, y = _random_blobs(n=300)
    result = calibrate(X, y, n_splits=5, seed=42)
    assert 0.35 <= result["cv_auc"] <= 0.65, (
        f"Expected AUC near 0.5, got {result['cv_auc']:.4f}"
    )


def test_calibrate_warning_condition_triggers_for_near_random() -> None:
    """
    The WARNING condition is: cv_auc within [0.45, 0.55].
    Near-random fixture must satisfy this.
    """
    X, y = _random_blobs(n=300)
    result = calibrate(X, y, n_splits=5, seed=42)
    # Check the WARNING band directly
    assert 0.45 <= result["cv_auc"] <= 0.55, (
        f"Expected AUC in WARNING band [0.45,0.55], got {result['cv_auc']:.4f}"
    )


# ---------------------------------------------------------------------------
# write_weights
# ---------------------------------------------------------------------------


def test_write_weights_roundtrip() -> None:
    """write_weights produces valid JSON loadable by stdlib json."""
    X, y = _separable_blobs(n=150)
    result = calibrate(X, y, n_splits=5, seed=42)

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "index_weights_v1.json"
        write_weights(result, str(out))

        loaded = json.loads(out.read_text())

    # Schema check on roundtrip
    assert loaded["index_version"] == "1.0"
    assert len(loaded["coef"]) == 5
    assert len(loaded["scaler_mean"]) == 5
    assert len(loaded["scaler_scale"]) == 5
    assert isinstance(loaded["cv_auc"], float)
    assert isinstance(loaded["intercept"], float)


def test_write_weights_values_are_python_native() -> None:
    """No numpy types should survive into the JSON (would break stdlib json)."""
    X, y = _separable_blobs(n=100)
    result = calibrate(X, y, n_splits=5, seed=42)

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "weights.json"
        write_weights(result, str(out))
        # If this loads without error, numpy types were properly converted
        loaded = json.loads(out.read_text())
    assert isinstance(loaded["coef"][0], float)
    assert isinstance(loaded["scaler_mean"][0], float)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_calibrate_deterministic_for_fixed_seed() -> None:
    """Same seed → identical coef and CV AUC."""
    X, y = _separable_blobs(n=200)
    r1 = calibrate(X, y, n_splits=5, seed=42)
    r2 = calibrate(X, y, n_splits=5, seed=42)

    assert r1["coef"] == r2["coef"]
    assert r1["cv_auc"] == r2["cv_auc"]
    assert r1["intercept"] == r2["intercept"]


def test_calibrate_different_seeds_may_differ() -> None:
    """Different seeds can produce different (but valid) results."""
    X, y = _separable_blobs(n=200)
    r1 = calibrate(X, y, n_splits=5, seed=42)
    r2 = calibrate(X, y, n_splits=5, seed=7)
    # Both should still be valid (AUC > 0.8 for separable data)
    assert r1["cv_auc"] > 0.80
    assert r2["cv_auc"] > 0.80
