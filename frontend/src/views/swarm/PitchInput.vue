<template>
  <div class="page page-fixed">
    <header class="rail">
      <router-link to="/" class="brand-mark">
        <span class="dot"></span>
        <span class="brand-text">SWARMIE</span>
      </router-link>
      <span class="rail-context">/ new roast</span>
      <a href="https://github.com/hp-8/swarmie" target="_blank" class="rail-far">github ↗</a>
    </header>

    <main class="workbench">
      <aside class="left-col">
        <div class="step">
          <div class="step-num">i.</div>
          <div class="step-label">The pitch</div>
          <div class="step-hint">Landing copy, deck, one-pager. Be specific.</div>
        </div>
        <div class="step is-quiet">
          <div class="step-num">ii.</div>
          <div class="step-label">Swarm size</div>
          <div class="step-hint">Bigger = more signal, more cost.</div>
        </div>
        <div class="step is-quiet">
          <div class="step-num">iii.</div>
          <div class="step-label">Run</div>
          <div class="step-hint">~60s. Streams live.</div>
        </div>
      </aside>

      <section class="canvas">
        <header class="canvas-head">
          <h1 class="canvas-title h-display">What are we roasting?</h1>
          <p class="canvas-sub">
            <em>"AI for sales"</em> is too thin. <em>"AI inbox triage for B2B AEs hitting &gt;50 cold replies/day, $49/seat"</em> is a pitch.
          </p>
        </header>

        <form class="form" @submit.prevent="onSubmit">
          <label class="field-wrap field-pitch">
            <div class="field-head">
              <span class="h-eyebrow">i · the pitch</span>
              <div class="field-head-right">
                <button v-if="!pitchText.trim()" type="button" class="template-btn" @click="fillTemplate">use template</button>
                <span class="field-meta">{{ pitchText.length.toLocaleString() }} / 20,000</span>
              </div>
            </div>
            <textarea
              v-model="pitchText"
              class="textarea"
              :placeholder="pitchPlaceholder"
              :disabled="submitting"
              maxlength="20000"
            />
            <div class="pitch-checklist">
              <span class="check-item" :class="{ done: hasSection('problem') }">problem</span>
              <span class="check-item" :class="{ done: hasSection('product') }">product</span>
              <span class="check-item" :class="{ done: hasSection('audience') }">audience</span>
              <span class="check-item" :class="{ done: hasSection('pricing') }">pricing</span>
              <span class="check-item" :class="{ done: hasSection('competitor') }">competitors</span>
            </div>
          </label>

          <div class="field-wrap field-size">
            <div class="field-head">
              <span class="h-eyebrow">ii · swarm size</span>
              <span class="field-meta">{{ agentCount }} agents · est. ${{ costEst }}</span>
            </div>
            <div class="size-row">
              <input
                v-model.number="agentCount"
                class="size-slider"
                type="range"
                min="20"
                max="500"
                step="10"
                :disabled="submitting"
              />
              <div class="size-presets">
                <button type="button" @click="agentCount = 20" :class="{ active: agentCount === 20 }">20</button>
                <button type="button" @click="agentCount = 100" :class="{ active: agentCount === 100 }">100</button>
                <button type="button" @click="agentCount = 250" :class="{ active: agentCount === 250 }">250</button>
                <button type="button" @click="agentCount = 500" :class="{ active: agentCount === 500 }">500</button>
              </div>
            </div>
          </div>

          <div v-if="error" class="error">{{ error }}</div>

          <div class="actions">
            <button class="h-btn is-accent run-btn" type="submit" :disabled="!canSubmit || submitting">
              <span v-if="submitting">Starting…</span>
              <span v-else>iii · run the swarm →</span>
            </button>
            <span class="actions-hint">{{ runHint }}</span>
          </div>

          <p class="ai-note">
            Reactions are produced by AI agents — <em>not real users</em>.
            <AiDisclosure variant="text" label="how this was generated" />
          </p>
        </form>
      </section>
    </main>

    <!-- Launch overlay -->
    <transition name="launch">
      <div v-if="launching" class="launch-overlay">
        <div class="launch-content">
          <div class="launch-ring"></div>
          <div class="launch-text">
            <span class="launch-label">Assembling the swarm</span>
            <span class="launch-sub">{{ agentCount }} agents · parsing your pitch</span>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { roastApi } from '../../api/roast'
import AiDisclosure from '../../components/AiDisclosure.vue'
import { trackRoastStart } from '../../lib/analytics'

const router = useRouter()
const pitchText = ref('')
const agentCount = ref(100)
const submitting = ref(false)
const launching = ref(false)
const error = ref('')

const canSubmit = computed(() => pitchText.value.trim().length >= 40)

const pitchPlaceholder = `PROBLEM: What pain are you solving? Who feels it?

PRODUCT: What does your product do? One-liner + key features.

AUDIENCE: Who is this for? Be specific — role, company size, industry.

PRICING: How much? Free tier? Per-seat? Usage-based?

COMPETITORS: Who else solves this? Why are you different?`

const TEMPLATE = `PROBLEM:

PRODUCT:

AUDIENCE:

PRICING:

COMPETITORS: `

function fillTemplate() {
  pitchText.value = TEMPLATE
}

function hasSection(key) {
  const t = pitchText.value.toLowerCase()
  const patterns = {
    problem: /problem[:\s].*\S/,
    product: /product[:\s].*\S/,
    audience: /audience[:\s].*\S|target[:\s].*\S|who[:\s].*\S|icp[:\s].*\S/,
    pricing: /pric(e|ing)[:\s].*\S|\$\d/,
    competitor: /competitor[:\s].*\S|vs\.?\s|alternative|compared to/,
  }
  return patterns[key]?.test(t) || false
}

const costEst = computed(() => {
  const speaking = agentCount.value * 0.2
  const tokens = speaking * 1000 + 6000
  const usd = (tokens / 1_000_000) * 0.6
  return usd < 0.01 ? '<0.01' : usd.toFixed(2)
})

const runHint = computed(() => {
  if (submitting.value) return 'sending…'
  if (!canSubmit.value) return 'fill the pitch first'
  return `${agentCount.value} agents · ~60s`
})

async function onSubmit() {
  if (!canSubmit.value || submitting.value) return
  error.value = ''
  submitting.value = true
  launching.value = true
  try {
    const res = await roastApi.create(pitchText.value.trim(), agentCount.value)
    const jobId = res.job_id || res.data?.job_id
    if (!jobId) throw new Error('No job_id in response')
    trackRoastStart(jobId, { pitchLength: pitchText.value.trim().length }).catch(() => {})
    await new Promise(r => setTimeout(r, 800))
    router.push({ name: 'Watching', params: { jobId } })
  } catch (e) {
    error.value = e?.response?.data?.error || e?.message || 'Failed to start roast'
    launching.value = false
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
/* Hallmark · page: PitchInput · macrostructure: Workbench (fixed-viewport)
 * theme: Midnight+coral (atmospheric)
 */

.page { color: var(--ink); background: var(--paper); }

.rail {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-6);
  border-bottom: 1px solid var(--rule);
  flex-shrink: 0;
}
.brand-mark {
  display: inline-flex; align-items: center; gap: var(--space-2);
  font-family: var(--font-mono); font-size: var(--text-xs);
  font-weight: 600; letter-spacing: 0.22em;
}
.brand-mark .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 14px var(--accent); }
.rail-context { font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.08em; color: var(--ink-2); }
.rail-far { margin-left: auto; font-family: var(--font-mono); font-size: var(--text-xs); color: var(--ink-2); }
.rail-far:hover { color: var(--ink); }

.workbench {
  flex: 1;
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: var(--space-7);
  max-width: var(--max-content);
  width: 100%;
  margin: 0 auto;
  padding: var(--space-6) var(--space-6);
  min-height: 0;
  overflow: hidden;
}
@media (max-width: 880px) {
  .workbench { grid-template-columns: 1fr; gap: var(--space-3); padding: var(--space-4); }
}

.left-col {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  align-self: start;
}
.step { padding-right: var(--space-3); }
.step.is-quiet { opacity: 0.55; }
.step-num {
  font-family: var(--font-display); font-style: italic; font-weight: 500;
  font-variation-settings: 'opsz' 96, 'wght' 500;
  font-size: var(--text-lg); color: var(--accent-bright); margin-bottom: var(--space-1);
}
.step-label {
  font-family: var(--font-mono); font-size: var(--text-xs);
  letter-spacing: 0.16em; text-transform: uppercase; color: var(--ink); margin-bottom: var(--space-1);
}
.step-hint { font-family: var(--font-body); font-size: var(--text-sm); color: var(--ink-2); line-height: 1.55; }

@media (max-width: 880px) {
  .left-col { flex-direction: row; flex-wrap: wrap; }
  .step { flex: 1; min-width: 140px; }
}

.canvas {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
.canvas-head { margin-bottom: var(--space-4); max-width: 640px; flex-shrink: 0; }
.canvas-title {
  font-size: clamp(28px, 4.5vw, 44px);
  font-weight: 500; font-variation-settings: 'opsz' 144, 'wght' 500;
  margin: 0 0 var(--space-2); color: var(--ink);
}
.canvas-sub {
  font-family: var(--font-body);
  color: var(--ink-2); font-size: var(--text-sm); line-height: 1.5; margin: 0;
}
.canvas-sub em { color: var(--accent-bright); font-style: italic; }

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  min-height: 0;
  flex: 1;
}

.field-wrap { display: flex; flex-direction: column; gap: var(--space-2); }
.field-pitch { flex: 1; min-height: 0; }

.field-head {
  display: flex; justify-content: space-between; align-items: baseline; gap: var(--space-3);
}
.field-head-right { display: flex; align-items: baseline; gap: var(--space-3); }
.field-meta { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--ink-3); }

.template-btn {
  font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.06em;
  padding: 4px 10px; background: transparent;
  border: 1px solid var(--rule-2); color: var(--accent-bright);
  border-radius: var(--radius-pill); cursor: pointer;
  transition: all var(--dur-fast) var(--ease-out);
}
.template-btn:hover { border-color: var(--accent); background: var(--accent-soft); }

.pitch-checklist {
  display: flex; gap: var(--space-2); flex-wrap: wrap; padding-top: var(--space-1);
}
.check-item {
  font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.1em;
  text-transform: uppercase; padding: 3px 8px;
  border-radius: var(--radius-pill); border: 1px solid var(--rule);
  color: var(--ink-4); transition: all var(--dur-base) var(--ease-out);
}
.check-item.done {
  color: var(--live); border-color: color-mix(in oklch, var(--live) 40%, transparent);
  background: color-mix(in oklch, var(--live) 8%, transparent);
}

.textarea {
  width: 100%;
  flex: 1;
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  padding: var(--space-4) var(--space-5);
  color: var(--ink);
  font: 14px/1.6 var(--font-mono);
  resize: none;
  min-height: 0;
  transition: border-color var(--dur-base) var(--ease-out), background var(--dur-base) var(--ease-out);
}
.textarea::placeholder { color: var(--ink-4); }
.textarea:focus {
  outline: none;
  border-color: var(--accent);
  background: color-mix(in oklch, var(--paper-2) 92%, var(--accent-soft));
}
.textarea:disabled { opacity: 0.5; }

.size-row { display: flex; gap: var(--space-4); align-items: center; flex-wrap: wrap; }
.size-slider {
  flex: 1; min-width: 200px;
  appearance: none; height: 4px;
  background: var(--paper-3); border-radius: var(--radius-pill); outline: none;
}
.size-slider::-webkit-slider-thumb {
  appearance: none; width: 18px; height: 18px; border-radius: 50%;
  background: var(--accent); border: 2px solid var(--paper);
  cursor: pointer; box-shadow: 0 0 0 1px var(--accent);
  transition: transform var(--dur-fast) var(--ease-out);
}
.size-slider::-webkit-slider-thumb:hover { transform: scale(1.15); }
.size-slider::-moz-range-thumb {
  width: 18px; height: 18px; border-radius: 50%;
  background: var(--accent); border: 2px solid var(--paper); cursor: pointer;
}

.size-presets {
  display: flex; gap: 4px;
  background: var(--paper-2); border: 1px solid var(--rule);
  border-radius: var(--radius-pill); padding: 3px;
}
.size-presets button {
  font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.05em;
  padding: 5px 11px; border: none; background: transparent; color: var(--ink-2);
  border-radius: var(--radius-pill); cursor: pointer;
  transition: all var(--dur-fast) var(--ease-out);
}
.size-presets button:hover { color: var(--ink); }
.size-presets button.active { background: var(--accent); color: var(--paper); }

.error {
  font-family: var(--font-mono); font-size: var(--text-sm);
  padding: var(--space-3) var(--space-4); color: var(--warn);
  background: var(--warn-soft);
  border: 1px solid color-mix(in oklch, var(--warn) 50%, transparent);
  border-radius: var(--radius-md);
}

.actions {
  display: flex; align-items: center; gap: var(--space-4); flex-wrap: wrap;
}
.run-btn { padding: 14px 24px; font-size: var(--text-base); }
.actions-hint {
  font-family: var(--font-mono); font-size: var(--text-xs);
  letter-spacing: 0.06em; color: var(--ink-3);
}
.ai-note {
  margin: var(--space-3) 0 0;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.04em;
  color: var(--ink-3);
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.ai-note em { font-style: italic; color: var(--ink); }

/* Launch overlay */
.launch-overlay {
  position: fixed; inset: 0; z-index: 100;
  background: var(--paper);
  display: flex; align-items: center; justify-content: center;
}
.launch-content {
  display: flex; flex-direction: column; align-items: center; gap: var(--space-5);
}
.launch-ring {
  width: 56px; height: 56px; border-radius: 50%;
  border: 2px solid var(--rule);
  border-top-color: var(--accent);
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.launch-text { text-align: center; display: flex; flex-direction: column; gap: var(--space-1); }
.launch-label {
  font-family: var(--font-display); font-style: italic; font-weight: 500;
  font-size: var(--text-xl); color: var(--ink);
}
.launch-sub {
  font-family: var(--font-mono); font-size: var(--text-xs);
  letter-spacing: 0.08em; color: var(--ink-3);
}

.launch-enter-active { animation: launch-in 300ms var(--ease-out); }
.launch-leave-active { animation: launch-out 200ms var(--ease-out); }
@keyframes launch-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes launch-out {
  from { opacity: 1; }
  to { opacity: 0; }
}
</style>
