# Swarmie Eval Harness

Offline quality evaluation for the Swarmie roast pipeline. Measures whether the
LLM output pipeline produces verdicts, objection themes, report schemas, and PMF
scores that are consistent with human-annotated expectations.

---

## Quick Start

All commands run from `backend/` with the venv active.

### Synth mode (offline — no API key required)
```bash
.venv/bin/python -m eval.run
# or explicitly:
.venv/bin/python -m eval.run --mode synth
```
Uses canned reactions and a stubbed LLM narrative call. Fully offline.

### Full mode (live pipeline — requires API key)
```bash
export LLM_API_KEY=sk-...  # or set in .env
.venv/bin/python -m eval.run --mode full
```
Runs the real pipeline: `PitchParser → ArchetypeGenerator → SwarmRunner → RoastReporter`.
Uses a reduced agent count (20 agents, 6 archetypes) for cost/speed. Expect ~$0.05–$0.20 per
case depending on model tier.

### Run a subset of cases
```bash
.venv/bin/python -m eval.run --cases tally_validate,strong_dev_tool
```

### Consistency check (3 runs per case, measures verdict stability)
```bash
.venv/bin/python -m eval.run --runs 3
# Full mode recommended for meaningful stability data:
.venv/bin/python -m eval.run --mode full --runs 3
```

### LLM-as-judge rubric
```bash
export LLM_API_KEY=sk-...
.venv/bin/python -m eval.run --judge
```
Scores each report on clarity, specificity, and actionability (1–5 each) via an LLM call.

### Write JSON results
```bash
.venv/bin/python -m eval.run --json-out /tmp/eval_results.json
```

### Run as pytest (offline portion)
```bash
.venv/bin/python -m pytest tests/test_eval_smoke.py -q
```

---

## What the Scores Mean

### Per-case score
Fraction of deterministic checks that pass (0–100%). The pass bar is **70%** per case.

### Deterministic checks (8 per case)
| Check | What it verifies |
|---|---|
| `schema` | All required report keys present with correct types |
| `verdict` | Verdict is a valid enum value AND in the case's expected set |
| `objection_themes` | ≥50% of required objection keyword groups appear in top_objections |
| `pmf_direction` | PMF score is in the expected range (positive ≥4.5, negative <6.0) |
| `confidence_ceiling` | Confidence doesn't exceed the case's declared ceiling |
| `sentiment_split_sums` | Positive + neutral + negative ≈ 100% |
| `action_split_non_negative` | All action counts are non-negative integers |
| `narrative_non_empty` | Both headline and narrative are non-empty strings |

### Consistency score
Fraction of N runs that produced the same (dominant) verdict. 100% = perfectly stable.
In synth mode, this will always be 100% because the stub is deterministic; run in full
mode for meaningful stability data.

### LLM-as-judge scores (1–5)
- **clarity** — narrative is clear, jargon-free, actionable
- **specificity** — cites specifics from this pitch, not generic advice
- **actionability** — next_action is one concrete, specific step
- **avg** — mean of the three dimensions

---

## How to Add a Golden Case

1. Open `eval/golden_set.py` and add a new entry to `GOLDEN_CASES`:
   ```python
   {
       "id": "my_new_case",               # unique slug
       "swarm_type": "validate",          # validate | investor | launch
       "pitch_text": "...",               # raw pitch text
       "expected_verdicts": {"ship_it", "sharpen_positioning"},
       "required_objection_themes": [
           ["price", "cost"],             # at least one kw must appear
           ["trust", "privacy"],
       ],
       "pmf_direction": "positive",       # positive | neutral | negative
       "confidence_ceiling": "high",      # low | med | high
       "notes": "Human annotation.",
   }
   ```

2. Add canned reactions to `eval/canned_reactions.py`:
   - Use the `_r()` helper (see file for signature)
   - Add at least 10–15 reactions mixing all four actions
   - For ignore reactions, use keyword args: `_r(N, seg, tone, "ignore", ig_reason="...", ig_cat="not_my_problem")`
   - Register in the `CANNED` dict at the bottom

3. Run the smoke test to verify:
   ```bash
   .venv/bin/python -m pytest tests/test_eval_smoke.py -q
   ```

---

## File Structure

```
eval/
  __init__.py           # package marker
  golden_set.py         # 6 golden cases with annotations
  canned_reactions.py   # hand-crafted reactions for synth mode
  checks.py             # deterministic scoring functions
  run.py                # CLI harness (synth/full/judge modes)
  README.md             # this file

tests/
  test_eval_smoke.py    # pytest — offline CI gate (31 tests)
```

---

## Known Limitations

1. **Synth-mode verdict is stub-driven.** In synth mode, the roast_reporter LLM call
   is stubbed with a canned response derived from the golden case's expected verdicts.
   This means the verdict check in synth mode is verifying infrastructure correctness
   (schema, metrics, confidence clamping) rather than LLM judgment quality. Use
   `--mode full` to evaluate actual LLM verdict quality.

2. **Objection theme check is corpus-based.** The check looks for keyword matches in
   `top_objections[*].category` and `top_objections[*].example_quote`. In synth mode,
   objection categories come from the canned reactions, so they reflect what the canned
   reactions surfaced — not live LLM output. In full mode, this is a genuine quality
   signal.

3. **Canned reactions are deterministic.** The PMF score, sentiment split, and action
   split in synth mode are fully deterministic (computed from canned data). They reflect
   the quality of the deterministic metric computation code, not LLM variability.

4. **Consistency check is only meaningful in full mode.** In synth mode, all 3 runs
   produce identical verdicts (100% stability) because both the reactions and the LLM
   stub are deterministic.

5. **LLM-as-judge uses the same model.** The judge rubric is called via the `synth`
   tier LLM — the same model being evaluated. This is a known self-evaluation bias.
   For stricter evaluation, configure a different judge model via `LLM_SYNTH_*` env vars.

6. **Full mode uses a reduced agent count.** To control cost during eval, full mode
   runs 20 agents (vs 100 in production). This makes the eval cheaper but reduces
   the signal quality compared to production runs.

---

## Production Bugs / Observations

No production code was modified. Observations from reading the production code:

1. **`_compute_sentiment_split` only counts `comment` and `post` actions** — `upvote`
   reactions are excluded from sentiment computation. This means a pitch with 60%
   upvotes and 40% neutral comments would show 0% positive sentiment, which is
   misleading. The PMF score formula also excludes upvote sentiment.

2. **`_compute_pmf_score` uses `avg_sentiment > 0.1` per segment** for the segment fit
   component, but ignores segment size. A single-agent segment with high sentiment
   scores equally to a 20-agent segment, which can distort the score for small swarms.

3. **Confidence ceiling logic** (in `_synthesize`) computes the ceiling deterministically
   but the `speaking_count < 15` branch produces ceiling `"low"` regardless of the
   quality signal. With 14 strong positive reactions, `confidence` is capped at `"low"`,
   which may under-signal good pitches for small swarms.
