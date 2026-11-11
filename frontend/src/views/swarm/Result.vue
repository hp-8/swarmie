<template>
  <div class="page page-fixed">
    <header class="rail">
      <router-link to="/" class="brand-mark">
        <span class="dot"></span>
        <span class="brand-text">Swarmie</span>
      </router-link>
      <span class="rail-context">Decision memo · {{ jobShort }}</span>
      <div class="rail-right">
        <div class="rail-tabs">
          <button class="rail-tab" :class="{ active: tab === 'report' }" @click="tab = 'report'">Memo</button>
          <button class="rail-tab" :class="{ active: tab === 'brain' }" @click="tab = 'brain'">Panel map</button>
        </div>
        <button class="rail-action" @click="copyShareUrl">
          {{ copied ? 'Link copied' : 'Copy link' }}
        </button>
        <button class="rail-action" @click="shareCard" :disabled="sharingCard || !report">
          <span v-if="sharingCard">rendering…</span>
          <span v-else>Share card</span>
        </button>
        <button class="rail-action rail-pdf" @click="downloadPdf" :disabled="downloading || !report">
          <span v-if="downloading">building…</span>
          <span v-else>Download PDF</span>
        </button>
        <router-link to="/new" class="rail-action accent">New memo</router-link>
      </div>
    </header>

    <main v-if="loading" class="state-msg">Loading report…</main>

    <main v-else-if="error" class="state-msg">
      <h2 class="state-title h-display">Report unavailable.</h2>
      <p>{{ error }}</p>
      <router-link to="/new" class="h-btn is-accent">Start a new roast →</router-link>
    </main>

    <main v-else-if="report && tab === 'brain'" class="brain-main">
      <BrainGraph
        :archetypes="archetypes"
        :agents="agentMap"
        @select-agent="onSelectAgent"
      />
      <div class="brain-stats">
        <span><b>{{ agentMap.size }}</b> {{ copy.agents }}</span>
        <span><b>{{ archetypes.length }}</b> archetypes</span>
        <span><b>{{ reactions.length }}</b> reactions</span>
      </div>
      <transition name="drawer">
        <aside v-if="selected" class="neuron-drawer" @click.self="selectedId = null">
          <div class="nd-card">
            <button class="nd-close" @click="selectedId = null">×</button>
            <div class="nd-head">
              <span class="h-eyebrow">inside the neuron</span>
              <h2 class="nd-name">@{{ selected.name }}</h2>
              <div class="nd-meta">
                <span class="nd-chip">{{ selected.segment }}</span>
                <span class="nd-chip">tone · {{ selected.tone }}</span>
                <span class="nd-chip">{{ selected.action }}</span>
              </div>
            </div>
            <div class="nd-block">
              <span class="h-eyebrow">persona</span>
              <p class="nd-persona">{{ selectedArchetype?.persona || '—' }}</p>
              <div v-if="selectedArchetype?.objection_bias?.length" class="nd-bias">
                <span class="h-eyebrow tiny">biases</span>
                <div class="nd-bias-row">
                  <span v-for="b in selectedArchetype.objection_bias" :key="b" class="nd-bias-chip">{{ b }}</span>
                </div>
              </div>
            </div>
            <div class="nd-block">
              <span class="h-eyebrow">reaction</span>
              <p v-if="selected.text" class="nd-text">"{{ selected.text }}"</p>
              <p v-else-if="selected.ignore_reason" class="nd-text">scrolled past — "{{ selected.ignore_reason }}"</p>
              <p v-else class="nd-text muted">silent · {{ selected.action }}</p>
              <div class="nd-sent">
                <span class="h-eyebrow tiny">sentiment {{ (selected.sentiment ?? 0).toFixed(2) }}</span>
                <div class="sent-bar2">
                  <div class="sent-fill2" :class="{ pos: (selected.sentiment ?? 0) >= 0, neg: (selected.sentiment ?? 0) < 0 }"
                    :style="{ width: Math.abs(selected.sentiment ?? 0) * 50 + '%', marginLeft: (selected.sentiment ?? 0) < 0 ? (50 - Math.abs(selected.sentiment) * 50) + '%' : '50%' }"></div>
                </div>
              </div>
              <div v-if="selected.objections?.length" class="nd-objs">
                <span class="h-eyebrow tiny">objections fired</span>
                <div class="nd-bias-row">
                  <span v-for="o in selected.objections" :key="o" class="nd-bias-chip warn">{{ o }}</span>
                </div>
              </div>
            </div>
            <AgentChatPanel
              :job-id="jobId"
              :agent-id="selectedId"
              :agent-name="selected.name"
            />
          </div>
        </aside>
      </transition>
    </main>

    <main v-else-if="report" class="memo-main scroll-zone">
      <DecisionMemo
        :report="report"
        :parsed-pitch="parsedPitch"
        :copy="copy"
        :job-id="jobId"
        :reaction-count="reactions.length"
      >
        <template #extra>
          <DeckDiagnosis v-if="deckDiagnosis" :d="deckDiagnosis" />
          <LaunchBrief v-else-if="launchBrief" :b="launchBrief" />
        </template>
      </DecisionMemo>
    </main>

    <footer v-if="report" class="foot-strip">
      <span>Alpha · synthetic agents, <em>not real users</em>. Directional only.</span>
      <span class="foot-sep">·</span>
      <AiDisclosure variant="text" label="how this was generated" />
      <span class="foot-sep">·</span>
      <router-link to="/terms" class="foot-cta">Terms</router-link>
      <span class="foot-sep">·</span>
      <router-link to="/privacy" class="foot-cta">Privacy</router-link>
      <span class="foot-sep">·</span>
      <a href="#" class="foot-cta" @click.prevent="openConsentSettings">Cookie settings</a>
      <span class="foot-sep">·</span>
      <router-link to="/new" class="foot-cta">New memo</router-link>
    </footer>

    <FeedbackWidget v-if="report && tab === 'report'" :job-id="jobId" />
  </div>
</template>

<script setup>
import { ref, shallowRef, computed, onMounted, watch } from 'vue'
import BrainGraph from './BrainGraph.vue'
import AgentChatPanel from './AgentChatPanel.vue'
import AiDisclosure from '../../components/AiDisclosure.vue'
import DeckDiagnosis from '../../components/swarm/DeckDiagnosis.vue'
import LaunchBrief from '../../components/swarm/LaunchBrief.vue'
import DecisionMemo from '../../components/swarm/DecisionMemo.vue'
import FeedbackWidget from '../../components/feedback/FeedbackWidget.vue'
import { useRoute } from 'vue-router'
import { roastApi } from '../../api/roast'
import { verdictMeta } from '../../lib/verdict'
import { buildShareCardBlob, downloadBlob } from '../../lib/shareCard'
import { generateRoastPDF } from '../../lib/pdf/template'
import { trackParsedPitch, trackReport, trackReactions, trackPdfDownload } from '../../lib/analytics'
import { track } from '../../lib/thirdParty'
import { openConsentSettings } from '../../lib/consent'

const route = useRoute()
const jobId = route.params.jobId

const loading = ref(true)
const error = ref('')
const report = ref(null)
const parsedPitch = ref(null)
const copied = ref(false)
const archetypes = ref([])
const reactions = ref([])
const agentMap = shallowRef(new Map())
const tab = ref('report')
const selectedId = ref(null)

const selected = computed(() => selectedId.value ? agentMap.value.get(selectedId.value) : null)
const selectedArchetype = computed(() => {
  if (!selected.value) return null
  return archetypes.value.find(a => a.id === selected.value.archetype_id) || null
})
function onSelectAgent(id) { selectedId.value = id }

// Animated score count-up
const scoreDisplayed = ref(0)

const jobShort = computed(() => (jobId || '').replace('roast_', '').slice(0, 8))

async function load() {
  try {
    const res = await roastApi.get(jobId)
    const j = res.data || res
    if (j.status === 'failed') {
      error.value = j.error || 'Roast failed'
    } else if (j.status !== 'completed') {
      error.value = `Job not finished (status: ${j.status})`
    } else {
      report.value = j.report
      parsedPitch.value = j.parsed_pitch
      swarmType.value = j.swarm_type || 'validate'
      archetypes.value = Array.isArray(j.archetypes) ? j.archetypes : []
      reactions.value = Array.isArray(j.reactions) ? j.reactions : []
      trackParsedPitch(jobId, j.parsed_pitch).catch(() => {})
      trackReport(jobId, j.report).catch(() => {})
      trackReactions(jobId, j.reactions).catch(() => {})
      const m = new Map()
      for (const r of reactions.value) {
        m.set(r.agent_id, {
          archetype_id: r.archetype_id,
          segment: r.segment,
          name: r.name,
          tone: r.tone,
          action: r.action,
          text: r.text,
          objections: r.objections,
          sentiment: r.sentiment,
          ignore_reason: r.ignore_reason,
          state: 'reacted',
        })
      }
      agentMap.value = m
    }
  } catch (e) {
    error.value = e?.message || 'Failed to load report'
  } finally {
    loading.value = false
  }
}

// Per-swarm display vocabulary. Data shape is identical across swarms — only
// the founder-facing labels change.
const COPY = {
  validate: {
    objections: 'top objections',
    voices: 'loudest voices',
    segments: 'segments',
    agents: 'agents',
    silence: (pct) => `why ${pct}% scrolled past`,
    askTag: 'test it',
    killTag: 'drop it if',
  },
  investor: {
    objections: 'questions & objections',
    voices: 'in the room',
    segments: 'investor types',
    agents: 'investors',
    silence: (pct) => `why ${pct}% passed`,
    askTag: 'get proof',
    killTag: 'stalls if',
  },
  launch: {
    objections: 'objections & questions',
    voices: 'in the thread',
    segments: 'communities',
    agents: 'commenters',
    silence: (pct) => `why ${pct}% scrolled past`,
    askTag: 'test this',
    killTag: 'risk if',
  },
}
const swarmType = ref('validate')
const copy = computed(() => COPY[swarmType.value] || COPY.validate)

// Deck diagnosis computed
const deckDiagnosis = computed(() => report.value?.deck_diagnosis ?? null)

// Launch brief computed
const launchBrief = computed(() => report.value?.launch_brief ?? null)

async function copyShareUrl() {
  await navigator.clipboard.writeText(window.location.href)
  track('share', { method: 'copy_link', content_type: 'roast' })
  copied.value = true
  setTimeout(() => (copied.value = false), 1500)
}

// --- Share card (1200×630 PNG, drawn client-side) -------------------------
const sharingCard = ref(false)

function shareCardData() {
  const r = report.value
  const top = r.top_objections?.[0]
  const risk = r.hidden_risks?.[0]
  return {
    riskTitle: risk?.risk || '',
    riskWhy: risk?.why_non_obvious || '',
    verdict: r.verdict,
    pmf_score: r.pmf_score,
    confidence: r.confidence,
    agentCount: reactions.value.length,
    objectionCategory: top?.category || '',
    objectionText: top?.example_quote || top?.real_test || '',
    url: 'swarmie.harshpatadia.com',
  }
}

async function shareCard() {
  if (sharingCard.value || !report.value) return
  sharingCard.value = true
  try {
    const { blob } = await buildShareCardBlob(shareCardData())
    track('share', { method: 'card', content_type: 'roast' })
    const filename = `swarmie-roast-${jobShort.value || 'card'}.png`
    const file = new File([blob], filename, { type: 'image/png' })
    // Web Share API with files (mobile) is the primary path; download is the fallback.
    if (navigator.canShare?.({ files: [file] })) {
      try {
        await navigator.share({
          files: [file],
          title: 'Swarmie roast',
          text: `${verdictMeta(report.value.verdict).label} — what ${reactions.value.length || 'a swarm of'} synthetic users said about my pitch. swarmie.harshpatadia.com`,
        })
        return
      } catch (e) {
        if (e?.name === 'AbortError') return // user closed the share sheet
        // any other share failure → fall through to plain download
      }
    }
    downloadBlob(blob, filename)
  } catch (e) {
    console.error('share card failed', e)
  } finally {
    sharingCard.value = false
  }
}

// --- PDF download (free) -------------------------------------------------
const downloading = ref(false)

async function downloadPdf() {
  if (downloading.value || !report.value) return
  downloading.value = true
  try {
    await generateRoastPDF({
      report: report.value,
      parsedPitch: parsedPitch.value,
      jobId,
      swarmType: swarmType.value,
      reactionCount: reactions.value.length,
    })
    trackPdfDownload(jobId).catch(() => {})
    track('file_download', { source: 'roast_pdf' })
  } catch (e) {
    console.error('PDF gen failed', e)
  } finally {
    setTimeout(() => { downloading.value = false }, 400)
  }
}

function animateScore(target) {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    scoreDisplayed.value = target
    return
  }
  const start = performance.now()
  const duration = 900
  const easeOut = t => 1 - Math.pow(1 - t, 3)
  function tick(now) {
    const p = Math.min(1, (now - start) / duration)
    scoreDisplayed.value = (easeOut(p) * target)
    if (p < 1) requestAnimationFrame(tick)
    else scoreDisplayed.value = target
  }
  requestAnimationFrame(tick)
}

watch(report, (r) => {
  if (r && typeof r.pmf_score === 'number') animateScore(r.pmf_score)
})

onMounted(() => {
  load()
})
</script>

<style scoped>
/* Hallmark · page: Result · macrostructure: Dashboard (fixed-viewport)
 * 3 rows × variable cols. Each scrollable cell is its own scroll-zone.
 * theme: Midnight+coral (atmospheric)
 */

.page { color: var(--ink); background: var(--paper); }

/* Rail */
.rail {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-6);
  border-bottom: 1px solid var(--rule);
  flex-shrink: 0;
}
.brand-mark { display: inline-flex; align-items: center; gap: var(--space-2); font-size: var(--text-md); font-weight: 700; letter-spacing: -0.01em; }
.brand-mark .dot { display: none; }
.brand-text { text-transform: capitalize; }
.rail-context { font-size: var(--text-sm); color: var(--ink-3); }
.rail-right { margin-left: auto; display: flex; gap: var(--space-2); }
.rail-action {
  font: inherit; font-size: var(--text-sm); font-weight: 500;
  padding: 7px 12px; background: transparent;
  border: 1px solid transparent; color: var(--ink-2);
  border-radius: var(--radius-sm); cursor: pointer;
  transition: all var(--dur-fast) var(--ease-out);
}
.rail-action:hover { color: var(--ink); background: var(--paper-3); }
.rail-action.accent { background: var(--ink); border-color: var(--ink); color: var(--paper); font-weight: 600; }
.rail-action.accent:hover { background: var(--ink-2); }
.rail-action:active { transform: scale(0.96); }
.rail-action:disabled { opacity: 0.5; cursor: not-allowed; }
.rail-action:disabled:hover { color: var(--ink-2); border-color: var(--rule-2); background: transparent; }

/* state msgs */
.state-msg {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  max-width: 560px;
  margin: 0 auto;
  padding: 0 var(--space-5);
  text-align: center;
  color: var(--ink-2);
}
.state-title { font-size: var(--text-3xl); color: var(--ink); margin: 0; }

@keyframes cell-in {
  to { opacity: 1; transform: translateY(0); }
}

.detail-tab.active {
  color: var(--ink);
  background: var(--paper-3);
  border-color: var(--rule-2);
  box-shadow: inset 0 1px 0 color-mix(in oklch, white 7%, transparent),
              0 1px 3px color-mix(in oklch, black 35%, transparent);
}

.detail-tab.active .detail-tab-count {
  color: var(--accent-bright);
  background: var(--accent-soft);
}

/* FOOT */
.foot-strip {
  flex-shrink: 0;
  padding: var(--space-2) var(--space-6);
  border-top: 1px solid var(--rule);
  font-size: var(--text-sm);
  color: var(--ink-3);
  text-align: center;
}
.foot-strip em { color: var(--ink); font-style: normal; font-weight: 600; }
.foot-sep { margin: 0 var(--space-2); color: var(--rule-2); }
.foot-cta { color: var(--ink-2); text-decoration: underline; text-underline-offset: 3px; }
.foot-cta:hover { color: var(--ink); }

.muted { color: var(--ink-3); font-size: var(--text-sm); margin: 0; }

/* rail tabs */
.rail-tabs {
  display: inline-flex;
  border: 1px solid var(--rule);
  border-radius: var(--radius-sm);
  padding: 2px;
  gap: 2px;
  margin-right: var(--space-3);
}
.rail-tab {
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 3px;
  background: transparent;
  color: var(--ink-3);
  border: 0;
  cursor: pointer;
  transition: background var(--dur-base) var(--ease-out), color var(--dur-base) var(--ease-out);
}
.rail-tab.active { background: var(--ink); color: var(--paper); }

/* brain main */
.brain-main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-6);
  position: relative;
}
.brain-main > :first-child { flex: 1; min-height: 0; }
.brain-stats {
  display: flex;
  gap: var(--space-5);
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-3);
  letter-spacing: 0.08em;
  padding: 0 var(--space-2);
}
.brain-stats b { color: var(--ink); font-weight: 700; margin-right: 4px; }

/* neuron drawer (Result tab) */
.neuron-drawer {
  position: fixed;
  inset: 0;
  background: rgba(7, 7, 15, 0.55);
  backdrop-filter: blur(4px);
  z-index: 80;
  display: flex;
  justify-content: flex-end;
}
.nd-card {
  width: min(440px, 92vw);
  height: 100%;
  background: var(--paper);
  border-left: 1px solid var(--rule);
  padding: var(--space-6);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  position: relative;
}
.nd-close {
  position: absolute;
  top: var(--space-3);
  right: var(--space-4);
  background: transparent;
  border: 0;
  font-size: 28px;
  line-height: 1;
  color: var(--ink-3);
  cursor: pointer;
}
.nd-close:hover { color: var(--ink); }
.nd-head { display: flex; flex-direction: column; gap: var(--space-2); }
.nd-name { font-family: var(--font-display); font-style: normal; font-size: var(--text-2xl); margin: 0; }
.nd-meta { display: flex; gap: 6px; flex-wrap: wrap; }
.nd-chip {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: 999px;
  border: 1px solid var(--rule);
  color: var(--ink-3);
}
.nd-block { display: flex; flex-direction: column; gap: var(--space-2); }
.h-eyebrow.tiny { font-size: 9px; }
.nd-persona, .nd-text { font-size: var(--text-sm); color: var(--ink); line-height: 1.5; margin: 0; }
.nd-text.muted { color: var(--ink-3); font-style: italic; }
.nd-bias-row { display: flex; flex-wrap: wrap; gap: 4px; }
.nd-bias-chip {
  font-family: var(--font-mono);
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 4px;
  background: color-mix(in oklch, var(--accent) 12%, transparent);
  color: var(--accent);
}
.nd-bias-chip.warn {
  background: color-mix(in oklch, var(--warn, #ff5470) 14%, transparent);
  color: var(--warn, #ff5470);
}
.nd-sent { display: flex; flex-direction: column; gap: 4px; }
.sent-bar2 { height: 6px; background: rgba(127,127,140,0.12); border-radius: 999px; overflow: hidden; }
.sent-fill2 { height: 100%; border-radius: 999px; }
.sent-fill2.pos { background: #3ddc97; }

.drawer-enter-active, .drawer-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.drawer-enter-active .nd-card, .drawer-leave-active .nd-card { transition: transform var(--dur-base) var(--ease-out); }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from .nd-card, .drawer-leave-to .nd-card { transform: translateX(100%); }

/* responsive for deck diagnosis */
@media (max-width: 1024px) {
  .strip-diag-hero { grid-template-columns: 160px 1fr; }
  .strip-diag-hero .cell-next-move { grid-column: 1 / -1; }
  .strip-diag-main { grid-template-columns: 1fr; }
  .strip-diag-zones { grid-template-columns: 1fr; }
}

@media (max-width: 760px) {
  .page.page-fixed { height: auto; overflow: auto; }
  
  
  
}

/* responsive for main dashboard */
@media (max-width: 1100px) {
  .strip-hero { grid-template-columns: 180px 1fr 196px; }
}

@media (max-width: 760px) {
  .rail { flex-wrap: wrap; row-gap: var(--space-2); padding: var(--space-3) var(--space-4); }
  .rail-context { display: none; }
  .rail-right { margin-left: 0; width: 100%; overflow-x: auto; scrollbar-width: none; }
  .rail-action, .rail-tab { white-space: nowrap; }
  
  
  .page.page-fixed { height: auto; overflow: auto; }
  
  
  
  
}

/* responsive for launch brief */
@media (max-width: 1024px) {
  .strip-launch-hero { grid-template-columns: 160px 1fr; }
  .strip-launch-hero .cell-launch-sentiment { grid-column: 1 / -1; }
  .strip-launch-qcr { grid-template-columns: 1fr 1fr; }
  .strip-launch-tp { grid-template-columns: 1fr; }
}

@media (max-width: 760px) {
  .page.page-fixed { height: auto; overflow: auto; }
  
  
  
}

/* iPad / tablet (portrait + landscape) — relax the fixed-viewport dashboard
 * into a comfortable scrolling 2-column flow. */
@media (min-width: 761px) and (max-width: 1024px) {
  .page.page-fixed { height: auto; overflow: auto; }
  .dash { grid-template-rows: auto auto auto; overflow: visible; max-width: 920px; }
  .cell { overflow: visible; }
  .scroll-zone { overflow: visible; }
  .strip-hero { grid-template-columns: 200px 1fr; }
  .strip-hero .cell-sentiment { grid-column: 1 / -1; }
  .detail-pane { overflow: visible; min-height: 50vh; }
  .pane, .pane-padded { overflow: visible; }
  .pane :deep(.obj-list),
  .pane :deep(.quotes-list) { overflow: visible; }
}
</style>
