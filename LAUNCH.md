# Swarmie Launch Checklist — Week of 2026-06-10

Goal: **100 users in 7 days.** One conversion metric: completed roasts (Supabase `runs` count, unique by anon id).
Everything below serves one loop: **see it → run it → share it → next founder sees it.**

---

## 1. Pre-flight — safety (BLOCKING, do first)

- [x] Rate limit `/api/roast` (per-IP 5/h, chat 30/h; env-tunable, `RATE_LIMIT_*`) ✅ 2026-06-11
- [x] Lock CORS to prod origin (`CORS_ORIGINS` allowlist) ✅ 2026-06-11
- [x] Cost-cap cancellation unit-tested ✅ — still do one LIVE check: tiny `ROAST_MAX_COST_USD`, real run. **Note 2026-06-11: cap was silently dead — `deepseek/deepseek-v4-flash` missing from `_PRICING`, every run priced $0. Fixed (real OpenRouter rates added); live check now meaningful — do it**
- [ ] Set a global daily spend ceiling on the LLM provider dashboard (independent of app cap) — **Harsh, 5 min**
- [ ] Confirm Gemini fallback path works (kill primary key locally, run a roast)
- [x] Friendly error states: 429 + catch-all 500 return clean JSON `{error}`; tracebacks stay server-side ✅ 2026-06-11
- [ ] **Deploy envs (Render):** set `CORS_ORIGINS`, leave `RATE_LIMIT_ENABLED=true` — without this the new code defaults are fine, but verify after deploy
- [ ] Supabase: check row limits / free-tier quotas survive ~500 runs
- [ ] Add one line to site footer/ToS: pitches stored, used only in aggregate for calibration, never shared or sold
- [ ] `./ci-local.sh` green before every push

## 2. Pre-flight — product (the viral mechanics)

- [x] **Share-card PNG** — "↑ share card" on Result: 1200×630 canvas PNG (verdict + confidence + top objection + dot-swarm + URL + "synthetic users · disclosed"), Web Share on mobile ✅ 2026-06-11
- [x] OG/Twitter meta — already complete in index.html (poster + video + summary_large_image); per-result dynamic OG = post-launch (SPA, needs edge fn) ✅
- [~] **Email capture** — SharpenPanel email-gate (2nd sharpen) already captures emails; dedicated "email-me-my-brief" field still optional, not blocking
- [x] **Famous-roasts gallery** — `/roasts` SHIPPED with REAL data ✅ 2026-06-11: 8 pitches × 100 agents through live pipeline (Quibi=kill, 7×sharpen; quotes are exact agent output, verified against run JSONs). Swarmie self-roast included as card 8
- [x] **Dogfood gate:** PASSED ✅ 2026-06-11 — verdict sharpen/med; top objection "a fancier way to confirm my own bias"; kill signal: 3/5 founders call it "a bot with different temperature settings". It stings; output now in launch copy
- [ ] Mobile pass on result page + share card (most Reddit/X clicks are mobile)
- [ ] Light concurrency check: 5 simultaneous SSE runs don't fall over

## 3. Assets (write once, remix per channel)

- [x] **Core copy block** → `launch/core-copy.md` ✅
- [x] X thread draft → `launch/x-thread.md` ✅ — all claims now REAL run output (dogfood + famous batch, 2026-06-11); Post 5 filled with Quibi/Theranos quotes
- [x] PH kit → `launch/producthunt.md` (taglines, description, maker comment, 6 prepared replies) ✅ — gallery images still need capturing
- [x] Show HN draft + 5 prepared answers → `launch/show-hn.md` ✅ — placeholder claims replaced with real dogfood output + accurate cost-cap mechanics
- [x] Reddit/IH variants + concierge reply templates + DM templates → `launch/reddit-ih.md`, `launch/dm-template.md` ✅
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

## Platforms — triaged (18 → 3 tiers; don't spread thin)

**Tier 1 — active channels (real effort, real conversations; the week lives here):**
| Platform | Play |
|---|---|
| Reddit (r/SideProject, r/alphaandbetausers, r/startups, r/Startup_Ideas, r/SaaS) | soft-launch posts + concierge replies (run THEIR pitch) |
| Indie Hackers | build-story post + feedback-thread concierge replies |
| X (Twitter) | launch thread + daily best-roast screenshots |
| Product Hunt | Saturday launch, full kit ready in `launch/` |
| Hacker News | Show HN Tuesday, engineering angle |

**Tier 2 — directory batch (one sitting, ~2h total, backlinks + drip traffic; do D4 while PH runs):**
BetaList · Uneed · SaasHub · AlternativeTo (list as alternative to ValidatorAI/IdeaProof — free positioning) · Launching Next · StartupBase · Orynth (verify what it is first) · "Side Project Ideas"-type listings. All need: logo 240×240, one-liner, short desc, 2–3 screenshots — see assets below. Submit once, never babysit.

**Tier 3 — post-launch / SEO drip (NOT this week; each is a content channel, not a launch channel):**
- Quora + Medium — answer/write "how to validate a startup idea" evergreen pieces linking the famous-roasts gallery (week 2+)
- LinkedIn — investor-swarm angle for the fundraising audience (week 2, pairs with first paid offer)
- TikTok — only if the 14s promo repurposes for free; zero new production this week
- Facebook groups — skip; mod-hostile to tools, wrong density

## Things we need before launching:

1. **Logo** — have `favicon.svg` + `icon.png`; need one 240×240+ square PNG export for directories *(15 min, Harsh)*
2. **One-liner** — ✅ done: "Roast your startup with 500 AI users in 60 seconds." (`launch/core-copy.md` has 3 variants)
3. **Short description** — ✅ done: PH ≤260-char block in `launch/producthunt.md`, reusable on every directory
4. ~~Pitch deck~~ — **cut.** No launch platform needs a deck; it's investor-outreach material. Don't build launch-blocking work that isn't launch-blocking.
5. **Product images** — capture after famous-roasts data lands: (a) share-card PNGs ×3, (b) decision-brief screenshot, (c) /roasts gallery shot, (d) swarm-watching shot. Promo poster + 14s video ✅ already exist
6. **Real dogfood run** — ✅ done 2026-06-11; output in x-thread Post 1, show-hn Answer 5, /roasts card 8
7. **Famous-roast real runs** — ✅ done 2026-06-11; 8 real runs in `famousRoasts.json`, batch cost < $0.10 total (~450k tokens at deepseek-v4-flash rates)

---

*Owner: Harsh. Status: pre-launch. Update checkboxes in place; retro goes at the bottom of this file on D8.*