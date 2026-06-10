# Swarmie Launch Checklist — Week of 2026-06-10

Goal: **100 users in 7 days.** One conversion metric: completed roasts (Supabase `runs` count, unique by anon id).
Everything below serves one loop: **see it → run it → share it → next founder sees it.**

---

## 1. Pre-flight — safety (BLOCKING, do first)

- [ ] Rate limit `/api/roast` (per-IP, e.g. 5 runs/hour) — no net today
- [ ] Lock CORS to prod origin (`backend/app/__init__.py`, currently `*`) — tech_debt P0-3
- [ ] Verify `ROAST_MAX_COST_USD` cap fires mid-run (test with tiny cap)
- [ ] Set a global daily spend ceiling on the LLM provider dashboard (independent of app cap)
- [ ] Confirm Gemini fallback path works (kill primary key locally, run a roast)
- [ ] Friendly error states: LLM down / cost cap hit / malformed pitch — no raw stack traces
- [ ] Supabase: check row limits / free-tier quotas survive ~500 runs
- [ ] Add one line to site footer/ToS: pitches stored, used only in aggregate for calibration, never shared or sold
- [ ] `./ci-local.sh` green before every push

## 2. Pre-flight — product (the viral mechanics)

- [ ] **Share-card PNG** — auto-generated per result: verdict + confidence + top objection + swarm visual + URL. Doubles as OG image so pasted links unfurl. *(~1 day — the single highest-leverage build)*
- [ ] OG/Twitter meta tags on result pages point at the share card
- [ ] **Email-me-my-brief** field on result page (optional, post-result) → the only retention/list asset we'll have *(~2h)*
- [ ] **Famous-roasts gallery** — pre-run 6–8 known startups (Juicero, Quibi, WeWork, Theranos pitch-as-written, + 2 currently-hyped AI startups), static page `/roasts` *(~half day, mostly pipeline runs)*
- [ ] **Dogfood gate:** run Swarmie's own pitch through Swarmie. If the brief doesn't sting, fix synthesis prompts before any launch. Re-run eval harness on golden set after changes.
- [ ] Mobile pass on result page + share card (most Reddit/X clicks are mobile)
- [ ] Light concurrency check: 5 simultaneous SSE runs don't fall over

## 3. Assets (write once, remix per channel)

- [ ] **Core copy block** — one paragraph, anti-wrapper angle: *"Validators give you a score. Swarmie hands you the objection you're avoiding + the exact question to ask 5 real users. Synthetic, disclosed, free, open-source, $0 on Ollama."*
- [ ] X thread draft (5–8 posts): hook = own roast verdict screenshot → how it works → famous roast → swarm video → CTA
- [ ] PH kit: tagline (<60 chars), 5 gallery images (share cards + brief screenshot), 14s promo video, maker first-comment (story + honesty angle), topics picked
- [ ] Show HN draft: title `Show HN: Swarmie – open-source AI swarm that roasts your startup (free on Ollama)` + first comment covering: cost engineering, ~60% silent agents = zero tokens, AGPL, synthetic-disclosure stance
- [ ] Reddit/IH variants — story-first, no link-drop tone; lead with what the roast got right/wrong about our own pitch
- [ ] 3 famous-roast screenshots cropped for replies/comments
- [ ] DM list: 20–30 founder friends / mutuals — ask them to *run a pitch and tell us where it's wrong* (genuine usage, not upvote begging)
- [ ] PH maker account active this week (comment on others' launches daily)
- [ ] Optional: custom domain (`swarmie.app`-style, ~$10) — vercel.app subdomain reads alpha-grade on PH

## 4. Channel sequence

| Day | Move |
|-----|------|
| **D1 (Wed)** | Safety list (§1) + start share card |
| **D2 (Thu)** | Finish share card + email capture + gallery. Dogfood gate. Write assets (§3) |
| **D3 (Fri)** | Soft launch: X thread, r/SideProject, r/alphaandbetausers, Indie Hackers post. DM the 20–30 list |
| **D4–5 (Sat–Sun)** | **Concierge distribution:** find "feedback on my idea" posts (r/startups, r/Startup_Ideas, r/SaaS, IH, BuildSpace + SaaS Builders Hub Discords). Run *their* pitch, reply with top 2 objections + link, disclose it's Swarmie. Target 10/day. Plus: PH launch **Saturday** (weekend = less competition); submit to launch directories same day |
| **D6 (Mon)** | Follow-ups, second X post (early numbers / best roast of the weekend), keep concierge replies going |
| **D7 (Tue)** | **Show HN** (weekday morning ET = HN's best window). All hands on comment replies |

## 5. Launch-day ops (PH day + HN day)

- [ ] Reply to every comment < 2h, founder voice, concede valid criticism (the brand is honesty — "fair hit" beats deflection)
- [ ] Pin cost/abuse dashboard + Supabase funnel in a visible tab all day
- [ ] Have the "isn't this just ChatGPT?" answer pre-written: *partly yes — the value is the decision brief + disclosed synthesis + what we do with the aggregate data (calibration). We never claim accuracy we haven't measured.*
- [ ] Screenshot + repost the best community roasts (with permission)
- [ ] If something breaks: status note on site within 15 min, fix, post-mortem honesty in-thread

## 6. Post-launch (D8)

- [ ] Retro vs kill-criteria (§7) — written, honest, in this file
- [ ] Email the captured list: best objections of week 1 + what we're fixing
- [ ] Keep 3 concierge replies/day going (compounding channel, not a launch stunt)
- [ ] Log every "I'd pay for X" comment verbatim → feeds paid-tier priority

## 7. Metrics & kill-criteria (decide BEFORE launch, judge on D8)

| Metric | Target | Miss means |
|--------|--------|------------|
| Completed roasts | 100 | distribution failed → channel retro, not feature work |
| Aha-rate (observable reactions: "oof"/"fair"/screenshot) | ≥30% of observed | synthesis quality — fix prompts before more traffic |
| Share-rate (unprompted posts/sends of result) | ≥10% | share card weak — iterate artifact, not pipeline |
| Return or referral within 7d | ≥15% | one-shot tool confirmed → lean harder into investor-prep wedge |
| Concierge sales ($49–99) | ≥2 | no WTP at this wedge → pivot monetization to investor prep only |

**Miss all → don't iterate the roast; pivot wedge or kill. Miss two → fix quality before buying more attention.**

---

*Owner: Harsh. Status: pre-launch. Update checkboxes in place; retro goes at the bottom of this file on D8.*
