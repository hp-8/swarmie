<template>
  <div class="x-rows">
    <section class="x-row" aria-labelledby="deck-title">
      <div class="x-cell x-wide">
        <div class="deck-head">
          <h2 id="deck-title">Deck diagnosis</h2>
          <dl class="deck-facts">
            <div><dt>Funding readiness</dt><dd>{{ d.readiness_pct ?? 0 }}%</dd></div>
            <div v-if="d.stage"><dt>Stage</dt><dd>{{ d.stage }}</dd></div>
            <div><dt>Deck score</dt><dd>{{ d.overall_score ?? 0 }}/130</dd></div>
          </dl>
        </div>
        <p v-if="d.next_move" class="deck-move"><strong>Fix in the deck first:</strong> {{ d.next_move }}</p>
        <ol v-if="d.slides?.length" class="slides">
          <li v-for="s in d.slides" :key="s.page + s.slide_type" class="slide">
            <div class="slide-top">
              <span class="slide-name">{{ cap(s.slide_type) }} <span class="slide-page">p.{{ s.page }}</span></span>
              <b class="slide-score" :class="{ 'is-weak': s.score < 5 }">{{ s.score }}/10</b>
            </div>
            <span class="bar" :style="{ '--w': `${(Number(s.score) || 0) * 10}%` }"></span>
            <p v-if="s.top_issue" class="slide-issue">{{ s.top_issue }}</p>
          </li>
        </ol>
      </div>
      <div class="x-cell">
        <h2>Red flags</h2>
        <ul v-if="d.red_flags?.length" class="flags">
          <li v-for="(f, i) in d.red_flags" :key="i">
            <p class="flag-top">
              <span class="sev" :class="{ 'is-serious': ['CRITICAL', 'HIGH'].includes(f.severity) }">{{ f.severity }}</span>
              {{ cap(f.slide_type) }} <span class="slide-page">p.{{ f.page }}</span>
            </p>
            <p class="flag-text">{{ f.text }}</p>
          </li>
        </ul>
        <p v-else class="muted">No red flags on this deck.</p>
      </div>
    </section>

    <section v-if="d.strong_zones?.length || d.weak_zones?.length || d.investor_simulation" class="x-row">
      <div v-if="d.strong_zones?.length || d.weak_zones?.length" class="x-cell">
        <template v-if="d.strong_zones?.length">
          <h2>Strong in the deck</h2>
          <ul class="ticks good"><li v-for="z in d.strong_zones" :key="z">{{ z }}</li></ul>
        </template>
        <template v-if="d.weak_zones?.length">
          <h2 :class="{ 'h-gap': d.strong_zones?.length }">Weak in the deck</h2>
          <ul class="ticks bad"><li v-for="z in d.weak_zones" :key="z">{{ z }}</li></ul>
        </template>
      </div>
      <figure v-if="d.investor_simulation" class="x-cell x-wide">
        <figcaption>An investor in the room</figcaption>
        <blockquote class="room">{{ d.investor_simulation }}</blockquote>
      </figure>
    </section>
  </div>
</template>

<script setup>
defineProps({ d: { type: Object, required: true } })
const cap = (s) => (s ? String(s).charAt(0).toUpperCase() + String(s).slice(1) : '')
</script>

<style scoped>
/* Extra memo rows: same hairline ledger as DecisionMemo's board. */
.x-rows { grid-column: 1 / -1; display: grid; gap: 1px; }
.x-row { display: flex; flex-wrap: wrap; gap: 1px; }
.x-cell { flex: 1 1 280px; margin: 0; min-width: 0; background: var(--paper); padding: var(--space-6); }
.x-wide { flex: 2 1 460px; }
h2, figcaption { margin: 0 0 var(--space-4); font-size: var(--text-base); font-weight: 700; }
.h-gap { margin-top: var(--space-6); }
.muted { margin: 0; color: var(--ink-3); font-size: var(--text-sm); }

.deck-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: var(--space-2) var(--space-5); }
.deck-head h2 { margin: 0; }
.deck-facts { display: flex; flex-wrap: wrap; gap: var(--space-1) var(--space-5); margin: 0; font-size: var(--text-sm); }
.deck-facts > div { display: flex; gap: var(--space-2); }
.deck-facts dt { color: var(--ink-3); }
.deck-facts dd { margin: 0; font-weight: 700; font-variant-numeric: tabular-nums; }
.deck-move { margin: var(--space-4) 0 0; padding: var(--space-3) var(--space-4); background: var(--paper-2); line-height: 1.5; }

.slides { list-style: none; margin: var(--space-5) 0 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: var(--space-5) var(--space-6); }
.slide-top { display: flex; justify-content: space-between; gap: var(--space-3); font-size: var(--text-sm); }
.slide-name { font-weight: 600; }
.slide-page { color: var(--ink-3); font-weight: 400; }
.slide-score { font-variant-numeric: tabular-nums; }
.slide-score.is-weak { background: var(--warn-hl); padding: 0 0.35em; border-radius: 3px; }
.bar { display: block; margin-top: var(--space-2); height: 5px; border-radius: 3px; background: linear-gradient(90deg, var(--ink-2) var(--w), var(--paper-3) var(--w)); }
.slide-issue { margin: var(--space-2) 0 0; font-size: var(--text-sm); line-height: 1.45; color: var(--ink-3); }

.flags { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-4); }
.flag-top { margin: 0; font-size: var(--text-sm); font-weight: 600; }
.sev { display: inline-block; margin-right: var(--space-2); font-size: var(--text-xs); font-weight: 700; letter-spacing: 0.05em; color: var(--ink-3); }
.sev.is-serious { color: var(--ink); background: var(--warn-hl); padding: 0.05em 0.4em; border-radius: 3px; }
.flag-text { margin: var(--space-1) 0 0; font-size: var(--text-sm); line-height: 1.5; color: var(--ink-2); }

.ticks { margin: 0; padding-left: 1.1em; display: grid; gap: var(--space-2); font-size: var(--text-sm); line-height: 1.5; color: var(--ink-2); }
.ticks.good li::marker { color: var(--live); }
.ticks.bad li::marker { color: var(--warn); }
.room { margin: 0; font-family: var(--font-display); font-size: var(--text-md); line-height: 1.6; color: var(--ink-2); max-width: 70ch; white-space: pre-line; }

@media (max-width: 767px) { .x-cell { padding: var(--space-5) var(--space-4); } }
</style>
