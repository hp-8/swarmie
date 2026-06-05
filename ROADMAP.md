# Swarmie Roadmap

A living document. Order roughly reflects priority.

## Phase 0 — Inherited Core (Done)

Forked from MiroFish, rebranded, rebased for founder-validation use case.

- [x] OASIS-based simulation engine
- [x] Zep graph memory
- [x] Ontology → persona pipeline
- [x] Report agent with tool-loop
- [x] Multi-step founder UI (5 steps)
- [x] Apache-2.0-licensed OASIS dependency

## Phase 1 — Founder-First Surface (mostly done)

Make the experience match the audience.

- [x] Pitch input wizard — paste deck text, structured template (problem/product/audience/pricing/competitors)
- [ ] ICP picker (B2B SaaS, indie devs, creators, D2C, …) — parser infers ICP; explicit picker still open
- [x] 60-second "quick sim" mode (small swarm, no Zep, just LLM personas)
- [x] Shareable result (copy link + PDF export) — auto-generated per-result PNG still open
- [x] Friction-free first run (no signup, no Zep required)
- [x] Atmospheric, fully-responsive marketing site (canvas swarm hero)

## Phase 1.5 — Decision Brief (done, beyond original plan)

Turn the output from a vanity scorecard into an action tool.

- [x] Verdict (ship / sharpen / wrong-audience / kill) + confidence band + single next action
- [x] Per-objection user-test question, kill-criteria, suggested fix
- [x] "Why N% scrolled past" — sampled, capped, cost-safe silence analysis mapped to fixes
- [x] Per-agent chat; verdict-led Result page hierarchy
- [x] Two feedback layers (per-objection votes + product feedback) → Supabase

## Phase 2 — Founder Intelligence Platform: v1 Swarms (next focus)

The evolution from a single validation tool into a platform of decision-specific swarms. Each swarm answers one founder decision and ends in a **verdict + next action**, never a dashboard. The wedge that escapes the synthetic-trust ceiling: pair **real market signal** with Swarmie's **synthetic reaction** — the comparison is the moat *and* the calibration ground-truth. v1 ships two.

> **Principle for every swarm: decision stress-testing, not roleplay.** Never pretend to be reality. The simulation is the interface; the intelligence is the product. Ground in real signal over time so synthetic reactions stay calibrated.

### Launch Swarm — *stress-test the launch* (not "predict your Product Hunt")
Surface the questions, objections, risks, and discussion patterns likely to emerge, from historical community behavior.
- [ ] Reaction patterns across PH / HN / Reddit / Indie Hackers / X archetypes
- [ ] Ground in real, recent threads from those communities (via the signal layer below)
- [ ] Output: likely top comment, objections, a response playbook, go / hold verdict
- [ ] Side-by-side: synthetic reaction vs real community chatter on the same topic

### Investor Swarm — *stress-test fundability* (not "talk to AI investors") — done
Pressure-test the raise against patterns from real investor behavior, discussions, and funding decisions.
- [x] Archetypes drawn from angel / operator / VC patterns reading the deck
- [x] Output: likely questions, partner-meeting objections, missing proof points, the "pass" reasons
- [x] Fundability verdict (fundable / sharpen-story / wrong-stage / not-fundable) + the one fix before the next investor call
- [x] Synthetic-first — no external data dependency, ships fast

### Shared plumbing
- [x] Swarm picker on input (Validate · Investor live; Launch shown as "soon")
- [x] Carry the decision-brief DNA (verdict + next action) into every swarm — subclass-per-swarm registry; pipeline/cost/SSE/storage shared

## Phase 2.5 — Realism / Signal Layer (feeds grounded swarms)

Right now agents are LLM-hallucinated personas. We need real grounding — built **source-agnostic** so Launch Swarm and friends plug in. Start on cheap, clean sources (Reddit official API, HN, public reviews); add X later, only when the data economics justify it (API cost + ToS are real constraints).

- [ ] Reddit + HN ingestion pipeline (PRAW, Pushshift, BigQuery dumps)
- [ ] Comment tagger (sentiment, action-type, objection-category, WTP)
- [ ] Embedding-based persona retrieval (RAG-style: real-comment-conditioned generation)
- [ ] Ship 5 default ICP packs as Hugging Face datasets
- [ ] Activation sampler (80% silence, free, no tokens)

## Phase 3 — Cost Engine

Two goals: realism *and* extreme cost-efficiency.

- [x] Tiered model routing (cheap reactions / deep agents / synthesis)
- [x] Action-roll-before-call sampling (~60% ignore, zero tokens)
- [x] Transparent Gemini fallback when the primary exhausts retries
- [ ] Prompt caching (Anthropic 90% discount, Gemini, DeepSeek)
- [ ] Batch API integration (50% discount where SLA allows)
- [x] Ollama-default config (zero API cost for local users)
- [x] Cost-budget cap per sim (`ROAST_MAX_COST_USD`, watchdog cancels mid-run)

## Phase 4 — Calibration & Trust

A simulation is only worth trusting if it's been measured. The long game: make
the **PMF Readiness Index** a *cited standard* for measuring startup ideas — a
credible, versioned number that backs the verdict (never replaces it). Earned
via real backtest, never asserted.

- [x] Per-sim confidence band in the report (deterministically clamped)
- [x] Feedback collection shipped (per-objection votes + product feedback → Supabase) — the calibration dataset
- [ ] **PMF Readiness Index v1** — reframe heuristic `pmf_score` into a versioned, 0–100, transparent 6-dim linear composite (engagement, sentiment, segment-fit, objection-severity, silence, confidence-band). Backs the verdict. See [spec](docs/superpowers/specs/2026-06-05-pmf-readiness-index-design.md).
- [ ] **YC backtest corpus (tiered)** — calibrate-first against real outcomes from `yc-oss` public data. Tier-1: ~1,052 matured (≤2018 batch) labeled cases (Acquired/Public = hit, Inactive = flop, Active excluded) for scale. Tier-2: ~50–100 HN/Wayback *contemporaneous* pitches for the honest headline claim. Decontaminate (strip names + outcome phrases — directory text literally embeds exits).
- [ ] **Weight calibration** — logistic regression over the 6 dims, 5-fold CV, report CV AUC never train AUC. Locked into versioned `index_weights_v1.json`.
- [ ] **Published rubric** — dimensions, weights, bands, what it does NOT measure, named biases (survivorship, narrow dynamic range, acqui-hire label noise, hindsight residual), live calibration result. Every index output self-labels `calibration_status`.
- [ ] Surface index + band + label under the verdict (frontend follow-up spec)
- [ ] First-party outcomes (v2) — fold Swarmie's own users tracked to real outcomes into the corpus over time; the truest, on-distribution calibration ground
- [ ] Public scoreboard pinned to corpus version

> Honesty guardrail: the backtest calibrates *reaction-signal quality against
> outcomes* — it does **not** turn Swarmie into a success-predictor (see
> Non-Goals). The index claims usefulness, pinned to a corpus version, not
> realism.

## Phase 5 — More Swarms (platform expansion)

After the v1 swarms (Phase 2) prove the model. Each must still end in a decision, not a dashboard.

- [ ] **Acquisition Swarm** — where your first users already hang out: communities, channels, creators, conversations
- [ ] **Competitor Swarm** — why customers choose / leave competitors, and the gaps left open
- [ ] **Signal Swarm** — buying intent, recurring frustrations, unmet needs from public conversations
- [ ] **Trend Swarm** — emerging pain points and new categories before they're obvious
- [ ] **Positioning A/B** — run N positionings in parallel, compare verdicts
- [ ] **Continuous monitoring** — re-run weekly against a tracked product

## Phase 6 — Open-Weights First-Class

- [ ] Distilled `swarmie-agent-7b` published on Hugging Face
- [ ] One-line install with bundled Ollama model
- [ ] Provider-agnostic adapter layer (Groq, Together, OpenRouter, Fireworks, …)

## Phase 7 — Paid Tiers

**Value-first:** monetize only once the swarms (Phase 2 + 5) make Swarmie indispensable and usage proves out. Free 60s text brief stays the viral top-of-funnel. Paid bets, in rough priority:

- [ ] **Live voice interview / panel** — talk to personas over the realtime API; they interrupt, object, follow up
- [ ] **Real-user bridge** — recruit 5 real ICP users to test the kill-criteria the sim generated (concierge first, then marketplace cut)
- [ ] **Paid swarms** — credits per grounded Launch / Investor / Acquisition run
- [ ] **Positioning monitor** (subscription) — weekly re-runs, alert on market/sentiment shifts
- [ ] Pricing: free brief · credits (voice / grounded / vision) · subscription (monitor / lab) · marketplace cut (real-user bridge)

## Non-Goals

- Replacing real user research. Swarmie complements it, not replaces it.
- Predicting "will this startup succeed?" — we predict *reactions*, not outcomes.
- Pretending the agents are real users. We will always disclose synthesis.

---

Open an issue or discussion to push for priority changes.
