"""
Weight calibration for the Swarmie PMF Readiness Index.

Fits a StandardScaler + LogisticRegression over the 5 numeric dimensions
produced by the backtest runner.  Reports CV AUC (out-of-fold, never train AUC),
then re-fits on all data to export the final weights.

Usage (CLI):
    python -m eval.backtest.calibrate \\
        --features eval/backtest/data/features_tier1.json \\
        --out app/services/swarm/index_weights_v1.json

sklearn and numpy are eval-only dependencies (see eval/requirements-eval.txt).
They are never imported at runtime by the production app.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

# numpy + sklearn are eval-only deps (eval/requirements-eval.txt). Imported
# lazily inside functions so this module imports cleanly in CI (uv sync), where
# those deps are absent — the production app never imports this module.
# TYPE_CHECKING import resolves the `np.ndarray` annotations for linters only.
if TYPE_CHECKING:
    import numpy as np

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

DIM_ORDER: list[str] = [
    "engagement_rate",
    "sentiment_score",
    "segment_fit",
    "objection_severity",
    "silence_penalty",
]

_DEFAULT_OUT = "app/services/swarm/index_weights_v1.json"

# The WARNING band: if CV AUC falls inside this range, separation is not
# demonstrated and the index should be labelled "uncalibrated" downstream.
_WARN_LOW = 0.45
_WARN_HIGH = 0.55


# ---------------------------------------------------------------------------
# load_features
# ---------------------------------------------------------------------------


def load_features(path: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Load a features JSON file produced by the backtest runner.

    Each row must have:
        id, label (0/1), run_idx,
        engagement_rate, sentiment_score, segment_fit,
        objection_severity, silence_penalty

    Returns:
        X   — float64 array of shape (n, 5) in DIM_ORDER column order
        y   — int array of shape (n,)  (0 = flop, 1 = hit)
        ids — list[str] of case ids
    """
    import numpy as np

    raw: list[dict[str, Any]] = json.loads(Path(path).read_text())

    X_rows: list[list[float]] = []
    y_vals: list[int] = []
    ids: list[str] = []

    for row in raw:
        X_rows.append([float(row[dim]) for dim in DIM_ORDER])
        y_vals.append(int(row["label"]))
        ids.append(str(row["id"]))

    X = np.array(X_rows, dtype=np.float64)
    y = np.array(y_vals, dtype=np.int64)
    return X, y, ids


# ---------------------------------------------------------------------------
# calibrate
# ---------------------------------------------------------------------------


def calibrate(
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int = 5,
    seed: int = 42,
) -> dict[str, Any]:
    """
    Fit StandardScaler + LogisticRegression and evaluate with k-fold CV.

    CV AUC is computed via out-of-fold predicted probabilities
    (cross_val_predict with method='predict_proba') so it genuinely reflects
    generalisation, not train-set fit.

    After CV scoring the scaler + model are re-fit on ALL data to produce
    the final exportable weights.

    Parameters
    ----------
    X        : (n, 5) feature matrix in DIM_ORDER column order
    y        : (n,) binary labels — 1 = hit, 0 = flop
    n_splits : number of CV folds (default 5)
    seed     : random seed for reproducibility

    Returns
    -------
    dict with keys:
        index_version, dim_order, coef, intercept,
        scaler_mean, scaler_scale, cv_auc,
        n, n_hits, n_flops, generated_at
    """
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import cross_val_predict
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    model = LogisticRegression(
        max_iter=1000,
        random_state=seed,
        solver="lbfgs",
    )

    # --- CV AUC (out-of-fold) ---
    from sklearn.model_selection import StratifiedKFold
    from sklearn.pipeline import Pipeline

    pipeline = Pipeline([("scaler", StandardScaler()), ("lr", LogisticRegression(
        max_iter=1000,
        random_state=seed,
        solver="lbfgs",
    ))])

    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)

    oof_proba = cross_val_predict(
        pipeline,
        X,
        y,
        cv=cv,
        method="predict_proba",
    )
    oof_scores = oof_proba[:, 1]
    cv_auc: float = float(roc_auc_score(y, oof_scores))

    # --- Final fit on all data ---
    X_scaled = scaler.fit_transform(X)
    model.fit(X_scaled, y)

    coef: list[float] = [float(c) for c in model.coef_[0]]
    intercept: float = float(model.intercept_[0])
    scaler_mean: list[float] = [float(m) for m in scaler.mean_]
    scaler_scale: list[float] = [float(s) for s in scaler.scale_]

    n = int(len(y))
    n_hits = int(np.sum(y == 1))
    n_flops = int(np.sum(y == 0))

    return {
        "index_version": "1.0",
        "dim_order": DIM_ORDER,
        "coef": coef,
        "intercept": intercept,
        "scaler_mean": scaler_mean,
        "scaler_scale": scaler_scale,
        "cv_auc": cv_auc,
        "n": n,
        "n_hits": n_hits,
        "n_flops": n_flops,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# write_weights
# ---------------------------------------------------------------------------


def write_weights(result: dict[str, Any], path: str = _DEFAULT_OUT) -> None:
    """
    Serialise the calibrate() result to a JSON file.

    All values are plain Python types (list[float], float, str, int) so
    stdlib json.dumps is sufficient — no numpy encoder needed.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Calibrate PMF Readiness Index weights via logistic regression."
    )
    parser.add_argument(
        "--features",
        required=True,
        help="Path to features JSON produced by the backtest runner.",
    )
    parser.add_argument(
        "--out",
        default=_DEFAULT_OUT,
        help=f"Output path for index_weights JSON (default: {_DEFAULT_OUT})",
    )
    args = parser.parse_args()

    print(f"Loading features from: {args.features}")
    X, y, ids = load_features(args.features)
    print(f"  Loaded {len(ids)} cases  ({int(y.sum())} hits / {int((y==0).sum())} flops)")

    print("Calibrating (5-fold CV) …")
    result = calibrate(X, y, n_splits=5, seed=42)

    cv_auc = result["cv_auc"]
    print()
    print("=" * 60)
    print(f"  CV AUC (out-of-fold): {cv_auc:.4f}")
    print("=" * 60)

    if _WARN_LOW <= cv_auc <= _WARN_HIGH:
        print()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("  WARNING: CV AUC is within [0.45, 0.55].")
        print("  Separation is NOT demonstrated.")
        print("  The index will be labelled UNCALIBRATED downstream.")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print()

    write_weights(result, args.out)
    print(f"Weights written to: {args.out}")


if __name__ == "__main__":  # pragma: no cover
    _main()
