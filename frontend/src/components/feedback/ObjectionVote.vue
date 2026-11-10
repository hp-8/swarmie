<!-- component: inline yes/no vote on an objection
 * states: default · voted-up · voted-down · switching
 * contrast: pass
 -->
<template>
  <div class="ov-wrap" :class="{ 'ov-voted': voted !== null }">
    <span class="ov-label">Does this ring true?</span>
    <button
      type="button"
      class="ov-btn"
      :class="{ active: voted === 1 }"
      aria-label="Yes, this objection rings true"
      :disabled="loading"
      @click="castVote(1)"
    >Yes</button>
    <button
      type="button"
      class="ov-btn"
      :class="{ active: voted === -1 }"
      aria-label="No, this objection does not ring true"
      :disabled="loading"
      @click="castVote(-1)"
    >No</button>
    <transition name="ov-thanks">
      <span v-if="showThanks" class="ov-thanks" aria-live="polite">saved</span>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { trackObjectionFeedback } from '../../lib/analytics.js'

const props = defineProps({
  jobId: { type: String, required: true },
  objectionCategory: { type: String, required: true },
})

const lsKey = () => `swv:${props.jobId}:${props.objectionCategory}`

const voted = ref(null)
const loading = ref(false)
const showThanks = ref(false)

onMounted(() => {
  let stored = null
  try { stored = localStorage.getItem(lsKey()) } catch { /* storage blocked */ }
  if (stored === '1' || stored === '-1') {
    voted.value = parseInt(stored, 10)
  }
})

async function castVote(v) {
  if (loading.value) return
  // Allow switching — do not short-circuit if same value; let upsert run
  loading.value = true
  const prev = voted.value
  voted.value = v
  try { localStorage.setItem(lsKey(), String(v)) } catch { /* storage blocked */ }

  await trackObjectionFeedback(props.jobId, props.objectionCategory, v)
  loading.value = false

  if (prev !== v) {
    showThanks.value = true
    setTimeout(() => { showThanks.value = false }, 1400)
  }
}
</script>

<style scoped>
.ov-wrap {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2, 8px);
  padding-top: var(--space-3, 12px);
  margin-top: var(--space-2, 8px);
  border-top: 0;
}

.ov-label {
  font-size: var(--text-sm);
  color: var(--ink-3);
  user-select: none;
}

.ov-btn {
  background: transparent;
  border: 1px solid var(--rule, rgba(255, 255, 255, 0.12));
  border-radius: var(--radius-sm);
  padding: 2px 10px;
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 600;
  line-height: 1.6;
  cursor: pointer;
  color: var(--ink-3, rgba(255, 255, 255, 0.5));
  transition:
    border-color 140ms ease-out,
    background 140ms ease-out,
    transform 100ms ease-out;
}

.ov-btn:hover:not(:disabled) {
  border-color: var(--accent, #e05a2b);
  color: var(--ink, #fff);
}

.ov-btn:active:not(:disabled) { transform: scale(0.92); }

.ov-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.ov-btn:focus-visible {
  outline: 2px solid var(--accent, #e05a2b);
  outline-offset: 2px;
}

/* active vote state */
.ov-btn.active {
  border-color: var(--accent, #e05a2b);
  background: var(--ink);
  color: var(--paper);
}

.ov-thanks {
  font-size: var(--text-sm);
  color: var(--live);
}

/* transitions */
.ov-thanks-enter-active,
.ov-thanks-leave-active { transition: opacity 200ms ease-out; }
.ov-thanks-enter-from,
.ov-thanks-leave-to { opacity: 0; }

@media (prefers-reduced-motion: reduce) {
  .ov-btn { transition: none; }
  .ov-thanks-enter-active, .ov-thanks-leave-active { transition: none; }
}
</style>
