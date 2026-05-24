# Contributing to Swarmie

First — thank you. Swarmie is early. Every PR matters.

## Where We Need Help (Most → Least)

### 1. ICP Corpora (highest impact)
We're building reusable "ICP packs" — tagged corpora of real social comments per founder-relevant segment.

- Pick a segment (e.g. *indie devs*, *B2B buyers*, *creators*, *PMs at Series A-C SaaS*)
- Scrape sources we trust (Reddit, HN, ProductHunt, GitHub issues)
- Tag with sentiment / objection-type / WTP signal
- Submit as a folder under `corpora/<icp-name>/` with a README

Anyone shipping a tagged 10k-comment ICP pack gets co-author credit on the launch post.

### 2. Backtest Cases
For Swarmie to be trustworthy, predictions must be measurable.

- Pick a known startup (a hit *or* a flop)
- Find real pre-launch pitch + real post-launch reception (Reddit/HN/PH threads)
- Add to `backtest/cases/<startup-name>/`
- Open a PR with the case + expected outcome

### 3. Cost Optimization
We default to local Ollama, but tiered model routing isn't built yet.

- Tier-1 cheap reactions (Haiku / Qwen-turbo / Llama-3.3 8B)
- Tier-2 deeper "influencer" agents (Sonnet)
- Tier-3 synthesis (Opus / Sonnet)

Anchor design in `backend/app/services/` — open an issue first to discuss approach.

### 4. Founder UX
The current UI is inherited from MiroFish and is *not* optimized for the "founder uploads pitch → sees PMF report" flow. Look at `frontend/src/views/Home.vue` and `Process.vue` first.

### 5. Docs, examples, screencasts
Underrated. Onboarding screencasts, blog posts, integration tutorials — all welcome.

---

## Dev Setup

See [README.md](./README.md#quick-start).

```bash
git clone https://github.com/hp-8/swarmie.git
cd swarmie
cp .env.example .env  # fill in keys
npm run setup:all
npm run dev
```

## Pull Request Process

1. Fork → branch → PR against `main`
2. Keep PRs small and focused. One concern per PR.
3. Reference the issue if one exists.
4. By submitting, you agree your contribution is licensed under AGPL-3.0.

## Code Style

- **Python**: PEP 8, type hints encouraged, `ruff` welcome
- **Vue/JS**: 2-space indent, single quotes, no unused imports
- Keep comments minimal — code should be readable on its own

## License of Contributions

All contributions are licensed under AGPL-3.0 (see [LICENSE](./LICENSE)).

## Code of Conduct

Be excellent to each other. Disagree on technical merit, not personal grounds. Harassment, discrimination, or bad-faith engagement gets you banned. No second chances.

## Questions?

Open a [GitHub Discussion](https://github.com/hp-8/swarmie/discussions) or an issue tagged `question`.
