# Swarmie PMF Readiness Index v1 — Design

**Date:** 2026-06-05
**Status:** Approved (brainstorming) → ready for implementation plan
**Spec scope:** Backend only. Frontend surfacing is a follow-up spec.

---

## Goal

Turn Swarmie's existing heuristic `pmf_score` into a **defensible, calibrated, versioned index** — the first step toward Swarmie becoming a cited standard for measuring startup ideas and PMF readiness.

The index does **not** replace the decision brief. The verdict (`ship_it` / `sharpen_positioning` / `wrong_audience` / `kill`) stays the brand headline. The **PMF Readiness Index** sits underneath it as the calibrated backbone — the citable number that makes the verdict defensible and, over time, becomes the standard.

This is the **calibrate-first** path: the number must mean something on day one, backed by a real ground-truth backtest. We are not shipping an asserted number and calibrating later.

## Non-goals (this spec)

- Public scoreboard UI.
- First-party outcome integration (Swarmie's own users tracked to real outcomes) — that is the v2 moat, deferred.
- Guidance-over-time coach (measure → next move → re-measure).
- Frontend changes beyond what a follow-up spec will add (surfacing index + band + label under the verdict).

## Honesty contract (the brand)

Per `PRODUCT.md`: *"earn accuracy claims, never assert them."* Every claim this index makes is pinned to a corpus version and a calibration result. The index self-labels its own calibration state. Known biases are published, not hidden. If the backtest separation is weak, we report it weak — a weak-but-honest standard beats a strong-sounding fraud.

---

## Architecture

### Component 1 — The index (transparent linear composite)

Reframe existing `_compute_pmf_score` (`backend/app/services/swarm/roast_reporter.py:233`) into a versioned `PmfIndex`.

- Internal compute stays a **transparent linear composite** over named dimensions (auditable = citable). No opaque "LLM rates it 0–100".
- **Surface scale: 0–100** (credit-score feel). Internal dimension math may stay normalized; final rescale to 0–100 for display/citation.
- Carries: point value, **confidence band**, `index_version` (`"1.0"`), and `calibration_status` label.

**Dimensions** (3 exist today, 3 new — all from fields the pipeline already emits, no new LLM calls):

| Dimension | Source field | Status | Direction |
|-----------|-------------|--------|-----------|
| `engagement_rate` | `action_split` (comment+post+0.5·upvote)/total | exists | higher = better |
| `sentiment_score` | `sentiment_split` (pos−neg)/100 | exists | higher = better |
| `segment_fit` | `icp_fit`, size-weighted by agent count | exists | higher = better |
| `objection_severity` | `top_objections` — weight fundamental (demand/willingness-to-pay) objections above cosmetic ones | **new** | higher = worse |
| `silence_penalty` | `silent_share_pct` — high silent share = low pull | **new** | higher = worse |
| `confidence` | synthesis `confidence` (low/med/high) | **new** | controls **band width**, not the point value |

`objection_severity`: map each top objection's category to a severity tier (fundamental vs framing vs cosmetic) via a small static category→tier table; severity = weighted count. Deterministic, no LLM.

`confidence` widens/narrows the reported band; it does not move the point estimate. Low synthesis confidence → wider band → lower **lower-bound**, which is what a cautious citer reads.

**Output object** (additive to `RoastReport`, does not break existing `pmf_score`):

```
pmf_index: {
  value: float,            # 0–100
  band: [low, high],       # confidence interval around value
  index_version: "1.0",
  calibration_status: str  # e.g. "calibrated v1 · YC-matured · AUC 0.6x (CI …)"
}
```

`pmf_score` (0–10) is retained for backward compatibility with the existing eval harness and frontend; `pmf_index.value ≈ pmf_score · 10` is **not** assumed — the index is recomputed from the 6-dim composite with calibrated weights, so it can diverge from the legacy heuristic. That divergence is expected and is the point.

### Component 2 — Ground-truth corpus (YC, tiered)

Source: `yc-oss` public API (`https://yc-oss.github.io/api/companies/all.json`), confirmed live, 5,953 companies, fields include `name`, `former_names`, `one_liner`, `long_description`, `batch`, `status`, `launched_at`, `website`.

**Tier 1 — scale (~1,052 labeled cases).**
- Filter to **matured batches** (batch year ≤ 2018) — outcomes have settled. Measured: 1,668 companies.
- Binary label:
  - **hit** = `status` ∈ {Acquired, Public} → 490
  - **flop** = `status` = Inactive → 562
  - **excluded** = `status` = Active (616) — censored, outcome unknown.
- Class balance ≈ 47/53 (hit/flop) — usable without heavy reweighting.
- Input text = `long_description` (fallback `one_liner`), **decontaminated**:
  - strip `name` + every `former_names` entry (case-insensitive).
  - strip outcome phrases via regex: `acquired|exited|exit(ed)?|shut down|shutdown|now part of|\*Acquired by|wound down|closed( down)?` and trailing exit-date clauses.
  - strip hiring/boilerplate ("we're hiring", "join us", careers URLs).
- **Known residual contamination:** directory text is post-pivot and post-success-polished. Tier 1 is therefore the *directional/scale* tier, not the headline-claim tier.

**Tier 2 — clean slice (~50–100 cases).**
- Match a subset of tier-1 companies to **contemporaneous launch text**:
  - **HN Algolia API** (`https://hn.algolia.com/api/v1/search?query=<company>&tags=show_hn`) for Show HN / Launch HN posts near `launched_at`.
  - Fallback: **Wayback Machine** landing-page snapshot from the launch year.
- This is the real pre-success pitch — minimal hindsight, contemporaneous, name-strippable.
- **The headline calibration claim is reported on this slice**, with tier-1 reported as the supporting large-N directional result.

### Component 3 — Backtest harness (extends `backend/eval/`)

New package `backend/eval/backtest/`, reusing existing eval infrastructure (synth/full modes, `RoastReport` plumbing).

- `corpus.py` — fetch + cache `yc_all.json`, apply maturity filter + labeling, expose tier-1 and tier-2 case lists.
- `decontaminate.py` — name/outcome/boilerplate scrubbing (unit-tested against the known leak cases: 42Floors, SlidePay).
- `runner.py` — run the index over each case; **N repeats per case** to capture run-variance; collect `pmf_index.value` distributions per label.
- `metrics.py` — **AUC** (hit vs flop index distributions), point-biserial correlation, hit-rate@threshold. Report **mean ± std across repeats**.

**Cost guard.** 1,052 cases × N live swarm runs is expensive and slow.
- **Tuning loop runs in synth/canned mode** (reuses existing `eval --mode synth`, deterministic-ish, ~free) for fast weight iteration over tier-1.
- **Live-LLM budget is spent only on the tier-2 clean slice** (~50–100 cases × a few repeats) for the final, reported validation.
- Respects existing `ROAST_MAX_COST_USD` watchdog.

### Component 4 — Weight calibration

- Fit the 6 dimension weights with **logistic regression** (hit=1, flop=0) → interpretable coefficients, output stays a linear composite, probability mapped to 0–100.
- **k-fold cross-validation; report CV AUC, never train AUC** — the overfit guard. With ~1,052 cases, 5-fold is comfortable.
- Lock fitted weights + intercept + scaling into versioned `backend/app/services/swarm/index_weights_v1.json`, loaded at runtime by `PmfIndex`. Fully reproducible from corpus version + fit script.
- Tier-1 fits the weights (scale, big-N); tier-2 is a **held-out clean check** the weights are never fit on.

### Component 5 — The standard artifact

Published rubric doc (`docs/pmf-index/RUBRIC.md` or similar):
- The 6 dimensions, their sources, the fitted weights, score bands.
- **What the index does NOT measure** (team, market timing, execution, real revenue — it measures *reaction signal to a pitch*, not outcome).
- Calibration result: CV AUC on tier-1, AUC on tier-2 clean slice, with confidence intervals.
- Corpus version + date.
- **Named biases:** survivorship (all passed YC's bar → narrow dynamic range), acqui-hire label noise (Acquired ≠ always success), hindsight residual in tier-1 text, censoring (Active excluded), class balance.

`calibration_status` on every index output pins the live number to this artifact and its version.

---

## Data flow

```
YC API ──> corpus.py (filter ≤2018, label hit/flop) ──> decontaminate.py
                                                              │
                          ┌───────────────────────────────────┤
                          ▼                                   ▼
                   Tier 1 (~1052)                      Tier 2 (~50–100)
                   directory text                   HN/Wayback contemporaneous
                          │                                   │
                          ▼                                   │
        synth-mode runner ──> 6-dim features per case         │
                          │                                   │
                          ▼                                   │
        logistic regression (5-fold CV) ──> index_weights_v1.json
                          │                                   │
                          ▼                                   ▼
                  CV AUC (tier-1)                  live-mode runner ──> AUC (tier-2, held out)
                          │                                   │
                          └──────────────> RUBRIC.md <────────┘
                                                │
                          PmfIndex (runtime) loads weights ──> pmf_index{value,band,version,calibration_status}
                                                │
                                          RoastReport (under verdict)
```

## Error handling & edge cases

- **YC API unreachable:** corpus loader uses cached `yc_all.json`; fail loudly if neither present (backtest is offline-capable once cached).
- **Empty/short decontaminated text** (some one-liners vanish after scrubbing): drop case from corpus, log count dropped (report N actually used, not nominal N).
- **HN/Wayback no match** for a tier-2 candidate: skip, try next; tier-2 is best-effort to target size.
- **Run-variance too high** (index std per case large): surface in the harness report; if a single run is unstable, runtime may report median of K runs (decision deferred to plan — costs tokens).
- **Degenerate AUC** (≈0.5): report honestly; do not ship a "calibrated" label claiming separation that isn't there. `calibration_status` would read "uncalibrated — separation not yet demonstrated".

## Testing

- `decontaminate.py`: unit tests against known leak cases (42Floors `*Acquired by Knotel`, SlidePay `Exited October 2014`) — assert outcome phrases + names removed.
- `corpus.py`: assert maturity filter + label mapping counts match the probe (1,668 matured; 490 hit / 562 flop / 616 excluded) against a pinned snapshot.
- `metrics.py`: AUC against a hand-computed small fixture.
- `PmfIndex`: deterministic given fixed weights + fixed report input; 0–100 bounds; band ordering (low ≤ value ≤ high).
- Existing eval harness (`backend/eval/`) must still pass — `pmf_score` retained.

## Open decisions deferred to the plan

- Runtime: report a single index run vs median-of-K (token cost trade-off).
- Exact severity tiers in the `objection_severity` category→tier table.
- Tier-2 target size (50 vs 100) given scraping effort and live-LLM budget.
