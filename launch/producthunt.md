# Swarmie V2: Product Hunt Launch Kit

---

## Tagline Options (each < 60 chars)

1. **Find the problem you can't see yet.**
2. **A decision memo for your pitch. Not a score.**
3. **500 AI reviewers read your pitch in a minute.**

---

## Description (≤ 260 chars)

Paste your pitch. A panel of AI reviewers reads it like Reddit, HN and Product Hunt would. You get a decision memo: what's working, hidden risks, the objections behind them, and what to test this week. Small reviews free, no signup.

---

## Maker First Comment

I built Swarmie because idea validators lie nicely. You paste a pitch, get "8.1 / 10", feel better, and ignore the thing you already suspected. Three months later a real user says it out loud.

V1 fixed that by being blunt. V2 fixes the overcorrection: blunt for its own sake is just as useless. So the new **decision memo** opens with what's working, then names the risks you missed, shows the reactions behind every claim, and ends with fixes to try this week.

**What it does:**
- Convenes a panel of AI reviewers (20 free, up to 500 with a pack), each with its own background, bias and attention span
- Part of the panel scrolls past without a word, because real audiences do
- Writes a decision memo: verdict, what's working, hidden risks, objections, path forward, exhibits

**Three review types:**
- **Validate:** does the market care?
- **Investor:** would a partner take the meeting? Upload your deck.
- **Launch:** how will HN, PH and Reddit react on launch day? (Yes, I ran this launch through it.) [Only keep if true.]

**What it costs:** small Validate reviews are free and unlimited, no signup. Packs start at $5 for 5 full reviews. Launch prices for the first 100 buyers: Starter $15 for 20, Sprint $49 for 100. No subscription, and failed reviews are refunded automatically.

**What it is NOT:** a prediction engine, a research replacement, or market validation. The reviewers are AI and they are wrong sometimes. Use it to find the question to bring to five real people.

Open source (AGPL-3.0), free to self-host on Ollama.

Tell me where the memo is wrong. That's the feedback I want most.

---

## Gallery Shot List (5 images)
<!-- Recapture from V2 UI. launch/assets/ holds V1 screenshots (decision brief); don't use those. -->

1. **Home hero:** "Find the problem you can't see yet." with the sample memo beside it.
2. **Decision memo, top:** verdict, what's working, hidden risks.
3. **Exhibits close-up:** one objection with the reactions that back it.
4. **Review type picker:** Validate / Investor / Launch, Investor with a deck attached.
5. **Rate card:** Free vs packs, launch price visible.

---

## Prepared Replies to Likely Comments

### "Isn't this just asking ChatGPT?"
Partly, and fair to ask. One LLM call averages everything into a hedge. Swarmie makes up to 500 reviewers react independently, models the ones who scroll past, and the memo cites the reactions behind each claim so you can check it. We also run a fixed set of trap pitches (flattery bait, harshness bait, a planted hidden risk) every time we change the memo.

### "Synthetic users are useless. You need real feedback."
Agreed that you need real feedback. Swarmie is the step before it: it tells you which question to bring to five real people, so those conversations aren't wasted on things you could have caught yourself.

### "How is this different from other idea validators?"
No score. A memo with a verdict, the evidence behind it, and a next step. And it's tuned to neither flatter nor pile on.

### "What does this cost?"
Small reviews (20 reviewers, Validate) are free and unlimited, no signup. Packs: $5 for 5 full reviews; Starter $15 for 20 and Sprint $49 for 100 at launch price for the first 100 buyers ($25 and $82 after). Full reviews unlock 500-reviewer panels, Investor and Launch reviews, deck upload, PDF and share card. No subscription.

### "Why AGPL?"
So anyone who hosts a modified Swarmie has to publish the changes. The core stays inspectable, which matters for a tool that influences real decisions. Self-hosting is free.

### "Can the panel be wrong?"
Yes. The reviewers carry their training data's biases. The memo shows its evidence so you can judge it, and every memo says it's synthetic. Treat it as a filter, never as proof.
