<template>
  <div class="page">
    <!-- nav: floating pill, minimal -->
    <header class="nav">
      <router-link to="/" class="brand-mark">
        <span class="dot"></span>
        <span class="brand-text">SWARMIE</span>
      </router-link>
      <nav class="nav-right">
        <a href="https://github.com/hp-8/swarmie" target="_blank" class="ghost-link">github ↗</a>
        <router-link to="/new" class="h-btn is-accent">Run a roast</router-link>
      </nav>
    </header>

    <main>
      <!-- HERO · Marquee -->
      <section class="hero">
        <div class="hero-grid">
          <div class="hero-copy">
            <div class="hero-eyebrow">
              <span class="h-chip is-accent">Open source · Alpha</span>
              <span class="hero-sub-tag">A founder-validation funnel that doesn't lie nicely.</span>
            </div>

            <h1 class="hero-title h-display">
              Roast<span class="hero-dot">.</span><br />
              your startup<br />
              with <em class="hero-em">500&nbsp;AI&nbsp;users.</em>
            </h1>

            <p class="hero-lede">
              Paste the pitch. Watch a swarm of agents react like a Reddit thread,
              an HN comment section, and a ProductHunt launch page all yelled at it.
              Find the three real objections before you burn a single user interview.
            </p>

            <div class="hero-actions">
              <router-link to="/new" class="h-btn is-accent">Start a roast →</router-link>
              <a href="#truth" class="h-btn is-ghost">How it works</a>
            </div>

            <div class="hero-meta">
              <span><strong>~60s</strong> per run</span>
              <span class="hero-dot-sep">·</span>
              <span><strong>$0</strong> on local Ollama</span>
              <span class="hero-dot-sep">·</span>
              <span><strong>AGPL-3.0</strong></span>
            </div>
          </div>

          <aside class="hero-media">
            <figure class="hero-video">
              <video
                class="hero-video-el"
                autoplay
                muted
                loop
                playsinline
                preload="metadata"
                poster="/swarmie-promo-poster.jpg"
                aria-label="Swarmie product walkthrough — pitch, swarm reaction, insight"
              >
                <source src="/swarmie-promo.webm" type="video/webm" />
                <source src="/swarmie-promo.mp4" type="video/mp4" />
              </video>
            </figure>
            <figcaption class="hero-media-cap">
              <span class="hmc-label">Product walkthrough</span>
              <span class="hmc-meta">Pitch &rarr; swarm &rarr; insight</span>
            </figcaption>
          </aside>
        </div>
      </section>

      <!-- TRUTH band — honesty hook -->
      <section id="truth" class="truth">
        <p class="truth-line">
          <span class="h-eyebrow">A note before we start. <AiDisclosure aria-label="How this was generated" /></span>
          <span class="truth-text">
            These are AI agents. <em class="truth-em">Not real users.</em> They are wrong sometimes,
            agreeable too often, and they don't write your TAM check.
            Use this to <span class="warm">kill bad positionings before</span> they cost a real conversation —
            not to declare PMF.
          </span>
        </p>
      </section>

      <!-- HOW · three columns, but each is a different size (irregular grid) -->
      <section class="how">
        <header class="section-head">
          <span class="h-eyebrow">01 · the loop</span>
          <h2 class="section-title h-display">Three turns. Sixty seconds.</h2>
        </header>

        <div class="how-grid">
          <article class="how-card span-2">
            <div class="how-num">i.</div>
            <h3 class="how-title">Paste a pitch.</h3>
            <p class="how-copy">
              Landing-page copy, deck text, one-pager, half a tweet. Whatever you'd
              actually show a user. We parse it for ICP, problem, solution, pricing.
            </p>
          </article>

          <article class="how-card">
            <div class="how-num">ii.</div>
            <h3 class="how-title">Swarm reacts.</h3>
            <p class="how-copy">
              100–500 agents with distinct personas, biases, tones. Skeptics, lurkers,
              fans, trolls. Each one decides to post, comment, upvote, or scroll past.
            </p>
          </article>

          <article class="how-card span-2 is-accent-card">
            <div class="how-num">iii.</div>
            <h3 class="how-title">Get the roast.</h3>
            <p class="how-copy">
              PMF score. Top three objections. Per-segment fit. Messaging gaps. A
              quotable card you can throw on Twitter the moment you decide to ship.
            </p>
          </article>
        </div>
      </section>

      <!-- STACK · single column statement -->
      <section class="stack">
        <header class="section-head">
          <span class="h-eyebrow">02 · what's under</span>
          <h2 class="section-title h-display">Built on open work.</h2>
        </header>
        <p class="stack-copy">
          Swarmie is a thin orchestration on top of <a href="https://github.com/666ghj/MiroFish" target="_blank">MiroFish</a>,
          <a href="https://github.com/camel-ai/oasis" target="_blank">OASIS (CAMEL-AI)</a>, and
          <a href="https://www.getzep.com/" target="_blank">Zep</a>. Any OpenAI-compatible model works —
          OpenAI, Anthropic via OpenRouter, Groq, Together, DeepSeek, Qwen, or
          a local Ollama on your laptop for the price of electricity.
        </p>
        <p class="stack-cta">
          <a href="https://github.com/hp-8/swarmie" target="_blank" class="stack-link">
            Read the code →
          </a>
        </p>
      </section>

      <!-- FOUNDER · who built this + work-with-me -->
      <section class="founder">
        <div class="founder-grid">
          <div class="founder-left">
            <span class="h-eyebrow">03 · who made this</span>
            <h2 class="founder-name h-display">Harsh Patadia.</h2>
            <p class="founder-bio">
              I build for founders. Swarmie is the free version of how I think about
              early-stage validation — fast, brutal, focused on the objection you
              actually need to hear. If you want a human in the loop — to ship the
              MVP, sharpen the pitch, or prep the raise — that's the day job.
            </p>
            <div class="founder-actions">
              <a href="https://harshpatadia.space" target="_blank" class="h-btn is-accent">
                Work with me →
              </a>
              <a href="https://harshpatadia.space" target="_blank" class="h-btn is-ghost">
                harshpatadia.space
              </a>
            </div>
          </div>
          <aside class="founder-right">
            <span class="h-eyebrow">elsewhere</span>
            <ul class="founder-links">
              <li><a href="https://github.com/hp-8" target="_blank">github.com/hp-8</a></li>
              <li><a href="https://x.com/harshpatadia_" target="_blank">x.com/harshpatadia_</a></li>
              <li><a href="https://www.linkedin.com/in/harsh-patadia" target="_blank">linkedin.com/in/harsh-patadia</a></li>
              <li><a href="https://harshpatadia.space" target="_blank">harshpatadia.space</a></li>
            </ul>
          </aside>
        </div>
      </section>

      <!-- CTA STATEMENT -->
      <section class="cta">
        <h2 class="cta-title h-display">
          What would <em>500 strangers</em><br />
          say about it today?
        </h2>
        <router-link to="/new" class="h-btn is-accent cta-btn">Run a roast →</router-link>
      </section>

      <footer class="foot">
        <div class="foot-row">
          <span class="brand-mark"><span class="dot"></span><span class="brand-text">SWARMIE</span></span>
          <span class="foot-meta">v0.1 · alpha · AGPL-3.0</span>
        </div>
        <div class="foot-row foot-sub">
          <span>Built by <a href="https://github.com/hp-8" target="_blank">@hp-8</a>.</span>
          <a href="https://github.com/hp-8/swarmie" target="_blank">github.com/hp-8/swarmie</a>
        </div>
      </footer>
    </main>
  </div>
</template>

<script setup>
import AiDisclosure from '../components/AiDisclosure.vue'
</script>

<style scoped>
/* Hallmark · page: Home · macrostructure: Marquee Hero
 * archetypes: N5 floating pill · H1 marquee · S2 eyebrow+display · F2 irregular grid · Ft1 statement
 * theme: Midnight+coral (atmospheric)
 */

.page {
  min-height: 100vh;
  color: var(--ink);
}

/* NAV — floating pill */
.nav {
  position: sticky;
  top: var(--space-4);
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: var(--max-content);
  margin: var(--space-4) auto 0;
  padding: 10px 14px 10px 18px;
  background: color-mix(in oklch, var(--paper-2) 88%, transparent);
  border: 1px solid var(--rule);
  border-radius: var(--radius-pill);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}
.brand-mark {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.22em;
  color: var(--ink);
}
.brand-mark .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 14px var(--accent);
}
.nav-right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}
.ghost-link {
  color: var(--ink-2);
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  letter-spacing: 0.04em;
  transition: color var(--dur-fast) var(--ease-out);
}
.ghost-link:hover { color: var(--ink); }
.nav-right .h-btn { padding: 9px 16px; font-size: var(--text-sm); }

/* HERO */
.hero {
  max-width: var(--max-content);
  margin: 0 auto;
  padding: var(--space-6) var(--space-5) var(--space-7);
}
.hero-eyebrow {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: 0;
  flex-wrap: wrap;
}
.hero-sub-tag {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.06em;
  color: var(--ink-3);
}
.hero-title {
  font-size: clamp(40px, 5.2vw, 72px);
  line-height: 0.98;
  letter-spacing: -0.015em;
  font-weight: 600;
  font-variation-settings: 'opsz' 144, 'wght' 600;
  margin: var(--space-4) 0 var(--space-4);
  color: var(--ink);
  overflow-wrap: anywhere;
  min-width: 0;
}
@media (max-width: 1024px) {
  .hero-title { font-size: clamp(48px, 8vw, 88px); }
}
.hero-em {
  font-style: italic;
  color: var(--accent-bright);
  font-weight: 600;
}
.hero-dot { color: var(--accent); }
.hero-lede {
  max-width: 560px;
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: 400;
  line-height: 1.5;
  color: var(--ink);
  margin: 0 0 var(--space-5);
}
.hero-actions {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  flex-wrap: wrap;
}
.hero-meta {
  display: flex;
  gap: var(--space-3);
  align-items: center;
  flex-wrap: wrap;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--ink-3);
}
.hero-meta strong { color: var(--ink); font-weight: 500; }
.hero-dot-sep { color: var(--rule-2); }

/* TRUTH band */
.truth {
  border-top: 1px solid var(--rule);
  border-bottom: 1px solid var(--rule);
  padding: var(--space-7) var(--space-5);
  background: var(--paper-2);
}
.truth-line {
  max-width: var(--max-narrow);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.truth-text {
  font-family: var(--font-body);
  font-size: var(--text-md);
  line-height: 1.65;
  color: var(--ink);
}
.truth-em { color: var(--ink); font-style: italic; }
.warm { color: var(--accent-bright); font-weight: 500; }

/* HOW */
.how, .stack, .cta {
  max-width: var(--max-content);
  margin: 0 auto;
  padding: var(--space-9) var(--space-5);
}
.section-head { margin-bottom: var(--space-7); }
.section-title {
  font-size: clamp(36px, 6vw, var(--text-3xl));
  font-weight: 500;
  font-variation-settings: 'opsz' 144, 'wght' 500;
  margin: var(--space-3) 0 0;
  color: var(--ink);
}
.how-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: var(--space-4);
}
.how-card {
  grid-column: span 1;
  padding: var(--space-6) var(--space-5);
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
}
.how-card.span-2 { grid-column: span 2; }
.how-card.is-accent-card {
  background: linear-gradient(140deg, var(--accent-soft), var(--paper-2) 70%);
  border-color: color-mix(in oklch, var(--accent) 60%, var(--rule-2));
}
.how-num {
  font-family: var(--font-display);
  font-style: italic;
  font-size: var(--text-lg);
  color: var(--accent-bright);
  margin-bottom: var(--space-4);
}
.how-title {
  font-family: var(--font-display);
  font-weight: 500;
  font-style: italic;
  font-variation-settings: 'opsz' 96, 'wght' 500;
  font-size: var(--text-2xl);
  margin: 0 0 var(--space-3);
  color: var(--ink);
}
.how-copy {
  font-family: var(--font-body);
  color: var(--ink-2);
  line-height: 1.6;
  margin: 0;
  font-size: var(--text-base);
}

@media (max-width: 760px) {
  .how-grid { grid-template-columns: 1fr; }
  .how-card.span-2 { grid-column: span 1; }
}

/* STACK */
.stack-copy {
  font-family: var(--font-body);
  font-size: var(--text-md);
  line-height: 1.65;
  color: var(--ink);
  max-width: var(--max-prose);
  margin: 0 0 var(--space-5);
}
.stack-copy a {
  color: var(--accent-bright);
  border-bottom: 1px dashed color-mix(in oklch, var(--accent) 50%, transparent);
  transition: color var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
}
.stack-copy a:hover { color: var(--ink); border-color: var(--ink); }
.stack-link {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  letter-spacing: 0.05em;
  color: var(--accent-bright);
}

/* FOUNDER */
.founder {
  max-width: var(--max-content);
  margin: 0 auto;
  padding: var(--space-9) var(--space-5);
  border-top: 1px solid var(--rule);
}
.founder-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: var(--space-8);
  align-items: start;
}
@media (max-width: 760px) {
  .founder-grid { grid-template-columns: 1fr; gap: var(--space-6); }
}
.founder-name {
  font-size: clamp(44px, 7vw, 80px);
  font-weight: 500;
  font-variation-settings: 'opsz' 144, 'wght' 500;
  margin: var(--space-2) 0 var(--space-5);
  color: var(--ink);
}
.founder-bio {
  font-family: var(--font-body);
  font-size: var(--text-md);
  line-height: 1.65;
  color: var(--ink);
  max-width: 540px;
  margin: 0 0 var(--space-6);
}
.founder-actions { display: flex; flex-wrap: wrap; gap: var(--space-3); }
.founder-actions .h-btn { padding: 12px 22px; font-size: var(--text-base); }
.founder-right { padding-top: var(--space-4); }
.founder-links {
  list-style: none;
  padding: 0;
  margin: var(--space-3) 0 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.founder-links a {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--ink-2);
  letter-spacing: 0.02em;
  border-bottom: 1px dashed var(--rule-2);
  padding-bottom: 2px;
  transition: color var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
}
.founder-links a:hover { color: var(--accent-bright); border-color: var(--accent); }

/* CTA — statement */
.cta {
  text-align: center;
  border-top: 1px solid var(--rule);
  padding-top: var(--space-10);
  padding-bottom: var(--space-10);
}
.cta-title {
  font-size: clamp(40px, 8vw, 88px);
  font-weight: 500;
  font-variation-settings: 'opsz' 144, 'wght' 500;
  margin: 0 auto var(--space-6);
  max-width: 720px;
  color: var(--ink);
}
.cta-title em { color: var(--accent-bright); }
.cta-btn { padding: 16px 28px; font-size: var(--text-md); }

/* FOOT */
.foot {
  max-width: var(--max-content);
  margin: 0 auto;
  padding: var(--space-5);
  border-top: 1px solid var(--rule);
  color: var(--ink-3);
  font-size: var(--text-sm);
}
.foot-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) 0;
  flex-wrap: wrap;
  gap: var(--space-3);
}
.foot-sub { font-family: var(--font-mono); font-size: var(--text-xs); }
.foot a { color: var(--ink-2); border-bottom: 1px dashed var(--rule-2); }
.foot a:hover { color: var(--ink); }
.foot-meta { font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.06em; }

/* hero split — copy left, media right */
.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  gap: clamp(var(--space-6), 5vw, var(--space-9));
  align-items: center;
}
.hero-copy { min-width: 0; }
.hero-media {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  align-self: center;
}
.hero-video {
  margin: 0;
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--rule);
  background: #f5efe2;
  box-shadow:
    0 1px 0 0 color-mix(in oklch, var(--ink) 4%, transparent) inset,
    0 40px 90px -30px rgba(0, 0, 0, 0.55),
    0 12px 32px -12px rgba(0, 0, 0, 0.35);
  aspect-ratio: 16 / 10;
}
.hero-video::after {
  /* refined inner hairline */
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
}
.hero-video-el {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}
.hero-media-cap {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 0 4px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-3);
}
.hmc-label { color: var(--ink-2, var(--ink)); }
.hmc-meta { color: var(--ink-3); }

@media (prefers-reduced-motion: reduce) {
  .hero-video-el { display: none; }
  .hero-video {
    background-image: url('/swarmie-promo-poster.jpg');
    background-size: cover;
    background-position: center;
  }
}

@media (max-width: 1024px) {
  .hero-grid { grid-template-columns: 1fr; gap: var(--space-7); }
  .hero-media { order: 2; }
  .hero-copy { order: 1; }
}
@media (max-width: 720px) {
  .hero-video { border-radius: 12px; aspect-ratio: 16 / 9; }
  .hero-media-cap { font-size: 10px; letter-spacing: 0.14em; }
}
</style>
