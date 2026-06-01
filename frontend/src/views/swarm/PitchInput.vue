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
        <div class="swarm-picker" role="tablist" aria-label="Choose a swarm">
          <button
            v-for="s in SWARMS"
            :key="s.key"
            type="button"
            role="tab"
            class="swarm-tab"
            :class="{ active: s.key === swarmType, locked: !s.enabled }"
            :aria-selected="s.key === swarmType"
            :disabled="!s.enabled || submitting"
            @click="selectSwarm(s)"
          >
            <span class="swarm-tab-label">{{ s.label }}</span>
            <span v-if="!s.enabled" class="swarm-tab-soon">soon</span>
          </button>
        </div>

        <header class="canvas-head">
          <h1 class="canvas-title h-display">{{ activeSwarm.title }}</h1>
          <p class="canvas-sub" v-html="activeSwarm.sub"></p>
        </header>

        <form class="form" @submit.prevent="onSubmit">
          <label class="field-wrap field-pitch">
            <div class="field-head">
              <span class="h-eyebrow">i · {{ swarmType === 'investor' ? 'the deck' : 'the pitch' }}</span>
              <div class="field-head-right">
                <button v-if="!pitchText.trim() && !deckFile" type="button" class="template-btn" @click="fillTemplate">use template</button>
                <span class="field-meta">{{ pitchText.length.toLocaleString() }} / 20,000</span>
              </div>
            </div>
            <textarea
              v-model="pitchText"
              class="textarea"
              :placeholder="activeSwarm.placeholder"
              :disabled="submitting || !!deckFile"
              maxlength="20000"
            />

            <!-- PDF dropzone — investor swarm only -->
            <div v-if="swarmType === 'investor'" class="dropzone-wrap">
              <div class="dropzone-or"><span class="h-eyebrow">or drop a PDF deck</span></div>
              <div
                class="dropzone"
                :class="{
                  'dz-dragover': dzDragover,
                  'dz-filled': !!deckFile,
                  'dz-error': !!dzError,
                  'dz-disabled': submitting,
                }"
                role="button"
                tabindex="0"
                :aria-label="deckFile ? 'PDF selected: ' + deckFile.name + '. Press to change.' : 'Drop a PDF or click to browse'"
                :aria-disabled="submitting ? 'true' : undefined"
                @click="!submitting && $refs.fileInput.click()"
                @keydown.enter.space.prevent="!submitting && $refs.fileInput.click()"
                @dragenter.prevent="!submitting && (dzDragover = true)"
                @dragover.prevent="!submitting && (dzDragover = true)"
                @dragleave.prevent="dzDragover = false"
                @drop.prevent="onFileDrop"
              >
                <input
                  ref="fileInput"
                  type="file"
                  accept="application/pdf"
                  class="dz-hidden-input"
                  :disabled="submitting"
                  @change="onFileChange"
                />
                <template v-if="deckFile">
                  <div class="dz-file-info">
                    <span class="dz-filename">{{ deckFile.name }}</span>
                    <span class="dz-size">{{ formatFileSize(deckFile.size) }}</span>
                  </div>
                  <button type="button" class="dz-clear" :disabled="submitting" @click.stop="clearDeck" aria-label="Remove PDF">
                    <span aria-hidden="true">x</span> clear
                  </button>
                </template>
                <template v-else>
                  <div class="dz-prompt">
                    <span class="dz-icon" aria-hidden="true">&#8593;</span>
                    <span class="dz-label">drop PDF or click to browse</span>
                    <span class="dz-hint">PDF only &middot; max 25 MB</span>
                  </div>
                </template>
              </div>
              <p v-if="dzError" class="dz-error-msg" role="alert">{{ dzError }}</p>
            </div>

            <div class="pitch-checklist" v-if="!deckFile">
              <span
                v-for="c in activeSwarm.checks"
                :key="c.key"
                class="check-item"
                :class="{ done: hasSection(c) }"
              >{{ c.label }}</span>
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
            <span class="launch-sub">{{ agentCount }} {{ activeSwarm.agentNoun }} · {{ deckFile ? 'reading your deck' : 'parsing your pitch' }}</span>
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
const swarmType = ref('validate')
const pitchText = ref('')
const agentCount = ref(100)
const submitting = ref(false)
const launching = ref(false)
const error = ref('')

// Deck dropzone state
const deckFile = ref(null)
const dzDragover = ref(false)
const dzError = ref('')
const fileInput = ref(null)

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function validateAndSetFile(file) {
  dzError.value = ''
  if (!file) return
  if (file.type !== 'application/pdf') {
    dzError.value = 'Only PDF files are accepted. Try dropping a .pdf deck.'
    return
  }
  if (file.size > 25 * 1024 * 1024) {
    dzError.value = 'File is too large. Max 25 MB.'
    return
  }
  deckFile.value = file
}

function onFileChange(e) {
  const file = e.target.files?.[0]
  validateAndSetFile(file)
  // Reset input so same file can be re-selected after clearing
  if (fileInput.value) fileInput.value.value = ''
}

function onFileDrop(e) {
  dzDragover.value = false
  if (submitting.value) return
  const file = e.dataTransfer?.files?.[0]
  validateAndSetFile(file)
}

function clearDeck() {
  deckFile.value = null
  dzError.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

// Each swarm answers one founder decision and carries its own input voice.
// `enabled: false` shows the option as "soon" — Launch ships with the signal layer.
const SWARMS = [
  {
    key: 'validate',
    label: 'Validate',
    blurb: 'Will the market care?',
    enabled: true,
    agentNoun: 'agents',
    title: 'What are we roasting?',
    sub: '<em>"AI for sales"</em> is too thin. <em>"AI inbox triage for B2B AEs hitting &gt;50 cold replies/day, $49/seat"</em> is a pitch.',
    placeholder: `PROBLEM: What pain are you solving? Who feels it?

PRODUCT: What does your product do? One-liner + key features.

AUDIENCE: Who is this for? Be specific — role, company size, industry.

PRICING: How much? Free tier? Per-seat? Usage-based?

COMPETITORS: Who else solves this? Why are you different?`,
    template: `PROBLEM:\n\nPRODUCT:\n\nAUDIENCE:\n\nPRICING:\n\nCOMPETITORS: `,
    checks: [
      { key: 'problem', label: 'problem', pattern: /problem[:\s].*\S/ },
      { key: 'product', label: 'product', pattern: /product[:\s].*\S/ },
      { key: 'audience', label: 'audience', pattern: /audience[:\s].*\S|target[:\s].*\S|who[:\s].*\S|icp[:\s].*\S/ },
      { key: 'pricing', label: 'pricing', pattern: /pric(e|ing)[:\s].*\S|\$\d/ },
      { key: 'competitor', label: 'competitors', pattern: /competitor[:\s].*\S|vs\.?\s|alternative|compared to/ },
    ],
  },
  {
    key: 'investor',
    label: 'Investor',
    blurb: 'Is it fundable?',
    enabled: true,
    agentNoun: 'investors',
    title: 'What deck are we stress-testing?',
    sub: 'A swarm of investor archetypes reads your deck like inbox #47. You get the likely questions, the missing proof, and the pass reasons before a real partner does.',
    placeholder: `PROBLEM: What pain, and why is it urgent now?

SOLUTION: The product + the wedge. Why you win.

MARKET: How big, and why venture-scale?

TRACTION: Revenue, users, growth, retention — real numbers.

TEAM: Who you are, why you'll win this.

RAISE: Stage + amount + what it buys.`,
    template: `PROBLEM:\n\nSOLUTION:\n\nMARKET:\n\nTRACTION:\n\nTEAM:\n\nRAISE: `,
    checks: [
      { key: 'problem', label: 'problem', pattern: /problem[:\s].*\S/ },
      { key: 'market', label: 'market', pattern: /market[:\s].*\S|tam[:\s].*\S/ },
      { key: 'traction', label: 'traction', pattern: /traction[:\s].*\S|revenue|users|mrr|arr|growth|retention/ },
      { key: 'team', label: 'team', pattern: /team[:\s].*\S|founder[:\s].*\S/ },
      { key: 'raise', label: 'raise', pattern: /rais(e|ing)[:\s].*\S|round[:\s].*\S|pre-?seed|seed|series\s/ },
    ],
  },
  {
    key: 'launch',
    label: 'Launch',
    blurb: 'soon',
    enabled: false,
    agentNoun: 'agents',
  },
]

const activeSwarm = computed(() => SWARMS.find(s => s.key === swarmType.value) || SWARMS[0])

function selectSwarm(s) {
  if (!s.enabled || submitting.value) return
  swarmType.value = s.key
}

const canSubmit = computed(() => {
  if (swarmType.value === 'investor' && deckFile.value) return true
  return pitchText.value.trim().length >= 40
})

function fillTemplate() {
  pitchText.value = activeSwarm.value.template
}

function hasSection(check) {
  return check.pattern?.test(pitchText.value.toLowerCase()) || false
}

const costEst = computed(() => {
  const speaking = agentCount.value * 0.2
  const tokens = speaking * 1000 + 6000
  const usd = (tokens / 1_000_000) * 0.6
  return usd < 0.01 ? '<0.01' : usd.toFixed(2)
})

const runHint = computed(() => {
  if (submitting.value) return 'sending…'
  if (!canSubmit.value) return deckFile.value ? 'PDF ready' : 'fill the pitch first'
  if (deckFile.value) return `${agentCount.value} ${activeSwarm.value.agentNoun} · deck mode · ~90s`
  return `${agentCount.value} ${activeSwarm.value.agentNoun} · ~60s`
})

async function onSubmit() {
  if (!canSubmit.value || submitting.value) return
  error.value = ''
  submitting.value = true
  launching.value = true
  try {
    const isDeck = swarmType.value === 'investor' && !!deckFile.value
    const res = isDeck
      ? await roastApi.createDeck(deckFile.value, agentCount.value, swarmType.value)
      : await roastApi.create(pitchText.value.trim(), agentCount.value, swarmType.value)
    const jobId = res.job_id || res.data?.job_id
    if (!jobId) throw new Error('No job_id in response')
    trackRoastStart(jobId, {
      pitchText: isDeck ? null : pitchText.value.trim(),
      pitchLength: isDeck ? null : pitchText.value.trim().length,
      nAgents: agentCount.value,
      swarmType: swarmType.value,
      source: isDeck ? 'deck' : 'text',
    }).catch(() => {})
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
/* Swarm picker — compact segmented control. One swarm = one founder decision.
 * Label-only: the active swarm's purpose is carried by the canvas title + sub. */
.swarm-picker {
  display: inline-flex;
  gap: 3px;
  margin-bottom: var(--space-4);
  padding: 3px;
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius-pill);
  flex-shrink: 0;
  align-self: start;
}
.swarm-tab {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 7px 16px;
  background: transparent;
  border: none;
  border-radius: var(--radius-pill);
  color: var(--ink-2);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out),
              color var(--dur-fast) var(--ease-out),
              transform var(--dur-fast) var(--ease-out);
}
.swarm-tab:hover:not(:disabled) { color: var(--ink); }
.swarm-tab:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.swarm-tab:active:not(:disabled) { transform: translateY(1px); }
.swarm-tab.active {
  background: var(--accent);
  color: var(--paper);
}
.swarm-tab.locked { opacity: 0.4; cursor: not-allowed; }
.swarm-tab-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-weight: 600;
}
.swarm-tab-soon {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-4);
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

/* Dropzone */
.dropzone-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex-shrink: 0;
}
.dropzone-or {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--ink-4);
}
.dropzone-or::before,
.dropzone-or::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--rule);
}

.dz-hidden-input {
  display: none;
}

.dropzone {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--paper-2);
  border: 1px dashed var(--rule-2);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition:
    border-color var(--dur-base) var(--ease-out),
    background var(--dur-base) var(--ease-out);
  min-height: 64px;
  user-select: none;
  outline: none;
}
.dropzone:hover:not(.dz-disabled) {
  border-color: var(--ink-3);
  background: color-mix(in oklch, var(--paper-2) 85%, var(--paper-3));
}
.dropzone:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 2px;
  border-radius: var(--radius-lg);
}
.dropzone:active:not(.dz-disabled) {
  background: var(--paper-3);
}
.dropzone.dz-dragover {
  border-color: var(--accent);
  border-style: solid;
  background: var(--accent-soft);
}
.dropzone.dz-filled {
  border-style: solid;
  border-color: var(--live);
  background: var(--live-soft);
}
.dropzone.dz-error {
  border-color: var(--warn);
  background: var(--warn-soft);
}
.dropzone.dz-disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.dz-prompt {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.dz-icon {
  display: none;
}
.dz-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-3);
}
.dz-hint {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.06em;
  color: var(--ink-4);
}

.dz-file-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.dz-filename {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.06em;
  color: var(--live);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dz-size {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.08em;
  color: var(--ink-4);
}

.dz-clear {
  flex-shrink: 0;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 4px 10px;
  background: transparent;
  border: 1px solid color-mix(in oklch, var(--live) 40%, transparent);
  color: var(--live);
  border-radius: var(--radius-pill);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.dz-clear:hover { background: var(--live-soft); }
.dz-clear:disabled { opacity: 0.4; cursor: not-allowed; }

.dz-error-msg {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.04em;
  color: var(--warn);
  margin: 0;
}

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
