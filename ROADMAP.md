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

## Phase 1 — Founder-First Surface (in progress)

Make the experience match the audience.

- [ ] Pitch input wizard — paste deck text / URL, not generic doc upload
- [ ] ICP picker (B2B SaaS, indie devs, creators, D2C, …)
- [ ] 60-second "quick sim" mode (100 agents, no Zep, just LLM personas)
- [ ] Shareable result card (auto-generated PNG / OG image)
- [ ] Friction-free first run (no signup, no Zep required)

## Phase 2 — Realism Layer

Right now agents are LLM-hallucinated personas. We need real grounding.

- [ ] Reddit + HN ingestion pipeline (PRAW, Pushshift, BigQuery dumps)
- [ ] Comment tagger (sentiment, action-type, objection-category, WTP)
- [ ] Embedding-based persona retrieval (RAG-style: real-comment-conditioned generation)
- [ ] Ship 5 default ICP packs as Hugging Face datasets
- [ ] Activation sampler (80% silence, free, no tokens)

## Phase 3 — Cost Engine

Two goals: realism *and* extreme cost-efficiency.

- [ ] Tiered model routing (cheap reactions / deep agents / synthesis)
- [ ] Prompt caching (Anthropic 90% discount, Gemini, DeepSeek)
- [ ] Batch API integration (50% discount where SLA allows)
- [ ] Ollama-default config (zero API cost for local users)
- [ ] Cost-budget cap per sim (`--max-cost 0.50`)

## Phase 4 — Calibration & Trust

A simulation is only worth trusting if it's been measured.

- [ ] Backtest harness — `npm run eval`
- [ ] 20 ground-truth cases (10 hits, 10 flops)
- [ ] Public scoreboard pinned to corpus version
- [ ] Per-sim confidence score in the report

## Phase 5 — Adjacent Modes

Same engine, different agent populations.

- [ ] **Investor reaction mode** — simulate 50 VC archetypes reading a pitch deck
- [ ] **Launch dress rehearsal** — predict PH / HN / Twitter launch reception
- [ ] **Positioning A/B** — run N positionings in parallel, compare scores
- [ ] **Continuous monitoring** — re-run weekly against a tracked product

## Phase 6 — Open-Weights First-Class

- [ ] Distilled `swarmie-agent-7b` published on Hugging Face
- [ ] One-line install with bundled Ollama model
- [ ] Provider-agnostic adapter layer (Groq, Together, OpenRouter, Fireworks, …)

## Non-Goals

- Replacing real user research. Swarmie complements it, not replaces it.
- Predicting "will this startup succeed?" — we predict *reactions*, not outcomes.
- Pretending the agents are real users. We will always disclose synthesis.

---

Open an issue or discussion to push for priority changes.
