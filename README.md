<div align="center">

# 🐝 Swarmie

**Roast your startup with 500 AI users in 60 seconds.**

Founder validation through grounded agent simulation. Upload a pitch, describe your ICP, and watch a swarm of AI users react like real people would — with objections, questions, snark, and silence.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](./CONTRIBUTING.md)
[![Status: Alpha](https://img.shields.io/badge/Status-Alpha-orange.svg)]()

</div>

---

## Why Swarmie

Before you spend $10k on user interviews or burn 6 months on the wrong positioning, **find your top 3 objections in 60 seconds**.

Swarmie isn't a replacement for talking to real users. It's a **pre-interview filter** — kill 17 bad positionings before you embarrass yourself with the 18th.

**Built for**:
- Pre-launch founders validating a pitch
- PMs A/B testing positioning before a launch
- Marketers stress-testing landing-page copy
- Indie hackers without a panel of real users to call

---

## How It Works

1. **Upload** your pitch, deck, or one-pager
2. Swarmie extracts ICP signals → builds a swarm of agents with distinct personas, biases, and tone
3. Agents react: comment, ignore, ask questions, raise objections — like a real Reddit / HN / ProductHunt thread
4. You get a **PMF scorecard**: top objections, sentiment split, ICP fit, messaging gaps

Powered by:
- **[OASIS](https://github.com/camel-ai/oasis)** (CAMEL-AI) — the underlying social simulation engine
- **[Zep](https://www.getzep.com/)** — agent long-term memory and knowledge graph
- Any OpenAI-compatible LLM (OpenAI, Anthropic via OpenRouter, Groq, Together, **Ollama for local/free**)

---

## Quick Start

### Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Node.js | 18+ | `node -v` |
| Python | 3.11 – 3.12 | `python --version` |
| uv | latest | `uv --version` |

### Setup

```bash
# 1. Clone
git clone https://github.com/hp-8/swarmie.git
cd swarmie

# 2. Configure
cp .env.example .env
# edit .env — add your LLM_API_KEY and ZEP_API_KEY

# 3. Install everything
npm run setup:all

# 4. Run
npm run dev
```

Open **http://localhost:3000**. Backend runs on `:5001`.

### Docker

```bash
cp .env.example .env
docker compose up -d
```

---

## Status

🚧 **Alpha.** Forked from [MiroFish](https://github.com/666ghj/MiroFish) — a Chinese-language swarm-prediction engine — and pivoted toward founder validation. The core simulation works end-to-end. The founder-focused UX, grounded ICP corpora, and backtest calibration are actively in development.

See **[ROADMAP.md](./ROADMAP.md)** for what's coming.

---

## What's Different from MiroFish

Swarmie keeps MiroFish's strong sim core (OASIS + Zep + multi-step pipeline) but pivots:

| Dimension | MiroFish | Swarmie |
|-----------|----------|---------|
| **Audience** | General prediction (news, novels, policy) | Pre-launch founders |
| **Input** | Any seed document | Pitch / deck / one-pager |
| **Output** | Long-form prediction report | PMF scorecard + objection clusters |
| **Realism** | LLM personas from raw graph | Grounded in real Reddit/HN/PH corpora (WIP) |
| **Calibration** | None | Public backtest scoreboard (WIP) |
| **Language** | Chinese-first | English-first |
| **Cost focus** | Frontier models | Tiered routing + local-model default |

---

## Contributing

We need help on:
- **ICP corpora** — scrape + tag Reddit/HN comments by founder-relevant segments
- **Backtest cases** — pick known startups (hits + flops), measure prediction accuracy
- **Cost optimization** — tiered model routing, archetype clustering, prompt caching
- **Founder UX** — make the "upload pitch → see report" flow brutally simple

See **[CONTRIBUTING.md](./CONTRIBUTING.md)**.

---

## License

**AGPL-3.0**. See [LICENSE](./LICENSE).

Inherited from upstream MiroFish. Network-use clause applies — if you host Swarmie as a service, you must publish your modifications.

For commercial licensing or hosted-service exceptions, open an issue.

---

## Acknowledgments

Swarmie stands on the work of:

- **[MiroFish](https://github.com/666ghj/MiroFish)** by 666ghj and team — upstream codebase
- **[OASIS](https://github.com/camel-ai/oasis)** by CAMEL-AI — agent social simulation engine (Apache 2.0)
- **[Zep](https://github.com/getzep/zep)** — agent memory + knowledge graph
- **[Shanda Group](https://www.shanda.com/)** — strategic support for original MiroFish

See **[NOTICE](./NOTICE)** for full attributions.
