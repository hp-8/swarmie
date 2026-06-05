# Swarmie PMF Readiness Index — Rubric v1

**Status:** weights NOT yet calibrated — see [Calibration result](#calibration-result). Until a calibration run lands, every index output self-labels `calibration_status: "uncalibrated — no weights"` and the verdict stands alone.

The PMF Readiness Index is a transparent, versioned number (0–100) that **backs** Swarmie's verdict — it does not replace it. The verdict (ship / sharpen / wrong-audience / kill) stays the headline. The index is the calibrated backbone: an auditable, citable measure that earns trust by being measured against real outcomes, never asserted.

Design spec: [`docs/superpowers/specs/2026-06-05-pmf-readiness-index-design.md`](../superpowers/specs/2026-06-05-pmf-readiness-index-design.md).

---

## What the index is

A logistic-regression composite over **5 deterministic dimensions** computed from a swarm's reaction to a pitch. Output scaled to 0–100 with a confidence band. The weights are fit against real startup outcomes (see Corpus); the formula and weights are published here so anyone can audit how a number was reached.

## The 5 dimensions

| Dimension | Source (from the roast report) | Direction |
|-----------|-------------------------------|-----------|
| `engagement_rate` | `(comment + post + 0.5·upvote) / total_actions` | higher = better |
| `sentiment_score` | `(positive% − negative%) / 100` | higher = better |
| `segment_fit` | size-weighted share of ICP segments with avg sentiment > 0.1 | higher = better |
| `objection_severity` | severity-weighted top objections (fundamental > framing > cosmetic) | higher = worse |
| `silence_penalty` | `silent_share_pct / 100` (share who scrolled past) | higher = worse |

`confidence` (the synthesis confidence: low / med / high) is **not** a fitted feature — it sets the width of the reported band (low → ±18, med → ±10, high → ±5). The point estimate is the calibrated probability × 100; the band communicates how much weight to put on it.

Weights are not pre-assigned by direction — the logistic regression learns each dimension's sign and magnitude from the data. The "higher = worse" dims are expected to receive negative coefficients, but that is an output of calibration, not an assumption.

## What the index does NOT measure

The index measures **reaction signal to a pitch**, not the startup's destiny. It says nothing about:

- **Team** — who is executing, their track record, ability to ship.
- **Market timing** — whether now is the right moment.
- **Execution** — can they actually build and distribute it.
- **Real revenue / retention** — it sees a pitch, not a P&L or a cohort curve.

A high index means *the swarm reacted the way it reacts to pitches that historically reached good outcomes* — a calibrated signal, not a prophecy. Per Swarmie's non-goals: we predict reactions, not outcomes. The index claims **usefulness pinned to a corpus version**, never realism.

## Corpus (ground truth)

Calibrated against **real YC company outcomes** (`yc-oss` public dataset).

- **Tier 1 (scale):** matured batches (≤ 2018), binary labelled — Acquired/Public = hit, Inactive = flop, Active excluded (censored). ~1,052 labelled cases (490 hit / 562 flop). Directory text, name- and outcome-phrase-scrubbed. *Directional* tier.
- **Tier 2 (clean):** ~50–100 companies matched to contemporaneous launch text (Show HN / Launch HN / Wayback landing copy from launch year). Real pre-success pitch, minimal hindsight. **The headline AUC is reported on this held-out tier.**

## Known biases

A standard is only honest if it names its own weaknesses:

- **Survivorship / narrow dynamic range** — every YC company already passed YC's bar. The index separates "winners from winners-that-died," not obvious flops from obvious hits. A modest AUC here is harder-won and more meaningful than separating cartoon cases.
- **Acqui-hire label noise** — "Acquired" includes soft-landing acqui-hires that were not real successes.
- **Hindsight residual** — Tier-1 directory text is post-pivot and post-success-polished even after scrubbing. This is why the headline claim is reported on the contemporaneous Tier-2 slice.
- **Censoring** — "Active" companies (outcome unknown) are excluded; the corpus is settled outcomes only.
- **Run variance** — swarm reactions are stochastic; the index varies run to run. The backtest reports mean ± std across repeats.

## Calibration result

> **PENDING — no calibration run has been executed yet.**
>
> Once `eval/backtest/runner.py` → `eval/backtest/calibrate.py` runs on the corpus, this section reports:
> - **CV AUC (Tier-1, 5-fold out-of-fold):** _tbd_
> - **AUC (Tier-2 held-out clean slice):** _tbd_ — the headline claim
> - **n / hits / flops, corpus version, date.**
>
> If CV AUC lands in [0.45, 0.55], separation is not demonstrated and the index ships labelled `"uncalibrated — separation not demonstrated"`. A weak-but-honest result is reported as weak.

## Reproducing

```bash
cd backend
pip install -r eval/requirements-eval.txt          # eval-only: sklearn, numpy

# 1. extract features (runs the swarm; needs an LLM engine — Ollama free or .env key)
.venv/bin/python -m eval.backtest.runner --sample 200 --balanced --repeats 1 \
    --out eval/backtest/data/features_tier1.json

# 2. calibrate weights (writes index_weights_v1.json + prints CV AUC)
.venv/bin/python -m eval.backtest.calibrate \
    --features eval/backtest/data/features_tier1.json \
    --out app/services/swarm/index_weights_v1.json
```

The runtime scorer (`app/services/swarm/pmf_index.py`) loads `index_weights_v1.json` and is pure stdlib — no sklearn at runtime. Versioned: claims pin to the corpus + weights version recorded in the JSON.
