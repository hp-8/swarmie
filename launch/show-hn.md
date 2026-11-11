# Swarmie V2: Show HN Submission

---

## Title (primary)

`Show HN: Swarmie – a panel of 500 AI reviewers writes a decision memo on your pitch`

## Title (alternative)

`Show HN: Swarmie v2 – open-source LLM panel that critiques startup pitches (AGPL, Ollama)`

---

## Body (150–250 words)

Swarmie takes a startup pitch and runs it past a panel of LLM reviewers: 20 on the free hosted tier, up to 500 with a pack, unlimited if you self-host.

Architecture: a two-tier model router uses a small fast model for individual reactions and a larger one for synthesis. Each reviewer rolls an action from its archetype's distribution: post, comment, upvote or scroll past. Ignorers (beyond a small sampled subset asked "why'd you scroll past?") make no LLM call, so silence is free, like real attention. Hosted runs have a hard per-run cost cap.

V2 changed the output. It's now a decision memo: verdict, what's working, hidden risks, objections, a path forward, and exhibits (the reactions that back each claim). V1 skewed harsh, so V2 calibrates tone, and an eval checks it on every change: an LLM judge scores the full memo on six dimensions, and trap cases check for flattery, needless harshness and a planted hidden risk the memo has to find.

Three review types: Validate, Investor (deck upload) and Launch.

Limits: the reviewers share one model's biases, they're wrong sometimes, and this doesn't replace talking to users. Every screen says so.

AGPL-3.0, runs for $0 on local Ollama.

GitHub: github.com/hp-8/swarmie
Live: swarmie.harshpatadia.com

Tell me where the memo is wrong.

---

## Prepared Answers to Likely HN Comments

### 1. "Why not one LLM call?"
One call asked for objections optimizes for a balanced, helpful answer, so it averages. The panel makes independent calls with distinct persona conditioning and no visibility into each other; clustering happens afterwards. Whether that's better is testable: run your pitch both ways and see which objections you didn't predict.

### 2. "The personas are all the same model."
True. Diversity comes from prompt conditioning and call independence, not different weights. We don't claim psychologically distinct agents; we claim the spread across conditioned calls surfaces objections a single call misses. Happy to see evidence either way.

### 3. "How do you know the memo is any good?"
Partly answered in V2. `backend/eval/` has a golden set of pitches, an LLM judge that scores the full memo (not just the headline) on six dimensions, and six trap cases: pitches built to bait flattery, bait harshness, or hide a planted risk. Every memo change runs against it. There's also a backtest harness on known hits and flops. What we don't have is ground truth against real user interviews. That's the eval I'd most like to build, and I'd take help.

### 4. "You're charging now?"
Small reviews stay free and unlimited with no signup. Packs ($5 for 5 full reviews and up) pay for 500-reviewer panels and the Investor and Launch modes, which cost real tokens. No subscription, failed runs are refunded automatically, and self-hosting stays free under AGPL.

### 5. "AGPL is a poison pill."
Intentional. Anyone hosting a modified version has to publish their changes, so the core stays inspectable. For closed commercial use, reach out about a commercial license.

### 6. "Cost ceiling: what happens when you hit it?"
Each run has a hard cost cap (`ROAST_MAX_COST_USD`). If a run exceeds it, the run is cancelled and says so instead of degrading silently, and a paid run's credit is refunded.
