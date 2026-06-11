<template>
  <div class="page roasts">
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
      <section class="roasts-head">
        <p class="kicker">famous roasts</p>
        <h1 class="h-display">Pitches history already graded.</h1>
        <p class="lede">
          We ran famous pitches — as they were actually told — through Swarmie's synthetic swarm,
          for fun and for calibration. These are synthetic reactions, disclosed as always.
          Hindsight makes everyone a genius; the interesting part is <em>which objection</em> the swarm finds first.
        </p>
      </section>

      <section class="roast-grid">
        <article v-for="r in roasts" :key="r.slug" class="roast-card">
          <div class="card-top">
            <h2 class="card-name">{{ r.name }}</h2>
            <span class="agents mono">{{ r.agent_count }} agents</span>
          </div>
          <p class="one-liner">{{ r.one_liner }}</p>

          <div class="verdict-row">
            <span class="verdict-label mono">verdict</span>
            <span class="verdict h-display" :class="verdictMeta(r.verdict).cls">{{ verdictMeta(r.verdict).label }}</span>
            <span class="conf mono">confidence · {{ r.confidence }}</span>
          </div>

          <blockquote class="objection">“{{ r.top_objections[0].text }}”</blockquote>

          <div class="card-meta mono">
            <span>{{ r.silence_pct }}% scrolled past</span>
          </div>

          <p class="blurb">{{ r.blurb }}</p>

          <router-link to="/new" class="h-btn is-accent card-cta">Roast your own →</router-link>
        </article>
      </section>

      <footer class="foot">
        <div class="foot-row foot-sub">
          <router-link to="/">← swarmie</router-link>
          <span>Synthetic users, always disclosed.</span>
        </div>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { verdictMeta } from '../lib/verdict'
import data from '../data/famousRoasts.json'

const roasts = data.roasts
</script>

<style scoped>
.roasts {
  min-height: 100vh;
  background: var(--paper);
  color: var(--ink);
}

.nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px clamp(20px, 5vw, 56px);
}

main {
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 clamp(20px, 5vw, 56px) 80px;
}

/* --- head --- */
.roasts-head {
  padding: clamp(40px, 8vh, 96px) 0 40px;
  max-width: 640px;
}
.kicker {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--accent-bright);
  margin: 0 0 14px;
}
.roasts-head h1 {
  font-size: clamp(34px, 5.4vw, 56px);
  line-height: 1.04;
  margin: 0 0 18px;
}
.lede {
  color: var(--ink-3);
  font-size: 16px;
  line-height: 1.65;
  margin: 0;
}
.lede em { color: var(--ink-2); }

/* --- grid --- */
.roast-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}
.roast-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 26px 24px 24px;
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: 14px;
}
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}
.card-name {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}
.mono {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-4);
}
.one-liner {
  color: var(--ink-3);
  font-size: 14px;
  line-height: 1.55;
  margin: 0;
}

.verdict-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
  padding-top: 6px;
  border-top: 1px solid var(--rule);
}
.verdict {
  font-style: italic;
  font-weight: 600;
  font-size: 30px;
  line-height: 1;
}
.verdict.is-ship { color: var(--live); }
.verdict.is-sharpen { color: var(--accent-bright); }
.verdict.is-wrong { color: var(--warn); }
.verdict.is-kill { color: var(--warn); }

.objection {
  margin: 0;
  padding-left: 14px;
  border-left: 2px solid var(--accent-soft);
  font-family: var(--font-display);
  font-style: italic;
  font-size: 16px;
  line-height: 1.5;
  color: var(--ink-2);
}

.card-meta { color: var(--ink-4); }

.blurb {
  color: var(--ink-3);
  font-size: 13px;
  line-height: 1.6;
  margin: 0;
  flex: 1;
}

.card-cta { align-self: flex-start; }

/* --- foot --- */
.foot {
  margin-top: 64px;
  padding-top: 20px;
  border-top: 1px solid var(--rule);
}
.foot-sub {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--ink-4);
}
.foot-sub a { color: var(--ink-3); text-decoration: none; }
.foot-sub a:hover { color: var(--accent-bright); }

@media (max-width: 640px) {
  .roast-grid { grid-template-columns: 1fr; }
  .verdict { font-size: 26px; }
}
</style>
