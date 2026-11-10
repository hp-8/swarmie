# Swarmie — PRODUCT.md

register: brand   <!-- marketing surfaces (Home) = brand; app screens (PitchInput/Watching/Result) = product -->

## Users
Pre-launch founders, indie hackers, and PMs validating positioning before they spend on user interviews. Technical enough to read a cost estimate; impatient with hype. They arrive skeptical ("isn't this just asking ChatGPT?") and convert when they see the *decision* the tool hands back, not a vanity score.

## Product purpose
Paste a pitch → a panel of 100–500 synthetic reviewers reacts like a Reddit/HN/PH thread → the founder gets a **decision memo**: a recommendation (ship it / sharpen positioning / wrong audience / rethink the core) with confidence, what's working, hidden risks the founder likely hasn't considered (each with why it's easy to miss and a cheap test), the objections each with an exact interview question + kill criteria + fix, a path forward, why the silent majority scrolled past, and per-segment fit. A pre-interview filter: find the problems you can't see before they cost real conversations or code.

## Brand / tone
**Honest advisor.** The voice of a trusted partner writing the memo before the Monday meeting: plain, exact, anti-hype. Names problems in proportion to the evidence, never flatters a weak idea, never catastrophizes a fixable one, and always leaves a realistic next step. Founders use it for real decisions, not a dopamine hit, so it must never demotivate for effect. The honesty is the brand: it openly discloses the reviewers are synthetic, not real users.

Copy: "convene the panel", "decision memo", "recommendation", "finding". Avoid "roast", "kill", "brutal" in the interface; the product name and URLs may keep legacy wording.

## Anti-references (do NOT look like these)
- Generic SaaS-cream landing with icon-card triples
- Purple/blue "AI" gradients, neon-on-black crypto, navy-and-gold fintech
- Hype copy: unleash, revolutionize, next-gen, seamless, transformative
- The hero-metric template (big number + small label + gradient)
- The previous midnight+coral glow look (near-black, one warm accent, italic display serif, tracked mono labels): retired 2026-11-10 as a generic AI-tool default.
- Editorial-magazine cliche (display-italic + tracked mono eyebrows + ruled separators) and paperwork for its own sake.

## Strategic principles
- **Honesty over hype.** Always disclose synthetic agents. Trust is the moat.
- **Conversion = "convene the panel."** Every marketing surface drives one action: submit a pitch and run it. Show the aha (a real sample memo) as proof before asking.
- **Cost-aware.** $0 on local Ollama, capped on hosted — say so, it's real.
- **The decision is the product; the swarm is the evidence.** Lead with the memo's findings. The crowd (all reactions, traceable) backs them up as exhibits.

## Visual direction (2026-11-10)
**Investment committee memo**, built as a precision instrument: white bond-paper ground, near-black ink, slate secondary, red reserved for risk flags. Numbered findings, exhibits, margin flags. Density of real findings and exact numbers, not formality. Craft bar: Co-Star (stark, blunt), Boardy (calm, human), Monday.com (scannable clarity).

## Positioning (anti-wrapper)
Never sell prediction; it can't simulate a real market and would just be a wrapper.
- **Synthetic swarm = the funnel** — instant, viral, honest red-team. Surfaces blind-spot objections + the questions to ask real users.
- **Real signal + real-user bridge = the moat** — mining actual X/Reddit/HN chatter is synthesis of real data, not simulation.
- **Calibration = the proof** — earn accuracy claims (votes, backtest), never assert them.
Claim usefulness, not realism. Lead with real, hook with synthetic.

**Core principle — every swarm is decision stress-testing, not roleplay.** Never pretend to be reality. Not "talk to AI investors" but "stress-test fundability against patterns from real investor behavior." Not "predict your launch" but "surface the questions, objections, and risks likely to emerge, from historical community behavior." The simulation is the interface; the intelligence is the product. Ground in real signal (Reddit, HN, reviews, launch threads) over time so synthetic reactions stay calibrated against reality.

## Shipped (current state)
- 60s pipeline: parse → archetypes → async swarm → decision brief, streamed over SSE.
- Decision-brief output: verdict + confidence + next action; per-objection user-test, kill-criteria, fix.
- Silence analysis: sampled, capped "why N% scrolled past" reasons, mapped to fixes.
- Per-agent chat; two-tier model routing + Gemini fallback; hard cost ceiling; Ollama-for-free.
- Two feedback layers (per-objection votes + product feedback) → Supabase, feeding calibration.
- Atmospheric, fully-responsive marketing site (canvas swarm hero); PDF export; Supabase analytics.

## Monetization directions (not built yet)
Free 60s text brief stays the viral top-of-funnel. Paid bets, in rough priority:
- **Live voice interview / panel** (realtime API) — talk to personas, they interrupt and object.
- **Real-user bridge** — recruit 5 real ICP users to test the kill-criteria the sim generated (marketplace cut).
- **Live grounding** — objections cite current Reddit/HN/review chatter.
- **Positioning monitor** (subscription) and **A/B positioning lab** (parallel runs).
- Adjacent swarms: **investor mode**, **launch dress rehearsal**, **landing/deck vision**.
