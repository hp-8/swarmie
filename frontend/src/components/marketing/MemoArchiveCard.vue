<template>
  <article :id="memo.slug" class="roast-card" :class="[`is-${variant}`, { 'is-featured': featured }]">
    <component :is="variant === 'compact' ? 'router-link' : 'div'" v-bind="variant === 'compact' ? { to: `/roasts#${memo.slug}` } : {}" class="card-link">
      <header class="card-head">
        <h3 class="card-name">{{ memo.name }}</h3>
        <span v-if="era" class="card-era">{{ era }}</span>
      </header>
      <p class="card-pitch">{{ pitch }}</p>

      <p class="verdict" :class="verdictMeta(memo.verdict).cls">{{ recPhrase(memo.verdict) }}</p>

      <blockquote class="card-quote">"{{ memo.top_objections[0].text }}"</blockquote>

      <dl class="card-stats">
        <div><dt>Panel</dt><dd>{{ memo.agent_count }}</dd></div>
        <div><dt>Scrolled past</dt><dd>{{ memo.silence_pct }}%</dd></div>
        <div><dt>Confidence</dt><dd>{{ CONF[memo.confidence] || memo.confidence }}</dd></div>
      </dl>
    </component>

    <template v-if="variant === 'full'">
      <div class="card-caught">
        <h4 class="caught-title">What the panel caught</h4>
        <p class="caught-body">{{ memo.blurb }}</p>
      </div>
      <router-link to="/new" class="card-cta">Review your own pitch</router-link>
    </template>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { verdictMeta, recPhrase } from '../../lib/verdict'

const props = defineProps({
  memo: { type: Object, required: true },
  variant: { type: String, default: 'full' }, // 'full' | 'compact'
  featured: { type: Boolean, default: false },
})

const CONF = { low: 'Low', med: 'Medium', high: 'High' }

// One-liners carry their era as a trailing "(2018 pitch)"; lift it into its own slot.
const ERA_RE = /\s*\(([^)]*\d{4}[^)]*)\)\s*$/
const era = computed(() => props.memo.one_liner.match(ERA_RE)?.[1] || '')
const pitch = computed(() => props.memo.one_liner.replace(ERA_RE, ''))
</script>

<style scoped>
.roast-card {
  position: relative;
  display: flex;
  flex-direction: column;
  background: var(--paper);
  border: 1px solid var(--rule);
  box-shadow: 0 1px 2px oklch(20% 0.02 250 / 0.06);
  transition: box-shadow var(--dur-base) var(--ease-out), transform var(--dur-base) var(--ease-out), border-color var(--dur-base) var(--ease-out);
  min-width: 0;
  scroll-margin-top: 96px;
}
.card-link { display: flex; flex-direction: column; flex: 1; padding: var(--space-5) var(--space-5) var(--space-4); color: inherit; }

.card-head { display: flex; justify-content: space-between; align-items: baseline; gap: var(--space-3); }
.card-name { margin: 0; font-family: var(--font-display); font-weight: 600; font-size: var(--text-xl); letter-spacing: -0.01em; }
.card-era { font-size: var(--text-sm); color: var(--ink-3); white-space: nowrap; font-variant-numeric: tabular-nums; }
.card-pitch { margin: var(--space-2) 0 0; font-size: var(--text-sm); line-height: 1.5; color: var(--ink-2); }

.verdict {
  margin: var(--space-5) 0 0;
  padding-top: var(--space-4);
  border-top: 2px solid var(--ink);
  font-family: var(--font-display);
  font-weight: 600;
  font-size: var(--text-2xl);
  line-height: 1.1;
  letter-spacing: -0.015em;
}
.verdict.is-kill, .verdict.is-wrong { color: var(--ink); background: linear-gradient(transparent 58%, var(--warn-hl) 58%); -webkit-box-decoration-break: clone; box-decoration-break: clone; width: fit-content; }
.verdict.is-ship { color: var(--live); }

.card-quote {
  margin: var(--space-3) 0 0;
  font-family: var(--font-display);
  font-size: var(--text-md);
  line-height: 1.5;
  color: var(--ink-2);
}

.card-stats { margin: auto 0 0; padding-top: var(--space-5); display: grid; grid-template-columns: repeat(3, auto); justify-content: start; gap: var(--space-6); }
.card-stats dt { font-size: var(--text-xs); color: var(--ink-3); }
.card-stats dd { margin: 2px 0 0; font-weight: 700; font-variant-numeric: tabular-nums; }

.card-caught { margin: 0 var(--space-5); padding: var(--space-4) 0; border-top: 1px solid var(--rule); }
.caught-title { margin: 0; font-size: var(--text-sm); font-weight: 700; }
.caught-body { margin: var(--space-2) 0 0; font-size: var(--text-sm); line-height: 1.6; color: var(--ink-2); max-width: 62ch; }
.card-cta {
  margin: 0 var(--space-5) var(--space-5);
  align-self: start;
  font-size: var(--text-sm);
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 3px;
}

/* Compact: Home strip. The whole card is the link. */
.is-compact { height: 100%; }
.is-compact .card-quote { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.is-compact .verdict { font-size: var(--text-xl); }
.is-compact:hover { transform: translateY(-3px); border-color: var(--rule-2); box-shadow: 0 18px 36px -24px oklch(20% 0.02 250 / 0.4); }

/* Featured: spans the archive grid, quote set large beside the verdict. */
.is-featured .card-link { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.25fr); column-gap: var(--space-8); }
.is-featured .card-head, .is-featured .card-pitch { grid-column: 1; }
.is-featured .verdict { grid-column: 1; font-size: var(--text-3xl); }
.is-featured .card-quote { grid-column: 2; grid-row: 1 / span 4; margin: 0; align-self: center; font-size: clamp(22px, 2.2vw, 30px); line-height: 1.35; color: var(--ink); }
.is-featured .card-stats { grid-column: 1; }

@media (max-width: 767px) {
  .is-featured .card-link { display: flex; }
  .is-featured .card-quote { font-size: var(--text-lg); margin-top: var(--space-3); }
  .is-featured .verdict { font-size: var(--text-2xl); }
  .card-stats { gap: var(--space-5); }
}
</style>
