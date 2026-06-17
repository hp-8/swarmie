"""
text_baseline.py — Direct text→outcome baseline for the PMF Readiness Index backtest.

No LLM. Trains classical ML models on the decontaminated directory text of EVERY
labeled tier-1 case (~1k companies, not the 200-case swarm sample) and reports
5-fold cross-validated AUC.

What this is
------------
A *baseline and honesty check*, not the index. The PMF index dims are swarm
outputs; this model reads the pitch text directly. Its AUC answers:
"how much outcome signal is in the pitch text alone?"

  - If swarm-index AUC ≤ text-baseline AUC, the swarm adds nothing — report that.
  - Top model coefficients double as a contamination detector: words like
    "acquired" or "wound" ranking high means decontamination missed something.

Models
------
  tfidf_lr    TF-IDF (word 1-2 grams) → LogisticRegression. Interpretable.
  tfidf_char  TF-IDF (char 3-5 grams) → LogisticRegression. Style/orthography.
  svd_gbm     TF-IDF → TruncatedSVD(256) → HistGradientBoosting. Nonlinear.
  embed_lr    MiniLM sentence embeddings → LogisticRegression. Semantic (DL).
              Only runs if sentence-transformers is installed; skipped otherwise.

All vectorizers are fit inside each CV fold (sklearn Pipeline) — no leakage.
The MiniLM encoder is frozen (pretrained, never sees the labels), so embeddings
are precomputed once and only the LR is cross-validated.

Usage
-----
  .venv/bin/python -m eval.backtest.text_baseline \
      --out eval/backtest/data/text_baseline.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

from eval.backtest.corpus import load_tier1
from eval.backtest.decontaminate import decontaminate

logger = logging.getLogger("swarmie.eval.backtest.text_baseline")

SEED = 42
N_FOLDS = 5


def load_all_clean() -> list[dict]:
    """Every labeled tier-1 case, decontaminated, empty texts dropped."""
    cases: list[dict] = []
    dropped = 0
    for case in load_tier1():
        text = decontaminate(
            {
                "name": case.get("name", ""),
                "former_names": case.get("former_names", []),
                "long_description": case.get("raw_text", ""),
                "one_liner": "",
            }
        )
        if not text:
            dropped += 1
            continue
        cases.append({"id": case["id"], "text": text, "label": case["label"],
                      "batch": case.get("batch")})
    logger.info("load_all_clean: %d cases (%d dropped empty)", len(cases), dropped)
    return cases


def build_models() -> dict[str, Pipeline]:
    return {
        "tfidf_lr": Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2), min_df=3, max_features=20000,
                sublinear_tf=True, strip_accents="unicode",
            )),
            ("lr", LogisticRegression(
                C=1.0, max_iter=2000, class_weight="balanced",
            )),
        ]),
        "tfidf_char": Pipeline([
            ("tfidf", TfidfVectorizer(
                analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                max_features=30000, sublinear_tf=True,
            )),
            ("lr", LogisticRegression(
                C=1.0, max_iter=2000, class_weight="balanced",
            )),
        ]),
        "svd_gbm": Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2), min_df=3, max_features=20000,
                sublinear_tf=True, strip_accents="unicode",
            )),
            ("svd", TruncatedSVD(n_components=256, random_state=SEED)),
            ("gbm", HistGradientBoostingClassifier(random_state=SEED)),
        ]),
    }


def cv_auc(model, X, labels: np.ndarray) -> tuple[float, float]:
    cv = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    scores = cross_val_score(model, X, labels, cv=cv, scoring="roc_auc", n_jobs=1)
    return float(scores.mean()), float(scores.std())


def embed_cv_auc(texts: list[str], labels: np.ndarray) -> tuple[float, float] | None:
    """MiniLM embeddings → LogisticRegression CV AUC, or None if deps missing.

    The encoder is pretrained and frozen — it never sees the labels — so
    encoding the full corpus once before the CV split is leak-free.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.info("embed_lr: sentence-transformers not installed — skipping")
        return None

    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = encoder.encode(texts, batch_size=64, show_progress_bar=False,
                                normalize_embeddings=True)
    lr = LogisticRegression(C=1.0, max_iter=2000, class_weight="balanced")
    return cv_auc(lr, embeddings, labels)


def top_coefficients(texts: list[str], labels: np.ndarray, k: int = 25) -> dict:
    """Fit tfidf_lr on the full corpus and return top ±k word features.

    Leak detector: outcome words ranking high → decontamination gap.
    """
    pipe = build_models()["tfidf_lr"]
    pipe.fit(texts, labels)
    vocab = np.array(pipe.named_steps["tfidf"].get_feature_names_out())
    coef = pipe.named_steps["lr"].coef_[0]
    order = np.argsort(coef)
    return {
        "predicts_hit": [
            {"term": vocab[i], "coef": round(float(coef[i]), 4)}
            for i in order[::-1][:k]
        ],
        "predicts_flop": [
            {"term": vocab[i], "coef": round(float(coef[i]), 4)}
            for i in order[:k]
        ],
    }


def run(out_path: Path) -> dict:
    cases = load_all_clean()
    texts = [c["text"] for c in cases]
    labels = np.array([c["label"] for c in cases])

    results: dict = {
        "n": len(cases),
        "hits": int(labels.sum()),
        "flops": int((labels == 0).sum()),
        "n_folds": N_FOLDS,
        "seed": SEED,
        "models": {},
    }

    for name, model in build_models().items():
        mean, std = cv_auc(model, texts, labels)
        results["models"][name] = {"cv_auc_mean": round(mean, 4),
                                   "cv_auc_std": round(std, 4)}
        logger.info("%-10s CV AUC = %.4f ± %.4f", name, mean, std)

    embed_result = embed_cv_auc(texts, labels)
    if embed_result is not None:
        mean, std = embed_result
        results["models"]["embed_lr"] = {"cv_auc_mean": round(mean, 4),
                                         "cv_auc_std": round(std, 4)}
        logger.info("%-10s CV AUC = %.4f ± %.4f", "embed_lr", mean, std)

    results["top_features"] = top_coefficients(texts, labels)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    logger.info("wrote %s", out_path)
    return results


def _main(argv: list[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        stream=sys.stderr,
    )
    p = argparse.ArgumentParser(
        description="Text-only outcome baseline (no LLM) over all tier-1 cases.",
        prog="python -m eval.backtest.text_baseline",
    )
    p.add_argument(
        "--out", type=str, default="eval/backtest/data/text_baseline.json",
        help="Output JSON path. Default: eval/backtest/data/text_baseline.json.",
    )
    args = p.parse_args(argv)

    results = run(Path(args.out))

    print(json.dumps({k: v for k, v in results.items() if k != "top_features"},
                     indent=2))
    print("\nTop hit-predicting terms:")
    for f in results["top_features"]["predicts_hit"][:15]:
        print(f"  {f['coef']:+.3f}  {f['term']}")
    print("\nTop flop-predicting terms:")
    for f in results["top_features"]["predicts_flop"][:15]:
        print(f"  {f['coef']:+.3f}  {f['term']}")


if __name__ == "__main__":
    _main()
