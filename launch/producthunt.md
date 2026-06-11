# Swarmie — Product Hunt Launch Kit

---

## Tagline Options (pick one — each < 60 chars)

1. **Roast your startup with 500 AI users in 60 seconds.**
2. **The objection you're avoiding, surfaced in 60 seconds.**
3. **A decision brief for your pitch. Not a score.**

---

## Description (≤ 260 chars)

Paste your pitch. A swarm of 100–500 AI personas reacts like Reddit, HN, and Product Hunt at once — some scroll past, the rest roast it. You get a Decision Brief: verdict, top objections, kill-criteria, and why the silent ones left.

---

## Maker First Comment

---

I built Swarmie because I was tired of validators that lie nicely.

You know the type — you paste your pitch, they hand back a number. "8.1 / 10." "Strong market signal." You feel slightly better. You ignore the thing you already suspected was wrong with your positioning. Three months later you're in a user interview and someone says the exact thing the number never surfaced.

Swarmie is built around a different premise: **the output should cost something to ignore.**

Here's what it actually does:

- Runs 100–500 AI personas against your pitch, each with a different background, bias, and attention span
- Part of the swarm scrolls past without reacting — because real audiences do that, and modeling silence is free
- The ones who stop leave objections, questions, snark
- The output is a **Decision Brief**: verdict, the single next action, each objection with the exact question to ask 5 real users, kill-criteria (what a real user would have to say to kill the objection), and a silence analysis explaining why the majority left without engaging

There's also an **Investor Swarm mode** — stress-tests fundability, surfaces likely partner-meeting questions, flags missing proof points.

**What it is NOT:**

- Not a prediction engine. It cannot tell you your startup will succeed.
- Not a research replacement. Synthetic reactions are not user interviews.
- Not a score. There is no 7.4/10.
- Not accurate by definition. AI personas are wrong sometimes. We say so on every screen.

The honest framing is this: it's a **pre-interview filter**. Kill the bad positioning before it costs a real conversation.

Free. No signup to run a roast. Runs for $0 on local Ollama. AGPL-3.0 on GitHub.

Now, per the spirit of the product — I'd genuinely like this community to run a pitch through it and tell me where the Decision Brief was wrong. That feedback is more useful to me than upvotes.

swarmie.vercel.app | github.com/hp-8/swarmie

— Harsh

---

## Gallery Shot List (5 images)

1. **Hero — homepage with swarm canvas.** The live animated swarm canvas mid-run. Shows the "Roast your startup with 500 AI users." headline and the glowing agent dots. Dark background. No UI chrome — just the atmosphere.

2. **The Decision Brief.** Full Decision Brief output: verdict chip ("sharpen"), confidence band, "do this next" block, one complete objection card showing the category, example quote, "ask 5 users" question, kill signal, and fix. This is the core product value — make it legible.

3. **The Swarm in Motion.** The Watching screen mid-run. Brain graph or reaction stream with the counter ticking up. Shows 300+ agents reacting live. Add an annotation: "silent agents cost zero tokens."

4. **Inside the Neuron.** The neuron drawer opened on a specific agent — shows the persona card, the agent's segment, tone, biases, and their actual reaction text. Demonstrates the depth behind each dot.

5. **Investor Swarm mode.** The pitch input screen with Investor Swarm tab selected. Shows the "stress-test fundability" framing and the deck upload dropzone. For the investor audience.

---

## Prepared Replies to Likely Comments

---

### "Isn't this just asking ChatGPT?"

Partly, yes — and the honest answer matters. Asking a single LLM "does this idea work?" averages everything into mush: it hedges, it says "it depends," it wants to be helpful. Swarmie does something structurally different: it forces 100–500 personas to react independently, with different biases, different skepticism thresholds, and different reasons to leave. Silence is explicitly modeled — agents that ignore the pitch produce no output at all, because ignoring is free and real audiences do the same. The output is a falsifiable decision brief with kill-criteria you can test with 5 real humans. And every screen discloses it's synthetic. We don't call it research.

---

### "Synthetic users are useless. You need real feedback."

Agreed — eventually. Swarmie is a pre-interview filter, not a research replacement. We say that on the homepage, in the app, and in the first-comment. The use case isn't "skip user interviews." It's "before you spend 5 hours recruiting and scheduling 5 user interviews, spend 60 seconds finding out whether your current framing will confuse them on the first sentence." If the swarm can't explain what your product does, neither can a real prospect. Kill that problem first. Then talk to humans.

---

### "How is this different from [idea validator X]?"

Most validators return a score. That score is optimized to make you feel good enough to keep using the product. Swarmie returns the objection you're avoiding and a falsifiable kill-criteria: the specific thing a real user would have to say to prove the objection is fatal. That's a different design goal. We also disclose every limitation aggressively — wrong sometimes, agreeable too often, not a research replacement. We think the honesty is the moat, not the swarm.

---

### "What does this cost? What's the pricing?"

Free to run on local Ollama — zero cost, zero API key. The hosted version at swarmie.vercel.app is free with a hard cost ceiling on our end. We're not currently charging. When that changes, it will be transparent and not a surprise. The full source is AGPL-3.0 on GitHub if you want to self-host with your own keys.

---

### "Why AGPL? That's restrictive."

Intentionally. AGPL means if you build a service on top of Swarmie, you have to open-source the modifications. We want the core to stay open and improvable by anyone, not absorbed into a proprietary product. If you want to use it in a closed commercial context, reach out — we can talk. The goal is to keep the tool available and honest, not to gate it.

---

### "Can the swarm be wrong? What's the error rate?"

Yes, it can be wrong — and we don't know the error rate in a rigorous sense. AI personas carry the biases of their training data. They can miss niche markets, overweight obvious objections, or surface noise instead of signal. We are explicit about this on every screen. The correct use of Swarmie is not "the swarm said X, therefore X is true." It's "the swarm flagged X as a possible objection — let me go ask 5 real users whether X is actually a problem." The kill-criteria in the Decision Brief are designed for exactly that: take the output to humans, run the test, and let the real conversation override the simulation.

---
