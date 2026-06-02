<template>
  <ol v-if="objections?.length" class="obj-list scroll-zone">
    <li v-for="(obj, i) in objections" :key="obj.category" class="obj-row">
      <span class="obj-rank">{{ String(i + 1).padStart(2, '0') }}</span>
      <div class="obj-body">
        <div class="obj-head-row">
          <span class="obj-cat">{{ obj.category }}</span>
          <span class="obj-count">{{ obj.count }}×</span>
        </div>
        <p v-if="obj.example_quote" class="obj-quote">"{{ obj.example_quote }}"</p>
        <div v-if="obj.real_test" class="obj-test">
          <button class="obj-test-q" @click="copyTest(obj)" title="Copy this question">
            <span class="obj-tag">{{ copy.askTag }}</span>
            <span class="obj-test-text">{{ obj.real_test }}</span>
            <span class="obj-copy">{{ copiedTest === obj.category ? '✓' : '⧉' }}</span>
          </button>
        </div>
        <p v-if="obj.kill_criteria" class="obj-kill"><span class="obj-tag warn">{{ copy.killTag }}</span>{{ obj.kill_criteria }}</p>
        <p v-if="obj.suggested_fix" class="obj-fix"><span class="obj-tag accent">fix</span>{{ obj.suggested_fix }}</p>
        <ObjectionVote :job-id="jobId" :objection-category="obj.category" />
      </div>
    </li>
  </ol>
  <p v-else class="muted">No clear clusters.</p>
</template>

<script setup>
import { ref } from 'vue'
import ObjectionVote from '../feedback/ObjectionVote.vue'

defineProps({
  objections: { type: Array, default: () => [] },
  copy: { type: Object, required: true },
  jobId: { type: String, required: true },
})

const copiedTest = ref(null)
async function copyTest(obj) {
  try { await navigator.clipboard.writeText(obj.real_test || '') } catch { /* clipboard blocked */ }
  copiedTest.value = obj.category
  setTimeout(() => { if (copiedTest.value === obj.category) copiedTest.value = null }, 1500)
}
</script>

<style scoped>
.obj-list { list-style: none; padding: 0 var(--space-3) 0 0; margin: 0; display: flex; flex-direction: column; gap: var(--space-4); }
.obj-row { display: grid; grid-template-columns: 34px 1fr; gap: var(--space-3); align-items: start; padding-bottom: var(--space-4); border-bottom: 1px solid var(--rule); }
.obj-row:last-child { border-bottom: 0; padding-bottom: 0; }
.obj-rank {
  font-family: var(--font-display); font-style: italic; font-weight: 600;
  font-size: var(--text-2xl); color: var(--accent-bright); line-height: 0.9;
}
.obj-head-row { display: flex; justify-content: space-between; align-items: baseline; gap: var(--space-3); margin-bottom: var(--space-1); }
.obj-cat { font-family: var(--font-mono); font-size: var(--text-sm); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--ink); }
.obj-count { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--ink-3); flex-shrink: 0; }
.obj-quote {
  font-family: var(--font-display); font-style: italic; font-weight: 500;
  font-variation-settings: 'opsz' 96, 'wght' 500;
  font-size: var(--text-md); line-height: 1.45; color: var(--ink); margin: 0;
}
.obj-tag { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink-3); margin-right: var(--space-2); padding: 1px 5px; border: 1px solid var(--rule); border-radius: 4px; white-space: nowrap; }
.obj-tag.warn { color: var(--warn); border-color: color-mix(in oklch, var(--warn) 35%, transparent); }
.obj-tag.accent { color: var(--accent-bright); border-color: color-mix(in oklch, var(--accent) 35%, transparent); }
.obj-test { margin-top: var(--space-2); }
.obj-test-q { display: flex; align-items: baseline; gap: var(--space-2); width: 100%; text-align: left; background: var(--paper-3); border: 1px solid var(--rule); border-radius: var(--radius-sm); padding: var(--space-2) var(--space-3); cursor: pointer; transition: border-color var(--dur-fast) var(--ease-out); }
.obj-test-q:hover { border-color: var(--ink-3); }
.obj-test-text { flex: 1; font-size: var(--text-md); color: var(--ink); line-height: 1.45; }
.obj-copy { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--ink-3); }
.obj-kill, .obj-fix { margin: var(--space-2) 0 0; font-size: var(--text-sm); color: var(--ink); line-height: 1.55; }
.muted { color: var(--ink-3); font-size: var(--text-sm); margin: 0; }
</style>
