# Swarmie — Reddit / Indie Hackers Launch Posts

---

## (a) r/SideProject Post

**Title:** I built a tool that roasts your startup pitch with 500 AI personas — free, open-source, no signup

---

Spent the last few weeks building Swarmie.

You paste a startup pitch. A swarm of 100–500 AI personas reacts like a Reddit/HN/Product Hunt thread — objections, questions, snark. Part of the swarm silently scrolls past without saying anything, because real audiences do that too.

In ~60 seconds you get a Decision Brief:
- Verdict: ship it / sharpen / wrong audience / kill
- The single next action
- Top objections, each with the exact question to test with 5 real users
- Kill-criteria (what a real user would need to say to prove the objection is fatal)
- Silence analysis: why the majority left without engaging

There's also an Investor Swarm mode that stress-tests fundability.

**Honest disclaimer:** The personas are AI-generated. They're wrong sometimes, agreeable too often, and this is not a replacement for real user research. It's a pre-interview filter — kill the bad positioning before it costs a real conversation.

Free. No signup. Runs for $0 on local Ollama. AGPL-3.0 on GitHub.

Live: swarmie.vercel.app
GitHub: github.com/hp-8/swarmie

Happy to hear where it breaks for you.

---

## (b) Indie Hackers Post

**Title:** I built Swarmie: 500 synthetic users roast your startup in 60 seconds (and no, it's not the wow tech — it's the objection you've been avoiding)

---

There's a particular kind of feedback you get from idea validators that is technically accurate and completely useless.

"Strong market opportunity." "Clear value proposition." "Consider pricing strategy."

It's not wrong. It's just formatted to not make you feel bad. And the one thing that would actually help you — the specific thing your ICP says when they see your pitch for the first time — gets laundered into "consider positioning."

I built Swarmie because I kept running into this problem when helping founders sharpen pitches. The gap between "validation tool" and "useful input" was almost always: the tool wouldn't tell you the specific objection, and it definitely wouldn't give you the falsifiable test to bring to a real user interview.

**What Swarmie does**

You paste your pitch text. Swarmie parses the ICP, problem, solution, and price from it, then spawns 100–500 AI personas — each with a distinct background, tone, and objection bias. Each persona can also just scroll past (zero LLM calls, zero cost — they don't engage, because real audiences don't either; how many ignore you depends on the pitch). The ones who stop post reactions: objections, questions, snark, upvotes.

The output is a Decision Brief:

- **Verdict** — ship it / sharpen / wrong audience / kill, with a confidence band
- **The single next action** — not a list of 12 things, one thing
- **Top objections** — ranked by frequency, each with:
  - The example quote from the swarm
  - The exact question to ask 5 real users ("At what monthly price would you stop evaluating this entirely?")
  - Kill-criteria: what a real user would need to say to prove this objection is fatal
  - Suggested fix to try first
- **Silence analysis** — why the majority left without engaging, and what to change

There's also an Investor Swarm mode: stress-tests fundability, surfaces likely partner-meeting questions, flags missing proof points, returns a fundability verdict.

**The thing I want to be honest about**

The personas are synthetic. They carry the biases of their training data. They're wrong sometimes. They can miss niche markets and overweight obvious objections.

The correct framing: Swarmie is a pre-interview filter, not a research replacement. If 400 out of 500 personas can't figure out what your product does from your pitch text, that's a real signal — not because they're right, but because real audiences read at the same speed and with the same attention span. Fix that problem before you bring the pitch to humans.

**The tech (briefly)**

- Async LLM swarm with two-tier model routing (fast model for reactions, larger model for synthesis)
- Silent ignores and upvotes cost zero LLM calls — models real-audience attention without paying for it
- Hard cost ceiling on the hosted version; Gemini fallback for rate limits
- Runs for $0 on local Ollama
- AGPL-3.0 — full source on GitHub

I ran Swarmie through Swarmie before launch (real run, not a hypothetical). Verdict: **sharpen**, medium confidence. The top objection the swarm wrote: *"a swarm of bots with 'distinct biases' is just a fancier way to confirm my own bias. i'll stick to cold emailing 10 real people."* The kill-criteria it handed me: if 3 of 5 founders say "it's just a bot with different temperature settings," the positioning is dead. 100% of the silent agents binned it as "seen this before — me-too AI tool."

That one landed. I haven't fully solved it. But at least I know exactly what question to bring to the next five conversations.

That's the idea.

swarmie.vercel.app | github.com/hp-8/swarmie

Would genuinely appreciate anyone who runs a real pitch through it and tells me where the brief was wrong. That's more useful to me than upvotes.

---

## (c) Concierge Reply Template

*Use this when replying to someone else's "give me feedback on my startup idea" post — after you've actually run their pitch through Swarmie. Open with their objections, then disclose. Zero pushiness.*

---

### Reddit-casual variant

---

Ran your pitch through a tool I've been building — here's what the swarm flagged as the top two friction points:

**[OBJECTION 1 — paste verbatim from the Decision Brief, e.g.: "Couldn't tell who the target customer is from the first sentence."]**

**[OBJECTION 2 — paste verbatim, e.g.: "Price anchor is missing — several personas stalled on 'how much does this cost?'"]**

Disclosure: those came from Swarmie (swarmie.vercel.app) — a synthetic AI swarm, not real users. Take it as a pre-filter, not validation. But if those two hit, worth asking a few real people the same question before the next draft.

---

### Discord-casual variant

---

Hey — I actually ran your pitch through Swarmie (a tool I built — synthetic AI personas, not real users) and these two things came up most:

**[OBJECTION 1 — e.g.: "The ICP isn't clear until the third paragraph — most personas stopped reading before that."]**

**[OBJECTION 2 — e.g.: "The pricing section raised more questions than it answered."]**

Full disclosure, it's a simulation — it's wrong sometimes. But if those two resonate, it might be worth addressing them before the next round of real feedback. Link if you want to try it on a revised version: swarmie.vercel.app

---
