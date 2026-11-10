<template>
  <section v-if="hasContent" class="advisor" aria-label="Advisor brief">
    <article v-if="working.length" class="adv-card">
      <span class="h-eyebrow">what's working</span>
      <ul class="adv-list">
        <li v-for="(w, i) in working" :key="i" class="adv-item adv-keep">{{ w }}</li>
      </ul>
    </article>

    <article v-if="risks.length" class="adv-card">
      <span class="h-eyebrow">hidden risks</span>
      <ol class="adv-list">
        <li v-for="(r, i) in risks" :key="i" class="adv-item">
          <p class="adv-risk">{{ r.risk }}</p>
          <p v-if="r.why_non_obvious" class="adv-sub"><span class="adv-tag">easy to miss</span>{{ r.why_non_obvious }}</p>
          <p v-if="r.cheap_test" class="adv-sub"><span class="adv-tag accent">test</span>{{ r.cheap_test }}</p>
        </li>
      </ol>
    </article>

    <article v-if="pathSteps.length" class="adv-card">
      <span class="h-eyebrow">path forward</span>
      <ol class="adv-list">
        <li v-for="s in pathSteps" :key="s.key" class="adv-item">
          <span class="adv-tag" :class="s.cls">{{ s.label }}</span>{{ s.text }}
        </li>
      </ol>
    </article>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  report: { type: Object, required: true },
})

const PATH_LABELS = [
  { key: 'this_week', label: 'this week', cls: 'accent' },
  { key: 'if_confirmed', label: 'if it holds', cls: 'live' },
  { key: 'if_not', label: 'if not', cls: '' },
]

const working = computed(() => props.report.what_working || [])
const risks = computed(() => props.report.hidden_risks || [])
const pathSteps = computed(() => {
  const p = props.report.path_forward || {}
  return PATH_LABELS.filter((s) => p[s.key]).map((s) => ({ ...s, text: p[s.key] }))
})
// Old results (pre-advisor fields) render nothing; a lone "this week" step that
// only repeats the hero's next_action isn't worth a section either.
const hasContent = computed(() =>
  working.value.length > 0 || risks.value.length > 0 || pathSteps.value.length > 1,
)
</script>

<style scoped>
.advisor {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(300px, 100%), 1fr));
  gap: var(--space-3);
}
.adv-card {
  background: var(--paper-3);
  border: 1px solid var(--rule);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  display: flex; flex-direction: column; gap: var(--space-3);
  min-width: 0;
}
.adv-list { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-3); }
.adv-item { font-size: var(--text-sm); line-height: 1.5; color: var(--ink-2); margin: 0; overflow-wrap: anywhere; }
.adv-keep::before { content: '+'; font-family: var(--font-mono); color: var(--live); margin-right: var(--space-2); }
.adv-risk { margin: 0 0 var(--space-1); color: var(--ink); font-weight: 600; }
.adv-sub { margin: var(--space-1) 0 0; color: var(--ink-2); }
.adv-tag {
  font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--ink-3); margin-right: var(--space-2); padding: 1px 5px;
  border: 1px solid var(--rule); border-radius: 4px; white-space: nowrap;
}
.adv-tag.accent { color: var(--accent-bright); border-color: color-mix(in oklch, var(--accent) 35%, transparent); }
.adv-tag.live { color: var(--live); border-color: color-mix(in oklch, var(--live) 35%, transparent); }
</style>
