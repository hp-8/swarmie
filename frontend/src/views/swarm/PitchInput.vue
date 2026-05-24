<template>
  <div class="page">
    <header class="rail">
      <router-link to="/" class="brand-mark">
        <span class="dot"></span>
        <span class="brand-text">SWARMIE</span>
      </router-link>
      <span class="rail-context">/ new roast</span>
      <a href="https://github.com/hp-8/swarmie" target="_blank" class="rail-far">github ↗</a>
    </header>

    <main class="workbench">
      <!-- LEFT rail · instrument labels -->
      <aside class="left-col">
        <div class="step">
          <div class="step-num">i.</div>
          <div class="step-label">The pitch</div>
          <div class="step-hint">
            Drop landing copy, deck text, one-pager, or a brutal one-liner.
            More context = sharper roast.
          </div>
        </div>
        <div class="step is-quiet">
          <div class="step-num">ii.</div>
          <div class="step-label">Swarm size</div>
          <div class="step-hint">
            Bigger swarm = more signal, more cost. We default to 100. 20 is
            plenty for a sanity check.
          </div>
        </div>
        <div class="step is-quiet">
          <div class="step-num">iii.</div>
          <div class="step-label">Run</div>
          <div class="step-hint">
            About 60 seconds. We stream the reactions live — you don't have
            to babysit it.
          </div>
        </div>
      </aside>

      <!-- RIGHT · canvas -->
      <section class="canvas">
        <header class="canvas-head">
          <h1 class="canvas-title h-display">What are we roasting?</h1>
          <p class="canvas-sub">
            Be specific. <em>"AI for sales"</em> is too thin to react to.
            <em>"AI inbox triage for B2B AEs hitting &gt;50 cold replies/day, $49/seat"</em>
            is a pitch.
          </p>
        </header>

        <form class="form" @submit.prevent="onSubmit">
          <label class="field-wrap">
            <div class="field-head">
              <span class="h-eyebrow">i · the pitch</span>
              <span class="field-meta">{{ pitchText.length.toLocaleString() }} / 20,000</span>
            </div>
            <textarea
              v-model="pitchText"
              class="textarea"
              rows="16"
              placeholder="Paste here. Mention the problem, the product, who it's for, pricing if you have it, and any competitors you keep getting compared to."
              :disabled="submitting"
              maxlength="20000"
            />
            <div class="field-feedback" :class="{ ok: canSubmit, warn: !canSubmit && pitchText.length > 0 }">
              {{ canSubmit ? 'Looks roastable.' : pitchText.length === 0 ? '' : 'Need at least 40 characters of context.' }}
            </div>
          </label>

          <label class="field-wrap field-wrap-row">
            <div class="field-head">
              <span class="h-eyebrow">ii · swarm size</span>
              <span class="field-meta">{{ agentCount }} agents</span>
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
            <div class="field-feedback">
              <span class="cost-est">est. cost: ~${{ costEst }}</span>
              <span class="cost-note">depends on the model you wired in <code>.env</code></span>
            </div>
          </label>

          <div v-if="error" class="error">{{ error }}</div>

          <div class="actions">
            <button class="h-btn is-accent run-btn" type="submit" :disabled="!canSubmit || submitting">
              <span v-if="submitting">Starting…</span>
              <span v-else>iii · run the swarm →</span>
            </button>
            <span class="actions-hint">{{ runHint }}</span>
          </div>
        </form>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { roastApi } from '../../api/roast'

const router = useRouter()

const pitchText = ref('')
const agentCount = ref(100)
const submitting = ref(false)
const error = ref('')

const canSubmit = computed(() => pitchText.value.trim().length >= 40)

// Rough estimate. 1 reaction ≈ 1k tokens at mini-tier. Ignores deep/synth overhead.
const costEst = computed(() => {
  const speaking = agentCount.value * 0.2   // ~20% comment+post
  const tokens = speaking * 1000 + 6000     // + parse + archetypes + synth
  const usd = (tokens / 1_000_000) * 0.6    // gpt-4o-mini-ish blended
  return usd < 0.01 ? '<0.01' : usd.toFixed(2)
})

const runHint = computed(() => {
  if (submitting.value) return 'sending pitch…'
  if (!canSubmit.value) return 'fill in the pitch first'
  return `${agentCount.value} agents · ~60s`
})

async function onSubmit() {
  if (!canSubmit.value || submitting.value) return
  error.value = ''
  submitting.value = true
  try {
    const res = await roastApi.create(pitchText.value.trim(), agentCount.value)
    const jobId = res.job_id || res.data?.job_id
    if (!jobId) throw new Error('No job_id in response')
    router.push({ name: 'Watching', params: { jobId } })
  } catch (e) {
    error.value = e?.response?.data?.error || e?.message || 'Failed to start roast'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
/* Hallmark · page: PitchInput · macrostructure: Workbench
 * archetypes: N-rail · S-stepped left · H-form-as-canvas · Ft-inline (none)
 * theme: Midnight+coral (atmospheric)
 */

.page { min-height: 100vh; color: var(--ink); }

/* Rail — slim top bar, separate from floating pill */
.rail {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--rule);
}
.brand-mark {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.22em;
}
.brand-mark .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 14px var(--accent);
}
.rail-context {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.08em;
  color: var(--ink-3);
}
.rail-far {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--ink-3);
}
.rail-far:hover { color: var(--ink); }

/* Workbench grid: left margin labels + canvas right */
.workbench {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: var(--space-8);
  max-width: var(--max-content);
  margin: 0 auto;
  padding: var(--space-8) var(--space-6) var(--space-9);
}
@media (max-width: 880px) {
  .workbench { grid-template-columns: 1fr; gap: var(--space-6); padding-top: var(--space-6); }
}

.left-col {
  position: sticky;
  top: var(--space-6);
  align-self: start;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}
.step { padding-right: var(--space-4); }
.step.is-quiet { opacity: 0.55; }
.step-num {
  font-family: var(--font-display);
  font-style: italic;
  font-size: var(--text-xl);
  color: var(--accent-bright);
  margin-bottom: var(--space-2);
}
.step-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink);
  margin-bottom: var(--space-2);
}
.step-hint { font-family: var(--font-body); font-size: var(--text-sm); color: var(--ink-2); line-height: 1.6; }

@media (max-width: 880px) {
  .left-col { position: static; flex-direction: row; flex-wrap: wrap; }
  .step { flex: 1; min-width: 180px; }
}

/* Canvas */
.canvas-head { margin-bottom: var(--space-7); max-width: 640px; }
.canvas-title {
  font-size: clamp(40px, 6vw, 64px);
  font-weight: 500;
  font-variation-settings: 'opsz' 144, 'wght' 500;
  margin: 0 0 var(--space-3);
  color: var(--ink);
}
.canvas-sub {
  font-family: var(--font-body);
  color: var(--ink);
  font-size: var(--text-md);
  line-height: 1.6;
  margin: 0;
}
.canvas-sub em { color: var(--accent-bright); font-style: italic; }

.form { display: flex; flex-direction: column; gap: var(--space-6); }

.field-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.field-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--space-3);
}
.field-meta {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--ink-3);
}

.textarea {
  width: 100%;
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  color: var(--ink);
  font: 15px/1.65 var(--font-mono);
  resize: vertical;
  min-height: 320px;
  transition: border-color var(--dur-base) var(--ease-out), background var(--dur-base) var(--ease-out);
}
.textarea::placeholder { color: var(--ink-4); }
.textarea:focus {
  border-color: var(--accent);
  background: color-mix(in oklch, var(--paper-2) 92%, var(--accent-soft));
}
.textarea:disabled { opacity: 0.5; }

.field-feedback {
  display: flex;
  gap: var(--space-3);
  align-items: center;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--ink-3);
  min-height: 16px;
}
.field-feedback.ok { color: var(--live); }
.field-feedback.warn { color: var(--warn); }

.size-row {
  display: flex;
  gap: var(--space-5);
  align-items: center;
  flex-wrap: wrap;
}
.size-slider {
  flex: 1;
  min-width: 220px;
  appearance: none;
  height: 4px;
  background: var(--paper-3);
  border-radius: var(--radius-pill);
  outline: none;
}
.size-slider::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent);
  border: 2px solid var(--paper);
  cursor: pointer;
  box-shadow: 0 0 0 1px var(--accent);
  transition: transform var(--dur-fast) var(--ease-out);
}
.size-slider::-webkit-slider-thumb:hover { transform: scale(1.15); }
.size-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent);
  border: 2px solid var(--paper);
  cursor: pointer;
}

.size-presets {
  display: flex;
  gap: var(--space-2);
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius-pill);
  padding: 4px;
}
.size-presets button {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.05em;
  padding: 6px 12px;
  border: none;
  background: transparent;
  color: var(--ink-2);
  border-radius: var(--radius-pill);
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease-out);
}
.size-presets button:hover { color: var(--ink); }
.size-presets button.active {
  background: var(--accent);
  color: var(--paper);
}

.cost-est { color: var(--ink-2); }
.cost-note code {
  background: var(--paper-3);
  padding: 0 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
}

.error {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  padding: var(--space-4);
  color: var(--warn);
  background: var(--warn-soft);
  border: 1px solid color-mix(in oklch, var(--warn) 50%, transparent);
  border-radius: var(--radius-md);
}

.actions {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-wrap: wrap;
  margin-top: var(--space-3);
}
.run-btn { padding: 16px 28px; font-size: var(--text-md); }
.actions-hint {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.06em;
  color: var(--ink-3);
}
</style>
