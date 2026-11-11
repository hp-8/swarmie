<template>
  <div class="page">
    <header class="rail">
      <router-link to="/" class="brand-mark">Swarmie</router-link>
      <span class="rail-context">New submission</span>
      <a href="https://github.com/hp-8/swarmie" target="_blank" rel="noopener" class="rail-far">GitHub</a>
    </header>

    <main class="desk">
      <form class="sheet" @submit.prevent="onSubmit">
        <section class="sub-main">
          <h1 class="sub-title">{{ activeSwarm.title }}</h1>
          <p class="sub-lede">{{ activeSwarm.sub }}</p>

          <div class="field-wrap field-pitch">
            <div class="field-head">
              <label for="pitch" class="field-label">{{ swarmType === 'investor' ? 'Deck or pitch' : 'Pitch' }}</label>
              <div class="field-head-right">
                <button v-if="!pitchText.trim() && !deckFile" type="button" class="template-btn" @click="fillTemplate">Use the template</button>
                <span class="field-meta">{{ pitchText.length.toLocaleString() }} / 20,000</span>
              </div>
            </div>
            <textarea
              id="pitch"
              v-model="pitchText"
              data-clarity-mask="true"
              class="textarea"
              :placeholder="activeSwarm.placeholder"
              :disabled="submitting || !!deckFile"
              maxlength="20000"
            />

            <DeckDropzone v-if="swarmType === 'investor'" v-model:file="deckFile" :disabled="submitting" />

            <ul v-if="!deckFile" class="pitch-checklist" aria-label="Sections the panel looks for">
              <li
                v-for="c in activeSwarm.checks"
                :key="c.key"
                class="check-item"
                :class="{ done: hasSection(c) }"
              >{{ c.label.charAt(0).toUpperCase() + c.label.slice(1) }}<span class="sr-only">{{ hasSection(c) ? ' covered' : ' missing' }}</span></li>
            </ul>
          </div>
        </section>

        <aside class="sub-side">
          <fieldset class="side-block">
            <legend class="field-label">Review type</legend>
            <div class="swarm-picker" role="tablist" aria-label="Choose a review type">
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
                {{ s.label }}<span v-if="!s.enabled" class="swarm-tab-soon"> (soon)</span><span v-else-if="isLocked(s)" class="swarm-tab-pack">Pack</span>
              </button>
            </div>
          </fieldset>

          <div class="side-block field-wrap field-size">
            <div class="field-head">
              <label for="size" class="field-label">Panel size</label>
              <span class="field-meta">{{ agentCount }} reviewers · {{ sizeNote }}</span>
            </div>
            <input
              id="size"
              v-model.number="agentCount"
              class="size-slider"
              type="range"
              min="20"
              max="500"
              step="10"
              :disabled="submitting"
            />
            <div class="size-presets">
              <button v-for="n in [20, 100, 250, 500]" :key="n" type="button" :class="{ active: agentCount === n }" @click="agentCount = n">{{ n }}</button>
            </div>
          </div>

          <div v-if="locked" class="pack-note">
            <p class="pack-title">{{ activeSwarm.label }} reviews come with review packs.</p>
            <p class="pack-copy">The free tier covers Validate reviews. Investor and Launch reviews, larger panels and PDF export are part of packs, launching soon.</p>
            <router-link :to="{ path: '/', hash: '#pricing' }" class="pack-link">See planned pricing</router-link>
          </div>

          <div v-if="error" class="error" role="alert">
            {{ error }}
            <router-link v-if="errorCode === 'sign_in_required'" to="/signin" class="error-link">Sign in</router-link>
            <router-link v-else-if="errorCode === 'no_credits'" to="/account" class="error-link">Buy a pack</router-link>
          </div>

          <label v-if="showRunConsent" class="run-consent">
            <input v-model="runConsent" type="checkbox" :disabled="submitting" />
            <span>
              I agree to share my pitch under Swarmie's
              <router-link to="/terms" class="rc-link">Terms</router-link>
              and
              <router-link to="/privacy" class="rc-link">Privacy Policy</router-link>.
            </span>
          </label>

          <div class="actions">
            <button class="run-btn" type="submit" :disabled="!canSubmit || submitting">
              {{ submitting ? 'Convening…' : 'Convene the panel' }}
            </button>
            <span class="actions-hint">{{ runHint }}</span>
          </div>

          <p class="ai-note">
            Reviewers are AI agents, not real users.
            <AiDisclosure variant="text" label="How this was generated" />
          </p>
        </aside>
      </form>
    </main>

    <transition name="launch">
      <div v-if="launching" class="launch-overlay" role="status">
        <p class="launch-label">Convening the panel</p>
        <p class="launch-sub">{{ agentCount }} {{ activeSwarm.agentNoun }} · {{ deckFile ? 'reading your deck' : 'reading your pitch' }}</p>
        <div class="launch-bar" aria-hidden="true"><span></span></div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { roastApi } from '../../api/roast'
import AiDisclosure from '../../components/AiDisclosure.vue'
import DeckDropzone from '../../components/swarm/DeckDropzone.vue'
import { trackRoastStart } from '../../lib/analytics'
import { track } from '../../lib/thirdParty'
import { hasAcceptedRunTerms, acceptRunTerms } from '../../lib/consent'
import { SWARMS, isLocked } from '../../lib/swarms'
import { BILLING_ENABLED } from '../../lib/account'

const router = useRouter()
const swarmType = ref('validate')
const pitchText = ref(takeDraft())

// A draft typed into the Home hero arrives via sessionStorage, once.
function takeDraft() {
  try {
    const d = sessionStorage.getItem('swarmie:draft') || ''
    sessionStorage.removeItem('swarmie:draft')
    return d
  } catch { return '' }
}
// Billing on: start on the free panel size so a first review never needs an account.
const agentCount = ref(BILLING_ENABLED ? 20 : 100)
const submitting = ref(false)
const launching = ref(false)
const error = ref('')
const errorCode = ref('')

// Deck file lives here — read by canSubmit / runHint / onSubmit. The dropzone
// widget owns its own drag + validation state (see DeckDropzone.vue).
const deckFile = ref(null)

const activeSwarm = computed(() => SWARMS.find(s => s.key === swarmType.value) || SWARMS[0])

function selectSwarm(s) {
  if (!s.enabled || submitting.value) return
  swarmType.value = s.key
}

// First-run consent (clickwrap to the docs). Surfaces only once the user has
// actually provided content, and never again after they accept once.
const _tosAccepted = hasAcceptedRunTerms()
const runConsent = ref(_tosAccepted)
const hasContent = computed(() => pitchText.value.trim().length > 0 || !!deckFile.value)
const showRunConsent = computed(() => !_tosAccepted && hasContent.value)

const locked = computed(() => isLocked(activeSwarm.value))

const canSubmit = computed(() => {
  if (locked.value) return false
  if (!runConsent.value) return false
  if (swarmType.value === 'investor' && deckFile.value) return true
  return pitchText.value.trim().length >= 40
})

function fillTemplate() {
  pitchText.value = activeSwarm.value.template
}

function hasSection(check) {
  return check.pattern?.test(pitchText.value.toLowerCase()) || false
}

// With billing on, larger panels and pack-only types cost one credit.
const FREE_MAX_AGENTS = 20
const usesCredit = computed(() => BILLING_ENABLED && (agentCount.value > FREE_MAX_AGENTS || activeSwarm.value.tier === 'pack'))
const sizeNote = computed(() => {
  if (usesCredit.value) return 'uses 1 credit'
  return 'free'
})

const runHint = computed(() => {
  if (submitting.value) return 'sending…'
  if (locked.value) return 'switch to Validate for a free review'
  if (!runConsent.value) return 'agree to the terms first'
  if (!canSubmit.value) return deckFile.value ? 'PDF ready' : 'fill the pitch first'
  if (deckFile.value) return `${agentCount.value} ${activeSwarm.value.agentNoun} · deck mode · ~90s`
  return `${agentCount.value} ${activeSwarm.value.agentNoun} · ~60s`
})

async function onSubmit() {
  if (!canSubmit.value || submitting.value) return
  acceptRunTerms()
  error.value = ''
  errorCode.value = ''
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
    track('roast_start', { swarm_type: swarmType.value, source: isDeck ? 'deck' : 'text', n_agents: agentCount.value })
    await new Promise(r => setTimeout(r, 800))
    router.push({ name: 'Watching', params: { jobId } })
  } catch (e) {
    error.value = e?.response?.data?.error || e?.message || 'Could not start the review. Try again in a moment.'
    errorCode.value = e?.response?.data?.code || ''
    launching.value = false
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.page { min-height: 100vh; color: var(--ink); background: var(--paper-2); display: flex; flex-direction: column; }

.rail { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-3) var(--space-6); background: var(--paper); border-bottom: 1px solid var(--rule); }
.brand-mark { font-size: var(--text-md); font-weight: 700; letter-spacing: -0.01em; }
.rail-context { font-size: var(--text-sm); color: var(--ink-3); }
.rail-far { margin-left: auto; font-size: var(--text-sm); color: var(--ink-2); text-decoration: underline; text-underline-offset: 3px; }

.desk { flex: 1; padding: var(--space-7) var(--space-6) var(--space-9); }
.sheet {
  max-width: 1120px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  background: var(--paper);
  border: 1px solid var(--rule);
  box-shadow: 0 18px 48px -32px oklch(20% 0.02 250 / 0.35);
}

.sub-main { padding: var(--space-7) var(--space-7) var(--space-6); border-right: 1px solid var(--rule); min-width: 0; }
.sub-title {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 600;
  font-size: clamp(32px, 4vw, 48px);
  line-height: 1.08;
  letter-spacing: -0.015em;
  text-wrap: balance;
}
.sub-lede { margin: var(--space-3) 0 var(--space-6); max-width: 62ch; color: var(--ink-2); line-height: 1.55; }

.field-head { display: flex; justify-content: space-between; align-items: baseline; gap: var(--space-3); margin-bottom: var(--space-2); }
.field-head-right { display: flex; align-items: baseline; gap: var(--space-4); }
.field-label { font-size: var(--text-sm); font-weight: 700; color: var(--ink); padding: 0; }
.field-meta { font-size: var(--text-sm); color: var(--ink-3); font-variant-numeric: tabular-nums; }
.template-btn {
  font: inherit; font-size: var(--text-sm); color: var(--ink-2);
  background: none; border: 0; padding: 0; cursor: pointer;
  text-decoration: underline; text-underline-offset: 3px;
}
.template-btn:hover { color: var(--ink); }

.textarea {
  display: block;
  width: 100%;
  min-height: 340px;
  resize: vertical;
  padding: var(--space-4);
  font: inherit;
  font-size: var(--text-base);
  line-height: 1.6;
  color: var(--ink);
  background: var(--paper);
  border: 1px solid var(--rule-2);
  border-radius: var(--radius-sm);
  transition: border-color var(--dur-fast) var(--ease-out), box-shadow var(--dur-fast) var(--ease-out);
}
.textarea:hover:not(:disabled) { border-color: var(--ink-4); }
.textarea:focus { outline: none; border-color: var(--ink); box-shadow: 0 0 0 3px oklch(50% 0.11 250 / 0.15); }
.textarea:disabled { background: var(--paper-2); color: var(--ink-3); }

.pitch-checklist { list-style: none; margin: var(--space-3) 0 0; padding: 0; display: flex; flex-wrap: wrap; gap: var(--space-2) var(--space-5); }
.check-item { display: inline-flex; align-items: center; gap: var(--space-2); font-size: var(--text-sm); color: var(--ink-3); }
.check-item::before {
  content: '';
  flex-shrink: 0;
  width: 12px; height: 12px;
  border: 1.5px solid var(--rule-2);
  border-radius: 2px;
  transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
}
.check-item.done { color: var(--ink); }
.check-item.done::before {
  background: var(--live) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3E%3Cpath d='M2.5 6.2l2.2 2.2 4.8-4.8' fill='none' stroke='white' stroke-width='1.6'/%3E%3C/svg%3E") center / 10px no-repeat;
  border-color: var(--live);
}

.sub-side { padding: var(--space-7) var(--space-6) var(--space-6); display: flex; flex-direction: column; gap: var(--space-6); background: var(--paper-2); }
.side-block { margin: 0; padding: 0; border: 0; min-width: 0; }
.side-block legend { margin-bottom: var(--space-2); }

.swarm-picker { display: grid; grid-template-columns: repeat(3, 1fr); border: 1px solid var(--rule-2); border-radius: var(--radius-sm); padding: 2px; gap: 2px; background: var(--paper); }
.swarm-tab {
  font: inherit; font-size: var(--text-sm); font-weight: 600;
  padding: 7px 4px; border: 0; border-radius: 3px;
  background: transparent; color: var(--ink-2); cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.swarm-tab:hover:not(:disabled):not(.active) { background: var(--paper-3); color: var(--ink); }
.swarm-tab.active { background: var(--ink); color: var(--paper); }
.swarm-tab:disabled:not(.active) { color: var(--ink-4); cursor: not-allowed; }
.swarm-tab-soon { font-weight: 400; }
.swarm-tab-pack { margin-left: 6px; font-size: var(--text-xs); font-weight: 700; letter-spacing: 0.04em; color: var(--ink-3); }
.swarm-tab.active .swarm-tab-pack { color: oklch(100% 0 0 / 0.7); }
.pack-note { display: grid; gap: var(--space-2); padding: var(--space-4); background: var(--paper); border: 1px solid var(--rule-2); border-radius: var(--radius-sm); }
.pack-title { margin: 0; font-weight: 700; }
.pack-copy { margin: 0; font-size: var(--text-sm); line-height: 1.55; color: var(--ink-2); }
.pack-link { justify-self: start; font-size: var(--text-sm); font-weight: 600; text-decoration: underline; text-underline-offset: 3px; }

.size-slider { width: 100%; accent-color: var(--ink); margin: var(--space-2) 0; }
.size-presets { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-2); }
.size-presets button {
  font: inherit; font-size: var(--text-sm); font-variant-numeric: tabular-nums;
  padding: 6px 0; border: 1px solid var(--rule-2); border-radius: var(--radius-sm);
  background: var(--paper); color: var(--ink-2); cursor: pointer;
}
.size-presets button:hover { border-color: var(--ink-4); color: var(--ink); }
.size-presets button.active { border-color: var(--ink); color: var(--ink); font-weight: 700; }

.error { font-size: var(--text-sm); color: var(--warn); background: var(--warn-soft); padding: var(--space-3); border-radius: var(--radius-sm); }
.error-link { margin-left: var(--space-2); font-weight: 700; color: var(--ink); text-decoration: underline; text-underline-offset: 3px; }

.run-consent { display: grid; grid-template-columns: auto 1fr; gap: var(--space-2); font-size: var(--text-sm); line-height: 1.5; color: var(--ink-2); }
.run-consent input { accent-color: var(--ink); margin-top: 3px; width: 16px; height: 16px; }
.rc-link { text-decoration: underline; text-underline-offset: 3px; color: var(--ink); }

.actions { display: grid; gap: var(--space-2); }
.run-btn {
  font: inherit; font-size: var(--text-md); font-weight: 700;
  padding: 14px var(--space-4);
  border: 0; border-radius: var(--radius-sm);
  background: var(--ink); color: var(--paper);
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out);
}
.run-btn:hover:not(:disabled) { background: var(--ink-2); }
.run-btn:active:not(:disabled) { transform: translateY(1px); }
.run-btn:disabled { background: var(--paper-4); color: var(--ink-3); cursor: not-allowed; }
.actions-hint { font-size: var(--text-sm); color: var(--ink-3); }
.actions-hint::first-letter { text-transform: uppercase; }
.ai-note { margin: auto 0 0; font-size: var(--text-sm); color: var(--ink-3); line-height: 1.5; }

.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

/* Launch overlay: the panel convening */
.launch-overlay {
  position: fixed; inset: 0; z-index: 50;
  display: grid; place-content: center; justify-items: center; gap: var(--space-2);
  background: oklch(100% 0 0 / 0.92);
  backdrop-filter: blur(6px);
}
.launch-label { margin: 0; font-family: var(--font-display); font-weight: 600; font-size: var(--text-3xl); }
.launch-sub { margin: 0; color: var(--ink-3); }
.launch-bar { margin-top: var(--space-4); width: 220px; height: 2px; background: var(--rule); overflow: hidden; }
.launch-bar span { display: block; height: 100%; width: 40%; background: var(--ink); animation: convene 1.4s var(--ease-in-out) infinite; }
@keyframes convene { from { transform: translateX(-100%); } to { transform: translateX(250%); } }
.launch-enter-active { transition: opacity 260ms var(--ease-out); }
.launch-leave-active { transition: opacity 180ms var(--ease-out); }
.launch-enter-from, .launch-leave-to { opacity: 0; }

@media (max-width: 1024px) {
  .sheet { grid-template-columns: minmax(0, 1fr); }
  .sub-main { border-right: 0; border-bottom: 1px solid var(--rule); }
  .sub-side .ai-note { margin-top: 0; }
}
@media (max-width: 767px) {
  .rail { padding: var(--space-3) var(--space-4); }
  .desk { padding: 0; }
  .sheet { border: 0; box-shadow: none; }
  .sub-main, .sub-side { padding: var(--space-6) var(--space-4); }
  .textarea { min-height: 260px; }
}
</style>
