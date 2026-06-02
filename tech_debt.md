# Tech Debt Register — MiroFish / Swarmie

_Last evaluated: 2026-06-02. Owner: eng. Scored P0 (product/safety risk) → P2 (hygiene)._

Swarmie is the live product: a slim async-LLM swarm for founder validation
(`backend/app/api/roast.py` + `services/swarm/*`, Vue/Vite SPA frontend). The
legacy MiroFish OASIS/Zep deep-sim engine has been fully removed.

---

## Resolved (refactor pass, 2026-06-02)

- **Legacy deep-sim removed** — frontend ~16k LOC (bundle 903→696 kB) + backend
  ~20k LOC + OASIS/Zep/camel deps. Commits `64bf85e`, `3e823dd`, `9303765`.
- **Result.vue** reaction-cell dedup (objections/quotes 3→1; fixed deck glyph bug). `4db412c`
- **PitchInput.vue** SWARMS catalogue → `lib/swarms.js`; DeckDropzone extracted. `9832968`, `5e1f1c2`

---

## Open debt

### P0 — product risk / no safety net
1. **No LLM output-quality eval.** The core product (roast verdict/objection
   quality) is unmeasured. Prompt changes can silently regress. No golden set,
   no consistency check, no LLM-as-judge. → build eval harness (seed:
   `test-pitches.local.txt`). _Highest priority — can't claim the product is good without it._
2. **Frontend: zero automated tests.** UI just refactored (3 new components +
   Result/PitchInput) with no net. → Vitest + Vue Testing Library.
3. **CORS = `*`** on `/api/*` (`backend/app/__init__.py`). Lock to the prod
   origin before any public launch. + no rate limiting on `/api/roast`.

### P1 — quality / performance
4. ~~**Frontend bundle is one 696 kB chunk.**~~ ✅ DONE 2026-06-02 — lazy routes +
   `manualChunks` + dynamic `import('jspdf')` on PDF click. Entry chunk 696 → **21.9 kB**
   (gzip 8.2 kB); PDF (589 kB) now loads only on download.
5. **No CI quality gates** — lint (ruff/eslint), complexity (radon), coverage,
   dep-audit, Lighthouse all run ad hoc / never. → next.
13. **`roast_reporter` product-logic bugs** (found by eval harness, NOT yet fixed):
    - `_compute_sentiment_split` ignores `upvote` reactions → a mostly-upvoted pitch
      shows 0% positive sentiment while its PMF still benefits. Misleading to founders.
    - `_compute_pmf_score` segment_fit is size-blind — a 1-agent segment weighs the
      same as a 20-agent one; inflates scores on unrepresentative micro-segments.
    - Confidence ceiling at `speaking_count < 15` is absolute — 14 strongly-aligned
      agents still force `confidence=low` regardless of signal quality.
6. **Backend complexity hotspots** (radon, 2026-06-02; MI all A so localized, not rot):
   - `roast_reporter._synthesize` — **CC D(24)**, returns a positional 9-tuple
     (unpack footgun). TESTED → extract `SynthesisResult` dataclass. _Safe, do next._
   - `roast.create_roast` C(20), `swarm_runner.run` C(18), `roast.chat_agent`
     C(17), `roast._run_pipeline` C(16) — untested core/API; need
     characterization tests BEFORE any refactor.
   - `llm._call_with_retry` C(12) / `_acall_with_retry` C(11) — sync/async retry
     duplication; dedupe behind shared core (untested → test first).
7. **No backend coverage measurement.** 32 tests pass; % unknown. Add `pytest-cov`.

### P2 — hygiene
8. **Mixed-language comments** (Chinese) linger in some live files (e.g. config).
   Inconsistent for an English-first codebase.
9. **`requirements.txt` vs `requirements-prod.txt`** now near-identical post-legacy.
   Collapse to one source (check `render.yaml` build cmd first).
10. **`utils/retry.py` appears unused** (0 importers found) — verify + remove if dead.
11. **No error tracking / tracing** — only logging. No Sentry-equivalent, no request IDs.
12. **Frontend is plain JS, no type checking, ESLint config unverified.**

---

## Baseline metrics (updated 2026-06-02, post-tooling)
| | Before | Now |
|---|---|---|
| Backend tests | 32 | **63** (+31 eval smoke) |
| Frontend tests | 0 | **86** (Vitest) |
| Frontend entry chunk | 696 kB | **21.9 kB** (gzip 8.2) |
| Lighthouse (Home) | — | Perf 81 · A11y/BP/SEO 100 |
| Backend LOC (app) | ~4.2k, MI all A (27–39) | — |
| Worst CC | `_synthesize` D(24) | — (unchanged) |

## In-flight (this session)
- [x] P0-1 LLM eval harness — `backend/eval/`, 6 golden cases, synth/full/judge modes
- [x] P0-2 frontend Vitest — 86 tests
- [x] P1-4 Lighthouse + bundle code-split
- [ ] P1-5 CI quality gates — next
- [ ] P1-6 `_synthesize` dataclass extraction
- [ ] P1-13 fix the 3 roast_reporter logic bugs (eval surfaced them; verify w/ harness)
