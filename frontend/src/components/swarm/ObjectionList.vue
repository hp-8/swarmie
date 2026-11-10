<template>
  <ol v-if="objections?.length" class="obj-list">
    <li v-for="(obj, i) in objections" :id="`objection-${i + 1}`" :key="obj.category" class="obj-row">
      <span class="obj-rank">{{ i + 1 }}</span>
      <div class="obj-body">
        <div class="obj-head-row">
          <span class="obj-cat">{{ obj.category }}</span>
          <span class="obj-count">{{ obj.count }}×</span>
        </div>
        <p v-if="obj.example_quote" class="obj-quote">"{{ obj.example_quote }}"</p>
        <dl class="obj-guide">
          <div v-if="obj.real_test" class="obj-test">
            <dt class="obj-tag">{{ copy.askTag }}</dt>
            <dd>
              <span class="obj-test-text">{{ obj.real_test }}</span>
              <button class="obj-test-q" type="button" @click="copyTest(obj)">
                {{ copiedTest === obj.category ? 'Copied' : 'Copy question' }}
              </button>
            </dd>
          </div>
          <div v-if="obj.kill_criteria" class="obj-kill">
            <dt class="obj-tag warn">{{ copy.killTag }}</dt><dd>{{ obj.kill_criteria }}</dd>
          </div>
          <div v-if="obj.suggested_fix" class="obj-fix">
            <dt class="obj-tag accent">fix</dt><dd>{{ obj.suggested_fix }}</dd>
          </div>
        </dl>
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
.obj-list { list-style: none; margin: 0; padding: 0; display: grid; }
.obj-row {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr);
  gap: var(--space-4);
  padding: var(--space-5) 0;
  border-bottom: 1px solid var(--rule);
  scroll-margin-top: var(--space-9);
}
.obj-rank { font-weight: 700; color: var(--ink-3); font-variant-numeric: tabular-nums; }
.obj-head-row { display: flex; justify-content: space-between; align-items: baseline; gap: var(--space-4); }
.obj-cat { font-size: var(--text-md); font-weight: 600; color: var(--ink); }
.obj-cat::first-letter { text-transform: uppercase; }
.obj-count { font-size: var(--text-sm); color: var(--ink-3); font-variant-numeric: tabular-nums; flex-shrink: 0; }
.obj-quote {
  margin: var(--space-2) 0 0;
  font-family: var(--font-display);
  font-size: var(--text-md);
  line-height: 1.5;
  color: var(--ink-2);
  max-width: 66ch;
}
.obj-guide { margin: var(--space-4) 0 0; display: grid; gap: var(--space-2); }
.obj-guide > div { display: grid; grid-template-columns: 112px minmax(0, 1fr); gap: var(--space-4); align-items: baseline; }
.obj-guide dd { margin: 0; line-height: 1.55; color: var(--ink-2); max-width: 62ch; }
.obj-tag { font-size: var(--text-sm); font-weight: 600; color: var(--ink-3); }
.obj-tag::first-letter { text-transform: uppercase; }
.obj-tag.warn { color: var(--warn); }
.obj-test-text { color: var(--ink); }
.obj-test-q {
  margin-left: var(--space-3);
  font: inherit;
  font-size: var(--text-sm);
  color: var(--ink-3);
  background: none;
  border: 0;
  padding: 0;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.obj-test-q:hover { color: var(--ink); }
.muted { color: var(--ink-3); }

@media (max-width: 767px) {
  .obj-row { grid-template-columns: 24px minmax(0, 1fr); gap: var(--space-3); }
  .obj-guide > div { grid-template-columns: minmax(0, 1fr); gap: 0; }
}
</style>
