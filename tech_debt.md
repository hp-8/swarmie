# Tech Debt Register — Swarmie

_Last evaluated: 2026-11-10. Owner: eng. Scored P0 (product/safety risk) → P2 (hygiene)._

Swarmie is the live product: a slim async-LLM swarm for founder validation
(`backend/app/api/roast.py` + `services/swarm/*`, Vue/Vite SPA frontend). The
legacy MiroFish OASIS/Zep deep-sim engine has been fully removed.

---

## Open debt

### P0 — launch blockers
_None open._

### P1 — quality / reliability
1. **No error tracking / tracing** — only logging. No Sentry-equivalent, no request IDs.
2. **Untested core/API complexity hotspots** (radon): `roast.create_roast` C(20),
   `swarm_runner.run` C(18), `roast.chat_agent` C(17), `roast._run_pipeline` C(16).
   Need characterization tests BEFORE any refactor.
3. **`llm._call_with_retry` C(12) / `_acall_with_retry` C(11)** — sync/async retry
   duplication; dedupe behind shared core (untested → test first).
4. **Backend coverage gate stale** — gate 40%, actual 62%. Ratchet to ~60.

5a. **No load test.** Capacity numbers (4 roasts, 32 threads) are reasoned, not measured.
   Run Locust against a staging deploy (gunicorn doesn't run on Windows).
5b. **Render free plan sleeps/restarts** → cold starts; deploys kill in-flight roasts.
   Accepted for now (2026-11-10).

5c. **Advisor brief not yet measured live.** Prompt rework (what_working / hidden_risks /
   path_forward, calibrated tone) is in; baseline-vs-new eval run pending an LLM key.
   Judge uses the same model tier it grades (self-preference bias) — use a different
   model for the judge when possible. Golden set 12 cases; grow to ~20.
5d. **PDF export omits the advisor brief** (`lib/pdf/template.js`). Share card fine.

### P2 — hygiene / scale-later
5. **Rate limiter is in-memory** — correct only while Render runs 1 gunicorn worker.
   Scaling out → switch `storage_uri` to `REDIS_URL`.
6. **Mixed-language comments** (Chinese) linger in some live files (e.g. config).
7. **`requirements.txt` vs `requirements-prod.txt`** near-identical post-legacy.
   Collapse to one source (check `render.yaml` build cmd first).
8. **No TS linting** — `HeroSwarm.vue` (`<script lang="ts">`) excluded from ESLint;
   needs typescript-eslint + tsconfig. Revisit only if the app adopts TS more broadly.
9. **Dev-only audit lows/moderates** (lhci/uuid) — fix downgrades lhci (breaking). Skipped.

### Product-design decisions (not bugs)
- `_compute_sentiment_split` excludes upvotes — metric is "sentiment of those who
  spoke"; PMF credits upvotes via engagement. Changing = redefining metric + UI.
- Confidence ceiling (<15 → low) — deliberate guardrail (`test_roast_reporter.py`).

---

## Resolved
- **2026-06-02** Legacy deep-sim removed — frontend ~16k LOC + backend ~20k LOC +
  OASIS/Zep/camel deps (`64bf85e`, `3e823dd`, `9303765`).
- **2026-06-02** Result.vue reaction-cell dedup (`4db412c`); PitchInput SWARMS →
  `lib/swarms.js`, DeckDropzone extracted (`9832968`, `5e1f1c2`).
- **2026-06-02** LLM eval harness — `backend/eval/`, 6 golden cases, synth/full/judge modes.
- **2026-06-02** Frontend Vitest (86 tests).
- **2026-06-02** Bundle code-split — entry 696 → 21.9 kB (gzip 8.2); jsPDF lazy on click.
- **2026-06-02** `_synthesize` → `SynthesisResult` dataclass + `_parse_synthesis`;
  D(24)→C(11), killed positional 9-tuple.
- **2026-06-02** `_compute_pmf_score` segment_fit now size-weighted by agent count.
- **2026-06-04** CI gates blocking: ruff, eslint, prod-dep `npm audit` (high+),
  pytest, vitest, build. Branch protection on. radon informational.
- **2026-06-04** Coverage gates — backend `--cov-fail-under=40`; frontend vitest v8
  thresholds (stmts 65 / lines 68 / branches 55 / funcs 50, Result.vue excluded).
- **2026-06-04** Vite high-severity vulns cleared (`npm audit fix`).
- CORS allowlist (`CORS_ORIGINS`) + per-IP limits on roast create (5/h) and chat (30/h) — `a7113b3`.
- **2026-11-10** `ProxyFix` (`TRUSTED_PROXY_HOPS`, default 1): limiter previously keyed on
  Render's proxy IP → all users shared one 5/h bucket.
- **2026-11-10** Global roast cap (`MAX_CONCURRENT_ROASTS`, default 4) → 503 + body
  `retry_after_seconds` when full, not counted against the per-IP quota. gunicorn
  threads 8 → 32 (each live SSE stream pins a thread; 8 viewers used to stall the app).

---

## Local pre-push check
Run `./ci-local.sh` from repo root before every push — should mirror `ci.yml`
(blocking: ruff, eslint, prod `npm audit`, pytest + coverage, vitest + coverage,
build; informational: radon). Only push when it prints the pass line.

---

## Baseline metrics (backend 2026-11-10; frontend/Lighthouse 2026-06-04)
| | Before | Now |
|---|---|---|
| Backend tests | 32 | 242 passed, 10 skipped |
| Backend coverage | — | 62% (gate 40) |
| Frontend tests | 0 | 86 (Vitest) |
| Frontend entry chunk | 696 kB | 21.9 kB (gzip 8.2) |
| Lighthouse (Home) | — | Perf 81 · A11y/BP/SEO 100 |
| Worst CC | `_synthesize` D(24) | `create_roast` C(20) |
