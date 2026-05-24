<template>
  <div class="home">
    <header class="nav">
      <div class="brand">SWARMIE</div>
      <nav class="nav-links">
        <a href="https://github.com/hp-8/swarmie" target="_blank">GitHub ↗</a>
        <a href="#how-it-works">How it works</a>
        <router-link to="/new" class="primary-link">Run a roast</router-link>
      </nav>
    </header>

    <main>
      <section class="hero">
        <div class="tag">Open-source · Founder validation</div>
        <h1>
          Roast your startup<br />
          with <span class="accent">500 AI users</span><br />
          in 60 seconds.
        </h1>
        <p class="lede">
          Paste your pitch. We simulate a swarm of real-looking commenters who react
          like Reddit, HN, and ProductHunt would. Find the top 3 objections before
          burning real interviews on the wrong pitch.
        </p>
        <div class="cta-row">
          <router-link to="/new" class="cta-primary">Start a roast →</router-link>
          <a href="https://github.com/hp-8/swarmie" target="_blank" class="cta-secondary">View on GitHub</a>
        </div>
        <p class="disclaimer">
          Alpha. AI agents, not real users. Use as a pre-interview filter — not a replacement for real conversations.
        </p>
      </section>

      <section id="how-it-works" class="how">
        <h2>How it works</h2>
        <div class="steps">
          <div class="step">
            <div class="step-num">01</div>
            <h3>Paste your pitch</h3>
            <p>One-pager, deck text, landing-page copy. Whatever you'd show a user.</p>
          </div>
          <div class="step">
            <div class="step-num">02</div>
            <h3>Swarm reacts</h3>
            <p>100–500 agents with distinct personas, biases, and tones. Skeptics, lurkers, fans, trolls.</p>
          </div>
          <div class="step">
            <div class="step-num">03</div>
            <h3>Get the roast</h3>
            <p>PMF score, top objections, ICP fit, messaging gaps. Shareable card to tweet.</p>
          </div>
        </div>
      </section>

      <section class="stack">
        <h2>Built on open source</h2>
        <p class="stack-lede">
          Forked from <a href="https://github.com/666ghj/MiroFish" target="_blank">MiroFish</a>.
          Powered by <a href="https://github.com/camel-ai/oasis" target="_blank">OASIS</a> (CAMEL-AI)
          and <a href="https://www.getzep.com/" target="_blank">Zep</a>.
          Works with any OpenAI-compatible LLM — including local Ollama, free.
        </p>
        <p class="stack-cta">
          <a href="https://github.com/hp-8/swarmie" target="_blank">Read the code →</a>
        </p>
      </section>

      <footer class="footer">
        <span>Swarmie · open source · AGPL-3.0</span>
        <span>
          <a href="https://github.com/hp-8/swarmie" target="_blank">github.com/hp-8/swarmie</a>
        </span>
      </footer>
    </main>
  </div>
</template>

<script setup>
// Static landing page. No state required.
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: #0b0c10;
  color: #f4f4f5;
  font-family: 'Inter', system-ui, sans-serif;
}

.nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 32px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  position: sticky;
  top: 0;
  background: rgba(11, 12, 16, 0.85);
  backdrop-filter: blur(8px);
  z-index: 10;
}

.brand {
  font-weight: 800;
  letter-spacing: 0.2em;
  font-size: 14px;
}

.nav-links {
  display: flex;
  gap: 22px;
  align-items: center;
  font-size: 13px;
}

.nav-links a {
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
}
.nav-links a:hover { color: #fff; }

.primary-link {
  background: linear-gradient(90deg, #ff6b35, #f59e0b);
  color: #0b0c10 !important;
  padding: 8px 14px;
  border-radius: 6px;
  font-weight: 600;
}

main { max-width: 1080px; margin: 0 auto; padding: 0 32px; }

.hero { padding: 96px 0 80px; max-width: 760px; }
.tag {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
  padding: 6px 12px;
  border-radius: 999px;
  margin-bottom: 24px;
}

.hero h1 {
  font-size: 64px;
  font-weight: 800;
  line-height: 1.05;
  letter-spacing: -0.03em;
  margin: 0 0 28px;
}

.accent {
  background: linear-gradient(90deg, #ff6b35, #f59e0b);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.lede {
  font-size: 19px;
  line-height: 1.55;
  color: rgba(255, 255, 255, 0.65);
  max-width: 580px;
  margin: 0 0 40px;
}

.cta-row { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 28px; }

.cta-primary {
  background: linear-gradient(90deg, #ff6b35, #f59e0b);
  color: #0b0c10;
  font-weight: 700;
  padding: 14px 28px;
  border-radius: 10px;
  text-decoration: none;
  font-size: 16px;
  transition: transform 0.1s;
}
.cta-primary:hover { transform: translateY(-1px); }

.cta-secondary {
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #fff;
  padding: 14px 22px;
  border-radius: 10px;
  text-decoration: none;
  font-size: 16px;
}
.cta-secondary:hover { background: rgba(255, 255, 255, 0.04); }

.disclaimer {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  max-width: 500px;
  line-height: 1.55;
  margin: 0;
}

.how { padding: 64px 0; border-top: 1px solid rgba(255, 255, 255, 0.05); }
.how h2 {
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: rgba(255, 255, 255, 0.5);
  margin: 0 0 32px;
  font-weight: 600;
}

.steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
@media (max-width: 720px) { .steps { grid-template-columns: 1fr; } }

.step {
  padding: 28px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
}
.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #f59e0b;
  letter-spacing: 0.1em;
  margin-bottom: 14px;
}
.step h3 { font-size: 18px; margin: 0 0 8px; font-weight: 600; }
.step p { font-size: 14px; line-height: 1.55; color: rgba(255, 255, 255, 0.55); margin: 0; }

.stack { padding: 64px 0; border-top: 1px solid rgba(255, 255, 255, 0.05); }
.stack h2 {
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: rgba(255, 255, 255, 0.5);
  margin: 0 0 16px;
  font-weight: 600;
}
.stack-lede { font-size: 16px; line-height: 1.6; color: rgba(255, 255, 255, 0.7); max-width: 720px; margin: 0 0 16px; }
.stack-lede a, .stack-cta a { color: #f59e0b; text-decoration: none; border-bottom: 1px dashed rgba(245, 158, 11, 0.3); }
.stack-lede a:hover, .stack-cta a:hover { border-bottom-color: #f59e0b; }

.footer {
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding: 32px 0;
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}
.footer a { color: inherit; text-decoration: none; }
.footer a:hover { color: #fff; }
</style>
