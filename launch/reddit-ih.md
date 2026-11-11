# Swarmie V2: Reddit / Indie Hackers Launch Posts

---

## (a) r/SideProject Post

**Title:** Swarmie v2: a panel of AI reviewers reads your startup pitch and writes a decision memo. Small reviews free, no signup

---

I shipped V2 of Swarmie.

You paste a pitch. A panel of AI reviewers reads it the way a Reddit, HN or Product Hunt thread would. Some object, some ask questions, and a lot of them scroll past without a word, because real audiences do.

In about a minute you get a decision memo:
- A verdict (ship it / sharpen / wrong audience / rethink the core)
- What's working
- Hidden risks you didn't mention
- The objections, with the reactions behind each one
- A path forward, with fixes to try this week

New in V2: Investor reviews (upload your deck, get the questions a partner will ask) and Launch reviews (how HN, PH and Reddit will react on launch day). V1 was harsh for the sake of it; V2 is tuned to neither flatter nor pile on.

**Disclaimer:** the reviewers are AI. They're wrong sometimes and this doesn't replace talking to users. It's a filter for before those conversations.

**Pricing:** small reviews (20 reviewers) are free and unlimited, no signup. Packs from $5 unlock 500-reviewer panels, Investor and Launch reviews and PDF export. Open source (AGPL-3.0) and free to self-host on Ollama.

Live: swarmie.harshpatadia.com
GitHub: github.com/hp-8/swarmie

Tell me where it gets your pitch wrong.

---

## (b) Indie Hackers Post

**Title:** I rebuilt my pitch-feedback tool after it got too harsh. Here's what V2 does differently

---

Idea validators fail in one of two ways. Most flatter you: "strong market opportunity", "clear value proposition". My V1 failed the other way. It was so blunt that founders could dismiss it as negative and move on. Either way, the useful thing gets lost: the specific risk your customer would raise, and what to test next.

**What Swarmie does**

You paste your pitch. Swarmie pulls out the ICP, problem, solution, pricing, competitors and traction, then convenes a panel of AI reviewers (20 free, up to 500 with a pack), each with its own background, tone and biases. Reviewers can scroll past without engaging, which costs nothing, the same way most real readers do. The ones who stop leave reactions.

**What V2 changed**

The output is now a decision memo:
- **Verdict**, with confidence
- **What's working:** so you know what not to break
- **Hidden risks:** things the panel spotted that your pitch doesn't address
- **Objections**, backed by exhibits (the actual reactions)
- **Path forward:** fixes to try and what to test this week

To keep it honest in both directions, there's an eval suite. An LLM judge scores the full memo on six dimensions, and trap pitches check whether it flatters a weak pitch, piles onto a strong one, or misses a risk I planted. Every change to the memo runs against it.

Two new review types: **Investor** (deck upload, likely partner questions, missing proof points) and **Launch** (go / sharpen / hold before you post anywhere).

**Pricing, plainly**

Small Validate reviews are free and unlimited, no account. Packs are for the expensive runs: $5 for 5 full reviews, and at launch price for the first 100 buyers, $15 for 20 or $49 for 100. No subscription; a failed review refunds its credit.

**The honest part**

The reviewers are synthetic and share one model's biases. Treat a memo as the question to bring to five real people, not as the answer.

**The tech**

- Async LLM panel, two-tier routing (fast model for reactions, larger for synthesis)
- Silent reviewers make zero LLM calls
- Hard per-run cost cap on hosted runs
- AGPL-3.0, $0 on local Ollama

swarmie.harshpatadia.com | github.com/hp-8/swarmie

If you run a real pitch through it, tell me where the memo was wrong. That's worth more to me than upvotes.

---

## (c) Concierge Reply Template

*For replying to someone's "feedback on my idea?" post, after you've actually run their pitch. Lead with their memo, then disclose. No pushiness.*

### Reddit-casual variant

Ran your pitch through a tool I built. The memo flagged two things:

**[HIDDEN RISK: paste from the memo, e.g. "Nothing says why a team would switch from the spreadsheet they already use."]**

**[OBJECTION: paste from the memo, e.g. "Several reviewers stalled on price: there's no anchor."]**

It also liked **[WHAT'S WORKING: e.g. "the one-line problem statement"]**, so I'd keep that.

Disclosure: that's from Swarmie (swarmie.harshpatadia.com), AI reviewers, not real users. A filter, not validation. If those two land, worth asking a few real people before the next draft.

### Discord-casual variant

Hey, I ran your pitch through Swarmie (a tool I built, AI reviewers, not real people). Top two flags:

**[HIDDEN RISK]**
**[OBJECTION]**

It's a simulation and it's wrong sometimes, but if those ring true, worth fixing before the next round of real feedback. Free to try on a revised version: swarmie.harshpatadia.com
