# Swarmie — PRODUCT.md

register: brand   <!-- marketing surfaces (Home) = brand; app screens (PitchInput/Watching/Result) = product -->

## Users
Pre-launch founders, indie hackers, and PMs validating positioning before they spend on user interviews. Technical enough to read a cost estimate; impatient with hype. They arrive skeptical ("isn't this just asking ChatGPT?") and convert when they see the *decision* the tool hands back, not a vanity score.

## Product purpose
Paste a pitch → a swarm of 100–500 AI personas react like a Reddit/HN/PH thread → the founder gets a **decision brief**: a verdict (ship / sharpen / wrong-audience / kill), the top objections each with an exact interview question + kill-criteria + fix, why the silent majority scrolled past, and per-segment fit. A pre-interview filter — kill bad positionings before they cost a real conversation.

## Brand / tone
Blunt, honest, anti-hype. "Doesn't lie nicely." Technical but warm. The honesty is the brand: it openly discloses the agents are synthetic, not real users. Atmospheric, late-night, tactile — a tool you run at 1am to find the objection you're avoiding.

## Anti-references (do NOT look like these)
- Generic SaaS-cream landing with icon-card triples
- Purple/blue "AI" gradients, neon-on-black crypto, navy-and-gold fintech
- Hype copy: unleash, revolutionize, next-gen, seamless, transformative
- The hero-metric template (big number + small label + gradient)
- Note: the editorial-magazine lane (display-italic + mono labels + ruled separators) is saturated in 2026 — BUT Swarmie's midnight+coral atmospheric identity is already committed; preserve it, push it toward atmosphere, don't swap lanes.

## Strategic principles
- **Honesty over hype.** Always disclose synthetic agents. Trust is the moat.
- **Conversion = "run a roast."** Every marketing surface drives one action: paste a pitch and run it. Show the aha (the decision brief) as proof before asking.
- **Cost-aware.** $0 on local Ollama, capped on hosted — say so, it's real.
- **The swarm is the unfair asset.** The living brain-graph visual is unique; lead with it, don't bury it.

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
