<template>
  <div class="page home">
    <!-- NAV — floating pill -->
    <header class="nav">
      <router-link to="/" class="brand-mark">
        <span class="dot"></span>
        <span class="brand-text">SWARMIE</span>
      </router-link>
      <nav class="nav-right">
        <a href="https://github.com/hp-8/swarmie" target="_blank" class="ghost-link">github ↗</a>
        <router-link to="/new" class="h-btn is-accent nav-cta">Run a roast</router-link>
      </nav>
    </header>

    <main>
      <!-- HERO — living swarm canvas, text overlaid low -->
      <section class="hero">
        <HeroSwarm class="hero-swarm" />
        <div class="hero-scrim" aria-hidden="true"></div>
        <div class="hero-inner hero-grid">
          <div class="hero-copy">
            <span class="h-chip is-accent hero-chip">Open source · Alpha</span>
            <h1 class="hero-title h-display">
              Roast your startup<br />
              with <em>500 AI users.</em>
            </h1>
            <p class="hero-lede">
              Paste the pitch. A swarm reacts like Reddit, HN and Product Hunt all at once,
              then hands you the three objections to kill before you burn a single user interview.
            </p>
            <div class="hero-actions">
              <router-link to="/new" class="h-btn is-accent hero-cta">Run a roast →</router-link>
              <a href="#how" class="h-btn is-ghost">See how it works</a>
            </div>
            <div class="hero-meta">
              <span><strong>~60s</strong> per run</span>
              <span class="sep">·</span>
              <span><strong>$0</strong> on local Ollama</span>
              <span class="sep">·</span>
              <span><strong>AGPL-3.0</strong></span>
            </div>
          </div>

          <figure class="hero-media">
            <video
              class="hero-video"
              autoplay muted loop playsinline preload="metadata"
              poster="/swarmie-promo-poster.jpg"
              aria-label="Swarmie walkthrough: paste a pitch, the swarm reacts, a decision brief comes back"
            >
              <source src="/swarmie-promo.webm" type="video/webm" />
              <source src="/swarmie-promo.mp4" type="video/mp4" />
            </video>
            <figcaption class="hero-media-cap">
              <span>walkthrough</span><span class="sep">·</span><span>pitch → swarm → decision</span>
            </figcaption>
          </figure>
        </div>
      </section>

      <!-- HONESTY band -->
      <section class="truth" v-reveal>
        <p class="truth-line">
          <span class="h-eyebrow">A note before we start. <AiDisclosure aria-label="How this was generated" /></span>
          <span class="truth-text">
            These are AI agents, <em>not real users</em>. They are wrong sometimes,
            agreeable too often, and they don't write your TAM check. Use the signal to
            <span class="warm">kill bad positionings before</span> they cost a real conversation,
            not to declare PMF.
          </span>
        </p>
      </section>

      <!-- LOOP — the walkthrough video is the proof, captions ride below -->
      <section id="how" class="loop">
        <header class="section-head" v-reveal>
          <span class="h-eyebrow">the loop</span>
          <h2 class="section-title h-display">Three turns. Sixty seconds.</h2>
        </header>

        <ol class="loop-steps">
          <li v-reveal="0">
            <span class="loop-num">i.</span>
            <h3 class="loop-step-title">Paste a pitch.</h3>
            <p class="loop-step-copy">Deck text, landing copy, half a tweet. We parse the ICP, problem, solution and price.</p>
          </li>
          <li v-reveal="120">
            <span class="loop-num">ii.</span>
            <h3 class="loop-step-title">The swarm reacts.</h3>
            <p class="loop-step-copy">100 to 500 personas post, comment, upvote or scroll past. Skeptics, lurkers, fans, trolls.</p>
          </li>
          <li v-reveal="240">
            <span class="loop-num">iii.</span>
            <h3 class="loop-step-title">Get a decision.</h3>
            <p class="loop-step-copy">A verdict, the objections to test, and why the silent ones scrolled past.</p>
          </li>
        </ol>
      </section>

      <!-- AHA — the output, shown -->
      <section class="aha" v-reveal>
        <div class="aha-copy">
          <span class="h-eyebrow">what you walk away with</span>
          <h2 class="aha-title h-display">You don't get a grade.<br />You get a <em>decision.</em></h2>
          <p class="aha-lede">
            Not a vanity PMF number. A verdict, the exact question to ask five real users,
            the signal that would kill the positioning, and the fix to try first.
          </p>
          <router-link to="/new" class="h-btn is-accent">Run yours →</router-link>
        </div>
        <div class="aha-visual">
          <DecisionBriefPreview />
        </div>
      </section>

      <!-- FOUNDER -->
      <section class="founder" v-reveal>
        <div class="founder-grid">
          <div class="founder-left">
            <span class="h-eyebrow">who made this</span>
            <h2 class="founder-name h-display">Harsh Patadia.</h2>
            <p class="founder-bio">
              I build for founders. Swarmie is the free version of how I think about early-stage
              validation: fast, brutal, focused on the objection you actually need to hear. If you
              want a human in the loop, to ship the MVP, sharpen the pitch or prep the raise, that's the day job.
            </p>
            <div class="founder-actions">
              <a href="https://harshpatadia.space" target="_blank" class="h-btn is-accent">Work with me →</a>
              <a href="https://harshpatadia.space" target="_blank" class="h-btn is-ghost">harshpatadia.space</a>
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

      <!-- CLOSING CTA -->
      <section class="cta" v-reveal>
        <h2 class="cta-title h-display">What would <em>500 strangers</em> say about it today?</h2>
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
          <router-link to="/terms">Terms</router-link>
          <router-link to="/privacy">Privacy</router-link>
        </div>
      </footer>
    </main>
  </div>
</template>

<script setup>
import AiDisclosure from '../components/AiDisclosure.vue'
import HeroSwarm from '../components/HeroSwarm.vue'
import DecisionBriefPreview from '../components/marketing/DecisionBriefPreview.vue'
</script>

<style scoped>
/* Hallmark · page: Home · macrostructure: Marquee Hero (atmospheric)
 * Hallmark · pre-emit critique: P5 H4 E5 S4 R5 V4
 * theme: Midnight+coral · genre: atmospheric · register: brand
 */

.page { min-height: 100vh; color: var(--ink); background: var(--paper); }

/* NAV — floating pill */
.nav {
  position: sticky; top: var(--space-4); z-index: 30;
  display: flex; align-items: center; justify-content: space-between;
  max-width: var(--max-content);
  margin: var(--space-4) auto 0;
  padding: 10px 14px 10px 18px;
  background: color-mix(in oklch, var(--paper-2) 82%, transparent);
  border: 1px solid var(--rule); border-radius: var(--radius-pill);
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
}
.brand-mark {
  display: inline-flex; align-items: center; gap: var(--space-2);
  font-family: var(--font-mono); font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.22em; color: var(--ink);
}
.brand-mark .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 14px var(--accent); }
.nav-right { display: flex; align-items: center; gap: var(--space-4); }
.ghost-link { color: var(--ink-2); font-size: var(--text-sm); font-family: var(--font-mono); letter-spacing: 0.04em; transition: color var(--dur-fast) var(--ease-out); }
.ghost-link:hover { color: var(--ink); }
.nav-cta { padding: 9px 16px; font-size: var(--text-sm); }

/* HERO — full-bleed swarm canvas + scrim + overlaid text */
.hero {
  position: relative;
  min-height: min(92vh, 900px);
  margin-top: calc(var(--space-7) * -1);
  display: flex; align-items: center;
  overflow: hidden;
}
.hero-swarm { z-index: 0; }
.hero-scrim {
  position: absolute; inset: 0; z-index: 1; pointer-events: none;
  background:
    /* vignette — darken the edges so the headline holds the eye */
    radial-gradient(125% 115% at 50% 38%, transparent 52%, color-mix(in oklch, var(--paper) 60%, transparent) 100%),
    /* cool counter-glow lower-left for depth */
    radial-gradient(70% 60% at 16% 80%, color-mix(in oklch, var(--info) 7%, transparent), transparent 60%),
    /* bottom fade so the hero melts into the next section */
    linear-gradient(to bottom, transparent 42%, color-mix(in oklch, var(--paper) 68%, transparent) 82%, var(--paper) 100%);
}
/* breathing coral dawn — the warmth behind the headline, alive but barely */
.hero-scrim::before {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(80% 62% at 72% 4%, color-mix(in oklch, var(--accent) 24%, transparent), transparent 58%),
    radial-gradient(46% 38% at 60% 0%, color-mix(in oklch, var(--accent-bright) 16%, transparent), transparent 62%);
  will-change: opacity, transform;
  transform-origin: 68% 0%;
  animation: heroBreathe 12s var(--ease-in-out) infinite alternate;
}
@keyframes heroBreathe {
  from { opacity: 0.78; transform: scale(1); }
  to   { opacity: 1;    transform: scale(1.05); }
}
/* fine grain for tactile depth */
.hero-scrim::after {
  content: ""; position: absolute; inset: 0; opacity: 0.05; mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
.hero-inner {
  position: relative; z-index: 2;
  max-width: var(--max-content); width: 100%;
  margin: 0 auto; padding: var(--space-8) var(--space-5) var(--space-9);
}
.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  gap: clamp(var(--space-6), 5vw, var(--space-8));
  align-items: center;
}
.hero-copy { min-width: 0; }
.hero-media {
  margin: 0; position: relative;
  border-radius: var(--radius-lg); overflow: hidden;
  border: 1px solid var(--rule); background: var(--paper-3);
  box-shadow: 0 40px 90px -36px rgba(0,0,0,0.7), 0 12px 32px -16px rgba(0,0,0,0.5);
  aspect-ratio: 16 / 10;
}
.hero-video { width: 100%; height: 100%; display: block; object-fit: cover; }
.hero-media-cap {
  position: absolute; left: 0; right: 0; bottom: 0;
  display: flex; gap: var(--space-2); align-items: center;
  padding: var(--space-3) var(--space-4);
  font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--ink-2);
  background: linear-gradient(to top, color-mix(in oklch, var(--paper) 78%, transparent), transparent);
}
.hero-media-cap .sep { color: var(--rule-2); }
.hero-chip { margin-bottom: var(--space-4); }

/* staggered entrance — chip → headline → lede → actions → meta, then the media */
.hero-copy > * { opacity: 0; animation: heroRise 620ms var(--ease-out) forwards; }
.hero-copy > *:nth-child(1) { animation-delay: 60ms; }
.hero-copy > *:nth-child(2) { animation-delay: 130ms; }
.hero-copy > *:nth-child(3) { animation-delay: 210ms; }
.hero-copy > *:nth-child(4) { animation-delay: 290ms; }
.hero-copy > *:nth-child(5) { animation-delay: 360ms; }
.hero-media { opacity: 0; animation: heroRise 720ms var(--ease-out) 360ms forwards; }
@keyframes heroRise {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: none; }
}
/* press feedback — the interface listens */
.hero-actions .h-btn:active { transform: scale(0.97); }
.hero-title {
  font-size: clamp(44px, 8.5vw, 104px);
  line-height: 0.96; letter-spacing: -0.02em; font-weight: 600;
  font-variation-settings: 'opsz' 144, 'wght' 600;
  margin: 0 0 var(--space-4); color: var(--ink);
  overflow-wrap: anywhere; min-width: 0;
}
.hero-title em { font-style: normal; color: var(--accent-bright); }
.hero-lede {
  max-width: 600px; font-family: var(--font-body);
  font-size: clamp(var(--text-base), 2.2vw, var(--text-lg));
  line-height: 1.55; color: var(--ink-2); margin: 0 0 var(--space-5);
}
.hero-actions { display: flex; gap: var(--space-3); flex-wrap: wrap; margin-bottom: var(--space-5); }
.hero-cta { padding: 15px 26px; font-size: var(--text-md); }
.hero-meta {
  display: flex; gap: var(--space-3); align-items: center; flex-wrap: wrap;
  font-family: var(--font-mono); font-size: var(--text-sm); color: var(--ink-3);
}
.hero-meta strong { color: var(--ink); font-weight: 500; }
.hero-meta .sep { color: var(--rule-2); }

/* HONESTY band */
.truth {
  border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule);
  padding: var(--space-8) var(--space-5); background: var(--paper-2);
}
.truth-line { max-width: var(--max-narrow); margin: 0 auto; display: flex; flex-direction: column; gap: var(--space-3); }
.truth-text { font-family: var(--font-body); font-size: clamp(var(--text-md), 2.4vw, var(--text-lg)); line-height: 1.65; color: var(--ink); }
.truth-em { color: var(--ink); font-style: normal; }
.truth-text em { color: var(--ink); font-style: normal; }
.warm { color: var(--accent-bright); font-weight: 500; }

/* shared section heads */
.section-head { max-width: var(--max-content); margin: 0 auto var(--space-7); }
.section-title { font-size: clamp(32px, 6vw, 56px); font-weight: 500; font-variation-settings: 'opsz' 144, 'wght' 500; margin: var(--space-2) 0 0; color: var(--ink); }

/* LOOP */
.loop { max-width: var(--max-content); margin: 0 auto; padding: var(--space-9) var(--space-5); }
.loop-steps {
  list-style: none; margin: 0; padding: 0;
  display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-6);
}
.loop-steps li { display: flex; flex-direction: column; gap: var(--space-2); }
.loop-num { font-family: var(--font-display); font-style: normal; font-size: var(--text-xl); color: var(--accent-bright); }
.loop-step-title { font-family: var(--font-display); font-style: normal; font-weight: 500; font-size: var(--text-xl); margin: 0; color: var(--ink); }
.loop-step-copy { font-family: var(--font-body); font-size: var(--text-base); line-height: 1.6; color: var(--ink-2); margin: 0; }

/* AHA */
.aha {
  max-width: var(--max-content); margin: 0 auto; padding: var(--space-9) var(--space-5);
  display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: clamp(var(--space-6), 5vw, var(--space-9)); align-items: center;
}
.aha-title { font-size: clamp(32px, 5.5vw, 56px); font-weight: 500; font-variation-settings: 'opsz' 144, 'wght' 500; margin: var(--space-3) 0 var(--space-4); color: var(--ink); }
.aha-title em { color: var(--accent-bright); font-style: normal; }
.aha-lede { font-family: var(--font-body); font-size: var(--text-md); line-height: 1.65; color: var(--ink-2); max-width: 460px; margin: 0 0 var(--space-6); }
.aha-visual { min-width: 0; }

/* FOUNDER */
.founder { max-width: var(--max-content); margin: 0 auto; padding: var(--space-9) var(--space-5); border-top: 1px solid var(--rule); }
.founder-grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: var(--space-8); align-items: start; }
.founder-name { font-size: clamp(40px, 7vw, 76px); font-weight: 500; font-variation-settings: 'opsz' 144, 'wght' 500; margin: var(--space-2) 0 var(--space-5); color: var(--ink); }
.founder-bio { font-family: var(--font-body); font-size: var(--text-md); line-height: 1.65; color: var(--ink); max-width: 540px; margin: 0 0 var(--space-6); }
.founder-actions { display: flex; flex-wrap: wrap; gap: var(--space-3); }
.founder-right { padding-top: var(--space-4); }
.founder-links { list-style: none; padding: 0; margin: var(--space-3) 0 0; display: flex; flex-direction: column; gap: var(--space-3); }
.founder-links a {
  font-family: var(--font-mono); font-size: var(--text-sm); color: var(--ink-2); letter-spacing: 0.02em;
  border-bottom: 1px dashed var(--rule-2); padding-bottom: 2px;
  transition: color var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
}
.founder-links a:hover { color: var(--accent-bright); border-color: var(--accent); }

/* CLOSING CTA */
.cta { max-width: var(--max-narrow); margin: 0 auto; text-align: center; border-top: 1px solid var(--rule); padding: var(--space-10) var(--space-5); }
.cta-title { font-size: clamp(36px, 7vw, 76px); font-weight: 500; font-variation-settings: 'opsz' 144, 'wght' 500; margin: 0 auto var(--space-6); color: var(--ink); }
.cta-title em { color: var(--accent-bright); font-style: normal; }
.cta-btn { padding: 16px 30px; font-size: var(--text-md); }

/* FOOT */
.foot { max-width: var(--max-content); margin: 0 auto; padding: var(--space-5); border-top: 1px solid var(--rule); color: var(--ink-3); font-size: var(--text-sm); }
.foot-row { display: flex; justify-content: space-between; align-items: center; padding: var(--space-3) 0; flex-wrap: wrap; gap: var(--space-3); }
.foot-sub { font-family: var(--font-mono); font-size: var(--text-xs); }
.foot a { color: var(--ink-2); border-bottom: 1px dashed var(--rule-2); }
.foot a:hover { color: var(--ink); }
.foot-meta { font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.06em; }

/* ---- TABLET / iPad ---- */
@media (max-width: 1024px) {
  .hero { min-height: auto; align-items: stretch; }
  .hero-inner { padding-top: var(--space-9); }
  .hero-grid { grid-template-columns: 1fr; gap: var(--space-7); }
  .hero-media { order: 2; max-width: 620px; }
  .hero-copy { order: 1; }
  .aha { grid-template-columns: 1fr; gap: var(--space-7); }
  .aha-visual { max-width: 560px; }
  .founder-grid { grid-template-columns: 1fr; gap: var(--space-6); }
}

/* ---- MOBILE ---- */
@media (max-width: 760px) {
  .nav { top: 0; margin-top: 0; border-radius: 0; border-left: 0; border-right: 0; border-top: 0; }
  .hero { min-height: 78vh; margin-top: 0; }
  .hero-inner { padding: var(--space-7) var(--space-4) var(--space-8); }
  .hero-title { font-size: clamp(38px, 12vw, 60px); }
  .hero-actions { gap: var(--space-2); }
  .hero-cta, .hero-actions .h-btn { width: 100%; }
  .loop-steps { grid-template-columns: 1fr; gap: var(--space-5); }
  .loop-media { border-radius: var(--radius-lg); }
  .founder-actions .h-btn { width: 100%; }
}
</style>

