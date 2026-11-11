<template>
  <div class="page page-fixed">
    <header class="rail">
      <router-link to="/" class="brand-mark">Swarmie</router-link>
      <span class="rail-context">Review in progress · {{ jobShort }}</span>
      <div class="rail-right">
        <span class="status" :class="statusChipClass">{{ statusLabel }}</span>
        <AiDisclosure aria-label="About this simulation" />
      </div>
    </header>

    <main class="doc">
      <aside class="anchor">
        <h1 class="anchor-title">{{ headline }}</h1>

        <ol class="stations" aria-label="Review progress">
          <li
            v-for="(st, i) in STATIONS"
            :key="st.key"
            class="station"
            :class="stationState(i)"
            :aria-current="stationState(i) === 'is-current' ? 'step' : undefined"
          >
            <span class="st-num">{{ i + 1 }}</span>
            <span class="st-label">{{ st.label }}</span>
            <span v-if="stationState(i) === 'is-current'" class="st-detail">{{ stationDetail(st.key) }}<template v-if="isRunning"> · {{ elapsedLabel }}</template></span>
          </li>
        </ol>

        <div class="progress-track" aria-hidden="true">
          <div class="progress-fill" :style="{ transform: `scaleX(${progressPct / 100})` }"></div>
        </div>

        <dl v-if="parsedPitch" class="pitch-card">
          <div><dt>Pitch</dt><dd>{{ parsedPitch.one_liner }}</dd></div>
          <div><dt>Audience</dt><dd>{{ parsedPitch.target_icp }}</dd></div>
          <div v-if="parsedPitch.icp_segments?.length"><dt>Segments</dt><dd>{{ parsedPitch.icp_segments.join(', ') }}</dd></div>
        </dl>

        <div v-if="error" class="error-box" role="alert">
          <strong>The review stopped.</strong>
          <span>{{ error }}</span>
          <button class="retry-btn" type="button" @click="$router.push('/new')">Start a new submission</button>
        </div>
      </aside>

      <section class="stream">
        <header class="stream-head">
          <h2 class="stream-title">{{ view === 'brain' ? 'Panel map' : 'Reactions as they arrive' }}</h2>
          <div class="view-toggle" role="tablist" aria-label="View">
            <button class="vt-btn" role="tab" :aria-selected="view === 'list'" :class="{ active: view === 'list' }" @click="view = 'list'">Log</button>
            <button class="vt-btn" role="tab" :aria-selected="view === 'brain'" :class="{ active: view === 'brain' }" @click="view = 'brain'">Panel map</button>
          </div>
        </header>

        <div v-show="view === 'brain'" class="brain-host">
          <BrainGraph
            ref="brainRef"
            :archetypes="archetypes"
            :agents="agentMap"
            @select-agent="onSelectAgent"
          />
          <div class="brain-stats">
            <span><b>{{ agentMap.size }}</b> reviewers</span>
            <span><b>{{ thinkingCount }}</b> reading</span>
            <span><b>{{ reactions.length }}</b> reacted</span>
          </div>
        </div>

        <div v-show="view === 'list'" class="list-host">
          <div v-if="visibleReactions.length === 0" class="stream-empty">
            <template v-if="isRunning && archetypes.length">
              <h3 class="wait-title">Who's on the panel</h3>
              <ul class="wait-panel">
                <li v-for="a in archetypes.slice(0, 12)" :key="a.id">
                  <b>{{ a.name }}</b>
                  <span>{{ a.segment }}<template v-if="a.objection_bias?.length"> · watches for {{ a.objection_bias.slice(0, 2).join(', ') }}</template></span>
                </li>
              </ul>
              <p class="wait-note">Their first reactions appear here as they finish reading.</p>
            </template>
            <template v-else-if="isRunning && parsedPitch">
              <h3 class="wait-title">What the panel will read</h3>
              <dl class="wait-pitch">
                <div v-for="f in pitchFields" :key="f.label"><dt>{{ f.label }}</dt><dd>{{ f.value }}</dd></div>
              </dl>
              <p class="wait-note">Next: choosing reviewers who match your audience.</p>
            </template>
            <p v-else class="wait-note">{{ isRunning ? 'Reading your pitch first. Reviewers appear here next.' : 'No reactions recorded.' }}</p>
            <p v-if="isRunning && stageSeconds >= 45" class="wait-slow">
              Still working. Free reviews run on a free model, so a step can take a minute or two.
            </p>
          </div>
          <transition-group name="slide" tag="ol" class="stream-list scroll-zone">
            <li
              v-for="r in visibleReactions"
              :key="r.agent_id"
              class="reaction"
              :class="['tone-' + r.tone, 'action-' + r.action]"
            >
              <button type="button" class="r-open" @click="onSelectAgent(r.agent_id)">
                <span class="r-meta">
                  <span class="r-handle">{{ r.name }}</span>
                  <span class="r-action">{{ actionLabel(r.action) }}</span>
                  <span class="r-seg">{{ r.segment }}</span>
                </span>
                <span v-if="r.text" class="r-text">{{ r.text }}</span>
                <span v-if="r.objections?.length" class="r-objections">Raised: {{ r.objections.join(', ') }}</span>
              </button>
            </li>
          </transition-group>
        </div>
      </section>
    </main>

    <transition name="drawer">
      <aside v-if="selected" class="neuron-drawer" @click.self="selectedId = null">
        <div class="nd-card" role="dialog" :aria-label="`Reviewer ${selected.name}`">
          <button class="nd-close" type="button" aria-label="Close" @click="selectedId = null">Close</button>
          <div class="nd-head">
            <h2 class="nd-name">{{ selected.name }}</h2>
            <p class="nd-meta">{{ [selected.segment, selected.tone, selected.action || 'pending'].filter(Boolean).join(' · ') }}</p>
          </div>

          <div class="nd-block">
            <h3 class="nd-label">Persona</h3>
            <p class="nd-persona">{{ selectedArchetype?.persona || 'Loading…' }}</p>
            <p v-if="selectedArchetype?.objection_bias?.length" class="nd-sub">Leans toward: {{ selectedArchetype.objection_bias.join(', ') }}</p>
          </div>

          <div v-if="selected.state === 'reacted'" class="nd-block">
            <h3 class="nd-label">Reaction</h3>
            <p v-if="selected.text" class="nd-text">"{{ selected.text }}"</p>
            <p v-else class="nd-text muted">No comment · {{ selected.action }}</p>
            <p class="nd-sub">Sentiment {{ (selected.sentiment ?? 0).toFixed(2) }} (from -1 to 1)</p>
            <p v-if="selected.objections?.length" class="nd-sub">Raised: {{ selected.objections.join(', ') }}</p>
          </div>
          <div v-else-if="selected.state === 'thinking'" class="nd-block">
            <h3 class="nd-label">Status</h3>
            <p class="nd-text">Reading the pitch now.</p>
          </div>
          <div v-else class="nd-block">
            <h3 class="nd-label">Status</h3>
            <p class="nd-text muted">Waiting to read the pitch.</p>
          </div>
          <AgentChatPanel
            v-if="status === 'completed' && selected.state === 'reacted'"
            :job-id="jobId"
            :agent-id="selectedId"
            :agent-name="selected.name"
          />
          <p v-else-if="selected.state === 'reacted'" class="nd-sub">You can question this reviewer once the memo is ready.</p>
        </div>
      </aside>
    </transition>
  </div>
</template>

<script setup>
import { watch, ref, shallowRef, triggerRef, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { roastApi } from '../../api/roast'
import BrainGraph from './BrainGraph.vue'
import AgentChatPanel from './AgentChatPanel.vue'
import AiDisclosure from '../../components/AiDisclosure.vue'

const route = useRoute()
const router = useRouter()
const jobId = route.params.jobId

const status = ref('pending')
const progress = ref(0)
const parsedPitch = ref(null)
const reactions = ref([])
const archetypes = ref([])
const agentMap = shallowRef(new Map()) // agent_id -> {archetype_id, segment, name, tone, state, action, sentiment, text, objections}
const view = ref('list')
const selectedId = ref(null)
const brainRef = ref(null)
const error = ref('')
let evtSource = null
let pollTimer = null

const jobShort = computed(() => (jobId || '').replace('roast_', '').slice(0, 8))
const progressPct = computed(() => Math.round(progress.value * 100))

const STATUS_MAP = {
  pending: 'Queued',
  parsing: 'Reading pitch',
  generating_archetypes: 'Assembling panel',
  running_swarm: 'Panel reacting',
  reporting: 'Writing memo',
  completed: 'Memo ready',
  failed: 'Failed',
  cancelled: 'Cancelled',
}
const statusLabel = computed(() => STATUS_MAP[status.value] || status.value)

// Time on the current step, so a slow free-model step reads as progress, not a freeze.
const now = ref(Date.now())
const stageStartedAt = ref(Date.now())
watch(status, () => { stageStartedAt.value = Date.now() })
const clock = setInterval(() => { now.value = Date.now() }, 1000)
const stageSeconds = computed(() => Math.max(0, Math.floor((now.value - stageStartedAt.value) / 1000)))
const elapsedLabel = computed(() => {
  const s = stageSeconds.value
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
})
const pitchFields = computed(() => {
  const p = parsedPitch.value || {}
  return [
    { label: 'Problem', value: p.problem },
    { label: 'Solution', value: p.solution },
    { label: 'Price', value: p.pricing },
    { label: 'Competitors', value: Array.isArray(p.competitors) ? p.competitors.join(', ') : p.competitors },
  ].filter((f) => f.value)
})
const isRunning = computed(() =>
  !['completed', 'failed', 'cancelled'].includes(status.value),
)
const statusChipClass = computed(() => {
  if (status.value === 'completed') return 'is-live'
  if (['failed', 'cancelled'].includes(status.value)) return 'is-warn'
  return 'is-accent'
})

// The run as fixed, numbered stations; the current one carries live detail.
const STATIONS = [
  { key: 'parsing', label: 'Reading your pitch' },
  { key: 'generating_archetypes', label: 'Assembling the panel' },
  { key: 'running_swarm', label: 'Panel reacting' },
  { key: 'reporting', label: 'Writing the memo' },
]
const lastStation = ref(0)
const stationIndex = computed(() => {
  if (status.value === 'completed') return STATIONS.length
  const i = STATIONS.findIndex((st) => st.key === status.value)
  return i === -1 ? lastStation.value : i
})
watch(stationIndex, (i) => { if (i < STATIONS.length) lastStation.value = i })
function stationState(i) {
  const failed = ['failed', 'cancelled'].includes(status.value)
  if (i < stationIndex.value) return 'is-done'
  if (i === stationIndex.value) return failed ? 'is-failed' : 'is-current'
  return 'is-pending'
}
function stationDetail(key) {
  if (key === 'running_swarm') return `${reactions.value.length} reactions in`
  if (key === 'generating_archetypes') return archetypes.value.length ? `${archetypes.value.length} reviewer types` : 'Choosing reviewer types'
  if (key === 'reporting') return 'Findings, risks and the next step'
  return 'Finding the problem, audience and price'
}

const headline = computed(() => {
  if (status.value === 'completed') return 'Memo ready.'
  if (['failed', 'cancelled'].includes(status.value)) return 'The review stopped.'
  if (status.value === 'running_swarm') return 'The panel is reacting.'
  if (status.value === 'reporting') return 'Writing the memo.'
  if (status.value === 'generating_archetypes') return 'Assembling the panel.'
  if (status.value === 'parsing') return 'Reading your pitch.'
  return 'Getting ready.'
})

const visibleReactions = computed(() => {
  return [...reactions.value]
    .filter(r => r.text || r.action === 'upvote')
    .slice(-80)
    .reverse()
})

function actionLabel(action) {
  return { post: 'Posted', comment: 'Commented', upvote: 'Upvoted', ignore: 'Scrolled past' }[action] || action
}

const thinkingCount = computed(() => {
  let n = 0
  for (const a of agentMap.value.values()) if (a.state === 'thinking') n++
  return n
})

const selected = computed(() => selectedId.value ? agentMap.value.get(selectedId.value) : null)
const selectedArchetype = computed(() => {
  if (!selected.value) return null
  return archetypes.value.find(a => a.id === selected.value.archetype_id) || null
})

function onSelectAgent(id) {
  selectedId.value = id
}

function upsertAgent(id, patch) {
  const m = agentMap.value
  const ex = m.get(id) || {}
  m.set(id, { ...ex, ...patch })
  triggerRef(agentMap)
  brainRef.value?.patchAgents?.()
}

function handleEvent(eventName, data) {
  if (eventName === 'status') {
    status.value = data.status || status.value
    if (typeof data.progress === 'number') progress.value = data.progress
    if (data.status === 'failed') error.value = data.error || 'Pipeline failed'
    if (data.status === 'completed') {
      setTimeout(() => {
        if (!selectedId.value) router.replace({ name: 'Result', params: { jobId } })
      }, 1800)
    }
  } else if (eventName === 'parsed_pitch') {
    parsedPitch.value = data
  } else if (eventName === 'archetypes') {
    archetypes.value = Array.isArray(data) ? data : []
  } else if (eventName === 'thinking') {
    upsertAgent(data.agent_id, {
      archetype_id: data.archetype_id,
      segment: data.segment,
      name: data.name,
      tone: data.tone,
      action: data.action,
      state: 'thinking',
    })
  } else if (eventName === 'reaction') {
    reactions.value.push(data)
    upsertAgent(data.agent_id, {
      archetype_id: data.archetype_id,
      segment: data.segment,
      name: data.name,
      tone: data.tone,
      action: data.action,
      text: data.text,
      objections: data.objections,
      sentiment: data.sentiment,
      state: 'reacted',
    })
  } else if (eventName === 'done') {
    setTimeout(() => router.replace({ name: 'Result', params: { jobId } }), 1800)
  }
}

function startStream() {
  const url = roastApi.streamUrl(jobId)
  evtSource = new EventSource(url)
  for (const name of ['status', 'parsed_pitch', 'archetypes', 'thinking', 'reaction', 'report', 'done']) {
    evtSource.addEventListener(name, (e) => {
      try { handleEvent(name, JSON.parse(e.data)) } catch (err) { console.warn('Bad SSE', name, err) }
    })
  }
  evtSource.onerror = () => {
    if (evtSource.readyState === EventSource.CLOSED) startPolling()
  }
}

function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    try {
      const job = await roastApi.get(jobId)
      const j = job.data || job
      status.value = j.status
      progress.value = j.progress || 0
      if (j.parsed_pitch) parsedPitch.value = j.parsed_pitch
      if (j.reactions) reactions.value = j.reactions
      if (j.error) error.value = j.error
      if (['completed', 'failed', 'cancelled'].includes(j.status)) {
        clearInterval(pollTimer)
        pollTimer = null
        if (j.status === 'completed') router.replace({ name: 'Result', params: { jobId } })
      }
    } catch (err) { console.warn('poll fail', err) }
  }, 2000)
}

function onKey(e) { if (e.key === 'Escape') selectedId.value = null }
onMounted(() => {
  startStream()
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  if (evtSource) evtSource.close()
  if (pollTimer) clearInterval(pollTimer)
  clearInterval(clock)
})
</script>

<style scoped>
.page { color: var(--ink); background: var(--paper); display: flex; flex-direction: column; }

.rail { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-3) var(--space-6); border-bottom: 1px solid var(--rule); flex-shrink: 0; }
.brand-mark { font-size: var(--text-md); font-weight: 700; letter-spacing: -0.01em; }
.rail-context { font-size: var(--text-sm); color: var(--ink-3); }
.rail-right { margin-left: auto; display: flex; align-items: center; gap: var(--space-3); }
.status { font-size: var(--text-sm); font-weight: 600; color: var(--ink-2); }
.status.is-live { color: var(--live); }
.status.is-warn { color: var(--warn); }

.doc { flex: 1; min-height: 0; display: grid; grid-template-columns: 380px minmax(0, 1fr); }

/* Left: the deliberation record */
.anchor { padding: var(--space-7) var(--space-6); border-right: 1px solid var(--rule); background: var(--paper-2); overflow-y: auto; display: flex; flex-direction: column; gap: var(--space-6); }
.anchor-title { margin: 0; font-family: var(--font-display); font-weight: 600; font-size: clamp(30px, 3vw, 40px); line-height: 1.1; letter-spacing: -0.015em; text-wrap: balance; }

.stations { list-style: none; margin: 0; padding: 0; display: grid; }
.station {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  column-gap: var(--space-3);
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--rule);
  color: var(--ink-4);
  transition: color var(--dur-base) var(--ease-out);
}
.st-num { font-weight: 700; font-variant-numeric: tabular-nums; }
.st-label { font-weight: 600; }
.st-detail { grid-column: 2; font-size: var(--text-sm); color: var(--ink-3); font-variant-numeric: tabular-nums; }
.station.is-done { color: var(--ink-3); }
.station.is-done .st-label { text-decoration: line-through; text-decoration-color: var(--rule-2); }
.station.is-current { color: var(--ink); }
.station.is-current .st-num { color: var(--info); }
.station.is-failed { color: var(--warn); }

.progress-track { height: 2px; background: var(--rule); overflow: hidden; }
.progress-fill { height: 100%; width: 100%; background: var(--ink); transform-origin: left; transition: transform var(--dur-slow) var(--ease-out); }

.pitch-card { margin: 0; display: grid; gap: var(--space-3); }
.pitch-card > div { display: grid; gap: 2px; }
.pitch-card dt { font-size: var(--text-sm); color: var(--ink-3); }
.pitch-card dd { margin: 0; line-height: 1.5; overflow-wrap: anywhere; }

.error-box { display: grid; gap: var(--space-2); padding: var(--space-4); background: var(--warn-soft); color: var(--ink); border-radius: var(--radius-sm); }
.error-box strong { color: var(--warn); }
.retry-btn { justify-self: start; font: inherit; font-weight: 600; padding: 8px 14px; border: 0; border-radius: var(--radius-sm); background: var(--ink); color: var(--paper); cursor: pointer; }
.retry-btn:hover { background: var(--ink-2); }

/* Right: reactions */
.stream { min-height: 0; display: flex; flex-direction: column; }
.stream-head { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-5) var(--space-6) var(--space-3); border-bottom: 1px solid var(--rule); }
.stream-title { margin: 0; font-size: var(--text-lg); font-weight: 700; letter-spacing: -0.01em; }
.view-toggle { display: inline-flex; border: 1px solid var(--rule-2); border-radius: var(--radius-sm); padding: 2px; gap: 2px; }
.vt-btn { font: inherit; font-size: var(--text-sm); font-weight: 600; padding: 4px 12px; border: 0; border-radius: 3px; background: transparent; color: var(--ink-2); cursor: pointer; }
.vt-btn:hover:not(.active) { background: var(--paper-3); }
.vt-btn.active { background: var(--ink); color: var(--paper); }

.list-host, .brain-host { flex: 1; min-height: 0; position: relative; }
.stream-empty { padding: var(--space-6); max-width: 68ch; height: 100%; overflow-y: auto; }
.wait-title { margin: 0 0 var(--space-4); font-size: var(--text-base); font-weight: 700; }
.wait-panel { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: var(--space-4) var(--space-5); }
.wait-panel li { display: grid; gap: 2px; font-size: var(--text-sm); animation: wait-in 360ms var(--ease-out) both; }
.wait-panel b { color: var(--ink); }
.wait-panel span { color: var(--ink-3); line-height: 1.45; }
.wait-pitch { margin: 0; display: grid; gap: var(--space-3); }
.wait-pitch > div { display: grid; grid-template-columns: 110px minmax(0, 1fr); gap: var(--space-4); }
.wait-pitch dt { font-size: var(--text-sm); color: var(--ink-3); }
.wait-pitch dd { margin: 0; line-height: 1.5; color: var(--ink-2); }
.wait-note { margin: var(--space-5) 0 0; font-size: var(--text-sm); color: var(--ink-3); }
.wait-slow { margin: var(--space-3) 0 0; font-size: var(--text-sm); color: var(--ink-2); }
@keyframes wait-in { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
@media (prefers-reduced-motion: reduce) { .wait-panel li { animation: none; } }
.stream-list { list-style: none; margin: 0; padding: 0 var(--space-6); height: 100%; overflow-y: auto; }
.reaction { border-bottom: 1px solid var(--rule); }
.r-open { display: grid; gap: var(--space-1); width: 100%; text-align: left; font: inherit; color: inherit; background: none; border: 0; padding: var(--space-4) 0; cursor: pointer; }
.r-open:hover .r-handle { text-decoration: underline; text-underline-offset: 3px; }
.r-meta { display: flex; flex-wrap: wrap; gap: 0 var(--space-3); font-size: var(--text-sm); color: var(--ink-3); }
.r-handle { font-weight: 600; color: var(--ink); }
.r-text { font-family: var(--font-display); font-size: var(--text-md); line-height: 1.5; color: var(--ink-2); max-width: 70ch; }
.r-objections { font-size: var(--text-sm); color: var(--warn); }
.tone-enthusiastic .r-action { color: var(--live); }
.tone-skeptical .r-action, .tone-aggressive .r-action { color: var(--warn); }

.slide-enter-active { transition: opacity 320ms var(--ease-out), transform 320ms var(--ease-out); }
.slide-enter-from { opacity: 0; transform: translateY(-6px); }

.brain-stats { position: absolute; right: var(--space-6); bottom: var(--space-4); display: flex; gap: var(--space-5); font-size: var(--text-sm); color: var(--ink-3); background: oklch(100% 0 0 / 0.9); padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm); }
.brain-stats b { color: var(--ink); font-variant-numeric: tabular-nums; }

/* Reviewer drawer */
.neuron-drawer { position: fixed; inset: 0; z-index: 40; background: oklch(20% 0.01 250 / 0.25); display: flex; justify-content: flex-end; }
.nd-card { width: min(440px, 100%); height: 100%; overflow-y: auto; background: var(--paper); border-left: 1px solid var(--rule); box-shadow: -18px 0 48px -32px oklch(20% 0.02 250 / 0.5); padding: var(--space-6); display: grid; align-content: start; gap: var(--space-5); position: relative; }
.nd-close { justify-self: end; font: inherit; font-size: var(--text-sm); color: var(--ink-2); background: none; border: 0; padding: 0; cursor: pointer; text-decoration: underline; text-underline-offset: 3px; }
.nd-name { margin: 0; font-family: var(--font-display); font-weight: 600; font-size: var(--text-2xl); overflow-wrap: anywhere; }
.nd-meta { margin: var(--space-1) 0 0; font-size: var(--text-sm); color: var(--ink-3); }
.nd-block { display: grid; gap: var(--space-2); padding-top: var(--space-4); border-top: 1px solid var(--rule); }
.nd-label { margin: 0; font-size: var(--text-sm); font-weight: 700; }
.nd-persona, .nd-text { margin: 0; line-height: 1.55; color: var(--ink-2); }
.nd-text { font-family: var(--font-display); font-size: var(--text-md); }
.nd-sub { margin: 0; font-size: var(--text-sm); color: var(--ink-3); }
.muted { color: var(--ink-3); }
.drawer-enter-active, .drawer-leave-active { transition: opacity 220ms var(--ease-out); }
.drawer-enter-active .nd-card, .drawer-leave-active .nd-card { transition: transform 260ms var(--ease-out); }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from .nd-card, .drawer-leave-to .nd-card { transform: translateX(24px); }

@media (max-width: 1024px) {
  .doc { grid-template-columns: 300px minmax(0, 1fr); }
}
@media (max-width: 767px) {
  .page.page-fixed { height: auto; min-height: 100vh; overflow: auto; }
  .rail { padding: var(--space-3) var(--space-4); flex-wrap: wrap; }
  .rail-context { display: none; }
  .doc { grid-template-columns: minmax(0, 1fr); }
  .anchor { border-right: 0; border-bottom: 1px solid var(--rule); padding: var(--space-6) var(--space-4); overflow: visible; }
  .stream-head { padding: var(--space-4); }
  .stream-list { padding: 0 var(--space-4); height: auto; overflow: visible; }
  .brain-host { min-height: 420px; }
}
</style>
