"""
runner.py — Feature-extraction runner for the PMF Readiness Index backtest.

Responsibilities
----------------
1. extract_dims(report)       Pure function: 6 index dimensions from a RoastReport dict.
2. run_case(pitch_text, ...)  Run one pitch through an injectable report_fn, extract dims.
3. build_sample(...)          Load tier-1 corpus, decontaminate, balanced random sample.
4. run(sample, repeats, ...)  Cross-product sample × repeats → feature rows.
5. CLI                        python -m eval.backtest.runner --help

Cost guard
----------
The CLI default report_fn runs the real swarm pipeline (parse → archetypes → reactions →
report). This is expensive; use ``--mode synth`` (or inject a canned report_fn) for fast
iteration over tier-1. Only spend live-LLM budget on tier-2.

The real pipeline entry point is:
  backend/app/api/roast._run_pipeline()

We replicate the pipeline's stages inline rather than importing the Flask route so the
runner can operate without a running server. The four stages are:
  1. PitchParser.parse(pitch_text)             → ParsedPitch
  2. ArchetypeGenerator.generate(pitch)        → list[Archetype]
  3. SwarmRunner.run(pitch, archetypes, ...)   → list[AgentReaction]   (async)
  4. RoastReporter.report(pitch, reactions)    → RoastReport

We then call RoastReport.to_dict() and pass the result to extract_dims.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import sys
from pathlib import Path
from typing import Any, Callable

# Wave-A modules: corpus, decontaminate, roast_reporter helpers.
from eval.backtest.corpus import load_tier1
from eval.backtest.decontaminate import decontaminate
from app.services.swarm.roast_reporter import (
    compute_objection_severity,
    compute_silence_penalty,
)

logger = logging.getLogger("swarmie.eval.backtest.runner")

# ---------------------------------------------------------------------------
# 1. extract_dims — pure, no LLM
# ---------------------------------------------------------------------------

def extract_dims(report: dict) -> dict:
    """Extract the 6 PMF index dimensions from a RoastReport dict.

    Args:
        report: dict as returned by RoastReport.to_dict(). Required keys:
            sentiment_split  {positive, neutral, negative}  (percentages 0-100)
            action_split     {post, comment, upvote, ignore}  (int counts)
            icp_fit          {seg: {count, avg_sentiment, ...}}
            top_objections   [{category, count, ...}]
            silent_share_pct float (0-100)

    Returns:
        dict with keys:
            engagement_rate    float  0..1   higher = better
            sentiment_score    float -1..1   higher = better
            segment_fit        float  0..1   higher = better
            objection_severity float  0..1   higher = worse
            silence_penalty    float  0..1   higher = worse
    """
    # --- action_split --------------------------------------------------------
    action_split: dict[str, Any] = report.get("action_split") or {}
    comment = int(action_split.get("comment", 0))
    post    = int(action_split.get("post", 0))
    upvote  = int(action_split.get("upvote", 0))
    ignore  = int(action_split.get("ignore", 0))
    total_actions = max(comment + post + upvote + ignore, 1)  # guard ≥ 1
    engagement_rate = (comment + post + 0.5 * upvote) / total_actions

    # --- sentiment_split -----------------------------------------------------
    sentiment_split: dict[str, Any] = report.get("sentiment_split") or {}
    positive = float(sentiment_split.get("positive", 0.0))
    negative = float(sentiment_split.get("negative", 0.0))
    sentiment_score = (positive - negative) / 100.0  # -1..1

    # --- icp_fit (size-weighted segment fit) ---------------------------------
    icp_fit: dict[str, Any] = report.get("icp_fit") or {}
    total_seg_agents = sum(
        int(v.get("count", 0)) for v in icp_fit.values()
    ) if icp_fit else 0
    total_seg_agents = max(total_seg_agents, 1)  # guard
    positive_seg_agents = sum(
        int(v.get("count", 0))
        for v in icp_fit.values()
        if float(v.get("avg_sentiment", 0.0)) > 0.1
    )
    segment_fit = positive_seg_agents / total_seg_agents

    # --- objection_severity (delegate to roast_reporter) --------------------
    top_objections: list[dict] = report.get("top_objections") or []
    objection_severity = compute_objection_severity(top_objections)

    # --- silence_penalty (delegate to roast_reporter) -----------------------
    silent_share_pct: float = float(report.get("silent_share_pct", 0.0))
    silence_penalty = compute_silence_penalty(silent_share_pct)

    return {
        "engagement_rate":    round(engagement_rate, 6),
        "sentiment_score":    round(sentiment_score, 6),
        "segment_fit":        round(segment_fit, 6),
        "objection_severity": objection_severity,  # already rounded in helper
        "silence_penalty":    silence_penalty,     # already rounded in helper
    }


# ---------------------------------------------------------------------------
# 2. run_case — injectable report_fn
# ---------------------------------------------------------------------------

def run_case(pitch_text: str, *, report_fn: Callable[[str], dict]) -> dict:
    """Run one pitch through report_fn and extract dimensions.

    Args:
        pitch_text:  The (decontaminated) pitch text to evaluate.
        report_fn:   Callable(pitch_text: str) -> report_dict.
                     Called synchronously. For the real async pipeline, wrap
                     with asyncio.run(...) inside the callable.

    Returns:
        dict of 6 dimensions from extract_dims.
    """
    report = report_fn(pitch_text)
    return extract_dims(report)


# ---------------------------------------------------------------------------
# 3. build_sample — deterministic balanced sample from tier-1
# ---------------------------------------------------------------------------

def build_sample(n_per_class: int = 100, seed: int = 42) -> list[dict]:
    """Load tier-1 corpus, decontaminate, balanced-sample n_per_class per class.

    Steps:
      1. load_tier1()         — raw labeled cases
      2. decontaminate()      — strip names / outcome phrases from raw_text
      3. drop empty texts     — log how many dropped
      4. split into hits (label=1) and flops (label=0)
      5. random.sample each class with fixed seed → n_per_class each
      6. Return combined list, each case has 'text' (cleaned) replacing raw_text

    Args:
        n_per_class: How many hits and flops to include (default 100 each).
        seed:        RNG seed for reproducibility (default 42).

    Returns:
        list of dicts: {id, name, former_names, text, label, status, batch}
    """
    rng = random.Random(seed)

    raw_cases = load_tier1()
    cleaned: list[dict] = []
    dropped = 0
    for case in raw_cases:
        # decontaminate() expects a record with long_description/one_liner keys,
        # but load_tier1() stores the already-selected text in raw_text.
        # Reconstruct a compatible record: put raw_text in long_description.
        decontam_record = {
            "name":             case.get("name", ""),
            "former_names":     case.get("former_names", []),
            "long_description": case.get("raw_text", ""),
            "one_liner":        "",
        }
        text = decontaminate(decontam_record)
        if not text:
            dropped += 1
            continue
        cleaned.append({
            "id":           case["id"],
            "name":         case["name"],
            "former_names": case.get("former_names", []),
            "text":         text,
            "label":        case["label"],
            "status":       case.get("status"),
            "batch":        case.get("batch"),
        })

    if dropped:
        logger.info("build_sample: dropped %d cases (empty after decontamination)", dropped)

    hits  = [c for c in cleaned if c["label"] == 1]
    flops = [c for c in cleaned if c["label"] == 0]

    if len(hits) < n_per_class:
        logger.warning(
            "build_sample: only %d hits available (requested %d)", len(hits), n_per_class
        )
    if len(flops) < n_per_class:
        logger.warning(
            "build_sample: only %d flops available (requested %d)", len(flops), n_per_class
        )

    sampled_hits  = rng.sample(hits,  min(n_per_class, len(hits)))
    sampled_flops = rng.sample(flops, min(n_per_class, len(flops)))

    return sampled_hits + sampled_flops


# ---------------------------------------------------------------------------
# 4. run — cross-product sample × repeats
# ---------------------------------------------------------------------------

def run(
    sample: list[dict],
    repeats: int,
    report_fn: Callable[[str], dict],
) -> list[dict]:
    """Run the pipeline over each case in sample, repeats times each.

    Each call to report_fn is wrapped in try/except; failures are logged and
    that (case, run_idx) row is skipped. The batch never aborts.

    Args:
        sample:     List of case dicts (from build_sample or similar).
        repeats:    Number of times to run each case (captures run-variance).
        report_fn:  Callable(pitch_text: str) -> report_dict.

    Returns:
        List of dicts: {id, label, run_idx, engagement_rate, sentiment_score,
                        segment_fit, objection_severity, silence_penalty}
    """
    rows: list[dict] = []
    total = len(sample) * repeats
    done = 0

    for case in sample:
        for run_idx in range(repeats):
            done += 1
            try:
                dims = run_case(case["text"], report_fn=report_fn)
            except Exception as exc:
                logger.warning(
                    "run: skipping case id=%s run=%d — %s: %s",
                    case.get("id"), run_idx, type(exc).__name__, exc,
                )
                continue

            rows.append({
                "id":      case["id"],
                "label":   case["label"],
                "run_idx": run_idx,
                **dims,
            })

            if done % 50 == 0 or done == total:
                logger.info("run: %d/%d complete (%d rows so far)", done, total, len(rows))

    return rows


# ---------------------------------------------------------------------------
# 5. Real pipeline report_fn (default for CLI)
# ---------------------------------------------------------------------------

def _make_real_report_fn(n_agents: int = 30) -> Callable[[str], dict]:
    """Return a synchronous report_fn that drives the full swarm pipeline.

    Pipeline stages (mirrors _run_pipeline in backend/app/api/roast.py):
      PitchParser.parse → ArchetypeGenerator.generate → SwarmRunner.run → RoastReporter.report

    The "validate" swarm spec is used (RoastReporter, PitchParser, etc.).

    LLM config is read from .env (loaded by app.config.Config via os.environ).
    """
    from app.services.swarm.registry import get_swarm
    from app.utils.llm import UsageTracker

    spec = get_swarm("validate")

    def _report_fn(pitch_text: str) -> dict:
        tracker = UsageTracker()

        # Stage 1 — parse pitch
        parser = spec.parser_cls(tracker=tracker)
        pitch = parser.parse(pitch_text)

        # Stage 2 — generate archetypes
        archgen = spec.archgen_cls(tracker=tracker)
        archetypes = archgen.generate(pitch, n_archetypes=spec.n_archetypes)

        # Stage 3 — run swarm (async)
        runner = spec.runner_cls(tracker=tracker)
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            reactions = loop.run_until_complete(
                runner.run(
                    pitch=pitch,
                    archetypes=archetypes,
                    n_agents=n_agents,
                    on_reaction=None,
                    on_thinking=None,
                )
            )
        finally:
            loop.close()

        # Stage 4 — synthesize report
        reporter = spec.reporter_cls(tracker=tracker)
        report = reporter.report(pitch, reactions)

        return report.to_dict()

    return _report_fn


# ---------------------------------------------------------------------------
# 6. CLI entry point
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None):
    import argparse
    p = argparse.ArgumentParser(
        description="Run the PMF Readiness Index feature-extraction backtest.",
        prog="python -m eval.backtest.runner",
    )
    p.add_argument(
        "--sample", type=int, default=200,
        help="Total sample size (n_per_class = sample // 2). Default: 200.",
    )
    p.add_argument(
        "--balanced", action="store_true", default=True,
        help="(default) Balanced classes (n_per_class = sample // 2).",
    )
    p.add_argument(
        "--repeats", type=int, default=1,
        help="Number of pipeline runs per case. Default: 1.",
    )
    p.add_argument(
        "--seed", type=int, default=42,
        help="RNG seed for sample selection. Default: 42.",
    )
    p.add_argument(
        "--out", type=str, default="eval/backtest/data/features_tier1.json",
        help="Output JSON file path. Default: eval/backtest/data/features_tier1.json.",
    )
    p.add_argument(
        "--limit", type=int, default=None,
        help="Cap the sample to this many cases total (for quick smoke tests).",
    )
    p.add_argument(
        "--n-agents", type=int, default=30,
        help="Number of swarm agents per pipeline run. Default: 30.",
    )
    return p.parse_args(argv)


def _main(argv: list[str] | None = None) -> None:
    import os
    # Ensure the app can boot (SECRET_KEY required by Config)
    os.environ.setdefault("SECRET_KEY", "backtest-runner-key")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        stream=sys.stderr,
    )

    args = _parse_args(argv)
    n_per_class = args.sample // 2

    logger.info(
        "Building sample: n_per_class=%d seed=%d", n_per_class, args.seed
    )
    sample = build_sample(n_per_class=n_per_class, seed=args.seed)

    if args.limit is not None:
        sample = sample[: args.limit]
        logger.info("Applied --limit %d; sample size now %d", args.limit, len(sample))

    logger.info(
        "Sample built: %d cases (%d hits, %d flops)",
        len(sample),
        sum(1 for c in sample if c["label"] == 1),
        sum(1 for c in sample if c["label"] == 0),
    )

    report_fn = _make_real_report_fn(n_agents=args.n_agents)

    logger.info(
        "Running: %d cases × %d repeat(s) = %d pipeline calls",
        len(sample), args.repeats, len(sample) * args.repeats,
    )
    rows = run(sample, repeats=args.repeats, report_fn=report_fn)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)

    logger.info(
        "Wrote %d rows to %s", len(rows), out_path
    )


if __name__ == "__main__":
    _main()
