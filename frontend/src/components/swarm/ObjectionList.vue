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
.obj-list {
  list-style: none; margin: 0; padding: 2px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(360px, 100%), 1fr));
  gap: var(--space-3);
  align-content: start;
}
.obj-row {
  display: grid; grid-template-columns: 30px 1fr; gap: var(--space-3);
  align-items: start;
  background: var(--paper-3);
  border: 1px solid var(--rule);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  box-shadow: inset 0 1px 0 color-mix(in oklch, white 4%, transparent);
}
.obj-rank {
  font-family: var(--font-display); font-style: normal; font-weight: 600;
  font-size: var(--text-2xl); color: var(--accent-bright); line-height: 0.9;
}
.obj-head-row { display: flex; justify-content: space-between; align-items: baseline; gap: var(--space-3); margin-bottom: var(--space-1); }
.obj-cat { font-family: var(--font-mono); font-size: var(--text-sm); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--ink); }
.obj-count { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--ink-3); flex-shrink: 0; }
.obj-quote {
  font-family: var(--font-display); font-style: normal; font-weight: 500;
  font-variation-settings: 'opsz' 96, 'wght' 500;
  font-size: var(--text-sm); line-height: 1.4; color: var(--ink-2); margin: 0;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
}
.obj-tag { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink-3); margin-right: var(--space-2); padding: 1px 5px; border: 1px solid var(--rule); border-radius: 4px; white-space: nowrap; }
.obj-tag.warn { color: var(--warn); border-color: color-mix(in oklch, var(--warn) 35%, transparent); }
.obj-tag.accent { color: var(--accent-bright); border-color: color-mix(in oklch, var(--accent) 35%, transparent); }
.obj-test { margin-top: var(--space-3); }
.obj-test-q {
  display: flex; align-items: center; gap: var(--space-3);
  width: 100%; text-align: left;
  background: color-mix(in oklch, var(--accent) 7%, var(--paper));
  border: 1px solid color-mix(in oklch, var(--accent) 22%, transparent);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  cursor: pointer;
  transition: border-color var(--dur-fast) var(--ease-out),
              background var(--dur-fast) var(--ease-out);
}
.obj-test-q:hover {
  border-color: color-mix(in oklch, var(--accent) 50%, transparent);
  background: color-mix(in oklch, var(--accent) 11%, var(--paper));
}
.obj-test-q:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
/* "GET PROOF" tag — filled coral micro-pill, not the outlined gray default */
.obj-test-q .obj-tag {
  align-self: flex-start;
  margin-right: 0;
  color: var(--accent-bright);
  border-color: transparent;
  background: var(--accent-soft);
}
.obj-test-text {
  flex: 1; min-width: 0; font-size: var(--text-sm); color: var(--ink); line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.obj-copy {
  flex-shrink: 0;
  width: 28px; height: 28px;
  display: grid; place-items: center;
  border-radius: 50%;
  background: color-mix(in oklch, var(--ink) 8%, transparent);
  color: var(--ink-2);
  font-size: 13px; line-height: 1;
  transition: background var(--dur-fast) var(--ease-out),
              color var(--dur-fast) var(--ease-out),
              transform var(--dur-fast) var(--ease-out);
}
.obj-test-q:hover .obj-copy { background: var(--accent-soft); color: var(--accent-bright); transform: translateY(-1px); }
.obj-kill, .obj-fix {
  margin: var(--space-2) 0 0; font-size: var(--text-xs); color: var(--ink-3); line-height: 1.45;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.muted { color: var(--ink-3); font-size: var(--text-sm); margin: 0; }
</style>
