# Swarmie — Show HN Submission

---

## Title (primary)

`Show HN: Swarmie – open-source AI swarm that roasts your startup (free on Ollama)`

## Title (alternative)

`Show HN: Swarmie – paste a pitch, get a decision brief from 500 AI personas (AGPL, Ollama-first)`

---

## Body (150–250 words)

Swarmie takes a startup pitch and runs an async LLM swarm of 100–500 personas against it.

The architecture: a two-tier model router picks between a small fast model for simple reactions and a larger model for synthesis tasks (objection clustering, verdict generation, silence analysis). About 60% of agents are configured to silently ignore the pitch — we call this the "scroll past" tier. They produce no LLM call at all, which keeps costs near zero for the majority and models the fact that real audiences do the same. There's a hard cost ceiling on the hosted version; the Gemini fallback kicks in if the primary model is rate-limited.

The output is a Decision Brief, not a score: verdict (ship it / sharpen / wrong audience / kill) + confidence band, a single next action, ranked objections each with a kill-criteria and the exact question to test with 5 real users, and a silence analysis explaining why the majority didn't engage.

There's an Investor Swarm mode (stress-tests fundability against likely partner-meeting questions).

Honest limits: the personas carry training-data biases, are wrong sometimes, and cannot replace real user research. We say so on every screen.

Runs for $0 on local Ollama — no key needed. AGPL-3.0.

GitHub: github.com/hp-8/swarmie
Live: swarmie.vercel.app

I'd like HN to roast the roaster. Tell me where the brief is wrong.

---

## Prepared Answers to Likely HN Comments

---

### 1. "Why not just use one LLM call? You're adding overhead for a parlor trick."

The structural difference: a single LLM asked "what are the objections to this pitch?" optimizes for a helpful, comprehensive answer. It hedges, it balances, it averages. The swarm forces 100+ independent calls with distinct persona prompts, different objection biases, and no visibility into each other's outputs — the clustering happens post-hoc, not pre-consensus. The silent majority (zero-cost ignores) models the attention dynamic. It's not a parlor trick — it's a deliberate architectural choice to prevent the averaging-into-mush that single-agent evaluations produce. Whether the output is better is empirically testable: run your pitch both ways and compare which objections you didn't see coming.

---

### 2. "The 'personas' are just prompt variations. They're all the same model under the hood."

True — they share the same weights. The diversity comes from prompt conditioning (background, segment, tone, objection biases injected per persona) and from the independence of the calls: no agent sees another's output during generation. Whether prompt-conditioned diversity is meaningful or illusory is a fair research question. Our position: it surfaces different objection clusters than a single call does in practice, which is what we can observe. We're not claiming the personas are psychologically distinct agents. We're claiming the output distribution across 500 conditioned calls is more useful than one unconditioned call. If you've seen evidence either way, I'm genuinely interested.

---

### 3. "Cost ceiling — what is it, and what happens when you hit it?"

The hosted version has a per-run token cap and a monthly ceiling on our end. When the ceiling is hit, new runs queue or the Gemini fallback route is used (lower cost per token). Users are not billed. We don't collect payment information. If costs become unsustainable, the hosted version goes offline and the AGPL source remains. Self-hosting with your own Ollama or API key has no ceiling at all.

---

### 4. "AGPL is a poison pill for any commercial use. Why not MIT?"

Intentional choice. AGPL ensures that if someone builds a hosted service on top of Swarmie, they have to publish their modifications. MIT would let a company fork it, add a proprietary layer, and close the source. We want the core tooling to stay inspectable and improvable — especially given that the output is intended to influence real business decisions. If you want to use it in a closed commercial context, the license allows that with a commercial exception — reach out.

---

### 5. "How do you validate that the Decision Brief output is actually useful?"

We don't have a rigorous benchmark, and I won't pretend we do. The most honest current answer: we have qualitative feedback from founders who ran pitches and found the top objection was something they'd been avoiding in real conversations — and that running the brief before a user interview changed the questions they asked. That's not a controlled study. The kill-criteria in the output are designed to be testable with 5 real users, which is the closest thing to ground truth we can point to. If anyone wants to build an eval benchmark for this (pitch → brief → real user interview concordance), I'd contribute to that.

---
