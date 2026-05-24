<template>
  <div class="page">
    <header class="rail">
      <router-link to="/" class="brand-mark">
        <span class="dot" :class="{ pulse: isRunning }"></span>
        <span class="brand-text">SWARMIE</span>
      </router-link>
      <span class="rail-context">/ run · {{ jobShort }}</span>
      <div class="rail-right">
        <span class="h-chip" :class="statusChipClass">{{ statusLabel }}</span>
      </div>
    </header>

    <main class="doc">
      <!-- LEFT — anchored pitch summary + progress -->
      <aside class="anchor">
        <div class="anchor-head">
          <span class="h-eyebrow">running</span>
          <h1 class="anchor-title h-display">{{ headline }}</h1>
        </div>

        <div class="progress-wrap">
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: progressPct + '%' }"></div>
          </div>
          <div class="progress-meta">
            <span class="progress-pct">{{ progressPct }}%</span>
            <span class="progress-stage">{{ stageLabel }}</span>
          </div>
        </div>

        <div v-if="parsedPitch" class="pitch-card">
          <span class="h-eyebrow">parsed pitch</span>
          <h3 class="pitch-line">{{ parsedPitch.one_liner }}</h3>
          <div class="pitch-row">
            <span class="pitch-key">target</span>
            <span class="pitch-val">{{ parsedPitch.target_icp }}</span>
          </div>
          <div v-if="parsedPitch.icp_segments?.length" class="pitch-row pitch-row-segments">
            <span class="pitch-key">segments</span>
            <div class="seg-chips">
              <span v-for="s in parsedPitch.icp_segments" :key="s" class="seg-chip">{{ s }}</span>
            </div>
          </div>
        </div>

        <div class="counter">
          <div class="counter-num">{{ reactions.length }}</div>
          <div class="counter-label">reactions</div>
        </div>

        <div v-if="error" class="error-box">
          <strong>Failed.</strong>
          <span>{{ error }}</span>
          <button class="h-btn is-ghost retry-btn" @click="$router.push('/new')">try again →</button>
        </div>
      </aside>

      <!-- RIGHT — live stream -->
      <section class="stream">
        <header class="stream-head">
          <span class="h-eyebrow">live · agent reactions</span>
          <span class="stream-count">{{ visibleReactions.length }} shown</span>
        </header>

        <div v-if="visibleReactions.length === 0" class="stream-empty">
          <div class="empty-dot pulse"></div>
          <span>Waiting for the first reaction…</span>
        </div>

        <transition-group name="slide" tag="ol" class="stream-list">
          <li
            v-for="r in visibleReactions"
            :key="r.agent_id"
            class="reaction"
            :class="['tone-' + r.tone, 'action-' + r.action]"
          >
            <div class="r-meta">
              <span class="r-handle">@{{ r.name }}</span>
              <span class="r-action">{{ actionGlyph(r.action) }} {{ r.action }}</span>
              <span class="r-seg">{{ r.segment }}</span>
            </div>
            <div v-if="r.text" class="r-text">{{ r.text }}</div>
            <div v-if="r.objections?.length" class="r-objections">
              <span v-for="o in r.objections" :key="o" class="r-obj">{{ o }}</span>
            </div>
          </li>
        </transition-group>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { roastApi } from '../../api/roast'

const route = useRoute()
const router = useRouter()
const jobId = route.params.jobId

const status = ref('pending')
const progress = ref(0)
const parsedPitch = ref(null)
const reactions = ref([])
const error = ref('')
let evtSource = null
let pollTimer = null

const jobShort = computed(() => (jobId || '').replace('roast_', '').slice(0, 8))
const progressPct = computed(() => Math.round(progress.value * 100))

const STATUS_MAP = {
  pending: 'Queued',
  parsing: 'Parsing pitch',
  generating_archetypes: 'Designing agents',
  running_swarm: 'Agents reacting',
  reporting: 'Synthesizing',
  completed: 'Done',
  failed: 'Failed',
  cancelled: 'Cancelled',
}
const statusLabel = computed(() => STATUS_MAP[status.value] || status.value)
const isRunning = computed(() =>
  !['completed', 'failed', 'cancelled'].includes(status.value),
)
const statusChipClass = computed(() => {
  if (status.value === 'completed') return 'is-live'
  if (['failed', 'cancelled'].includes(status.value)) return 'is-warn'
  return 'is-accent'
})

const stageLabel = computed(() => {
  if (status.value === 'running_swarm') return `${reactions.value.length} reactions in`
  return statusLabel.value
})

const headline = computed(() => {
  if (status.value === 'completed') return 'Roast complete.'
  if (status.value === 'failed') return 'Something broke.'
  if (status.value === 'running_swarm') return 'The swarm is talking.'
  if (status.value === 'reporting') return 'Reading the room.'
  if (status.value === 'generating_archetypes') return 'Casting the crowd.'
  if (status.value === 'parsing') return 'Reading the pitch.'
  return 'Warming up…'
})

const visibleReactions = computed(() => {
  return [...reactions.value]
    .filter(r => r.text || r.action === 'upvote')
    .slice(-80)
    .reverse()
})

function actionGlyph(action) {
  return { post: '◆', comment: '✎', upvote: '↑', ignore: '·' }[action] || '·'
}

function handleEvent(eventName, data) {
  if (eventName === 'status') {
    status.value = data.status || status.value
    if (typeof data.progress === 'number') progress.value = data.progress
    if (data.status === 'failed') error.value = data.error || 'Pipeline failed'
    if (data.status === 'completed') {
      router.replace({ name: 'Result', params: { jobId } })
    }
  } else if (eventName === 'parsed_pitch') {
    parsedPitch.value = data
  } else if (eventName === 'reaction') {
    reactions.value.push(data)
  } else if (eventName === 'done') {
    router.replace({ name: 'Result', params: { jobId } })
  }
}

function startStream() {
  const url = roastApi.streamUrl(jobId)
  evtSource = new EventSource(url)
  for (const name of ['status', 'parsed_pitch', 'archetypes', 'reaction', 'report', 'usage', 'done']) {
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

onMounted(startStream)
onBeforeUnmount(() => {
  if (evtSource) evtSource.close()
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
/* Hallmark · page: Watching · macrostructure: Live Document (split)
 * archetypes: N-rail-tight · S-anchored-left · F-stream-right · Ft-none
 * theme: Midnight+coral (atmospheric)
 */

.page { min-height: 100vh; color: var(--ink); }

/* Rail */
.rail {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--rule);
  position: sticky;
  top: 0;
  background: color-mix(in oklch, var(--paper) 88%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  z-index: 20;
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
.brand-mark .dot.pulse {
  animation: pulse-dot 1.4s var(--ease-in-out) infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; box-shadow: 0 0 14px var(--accent); }
  50% { opacity: 0.55; box-shadow: 0 0 28px var(--accent); }
}

.rail-context {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.08em;
  color: var(--ink-3);
}
.rail-right { margin-left: auto; }

/* Document layout */
.doc {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: var(--space-7);
  max-width: var(--max-content);
  margin: 0 auto;
  padding: var(--space-7) var(--space-6) var(--space-9);
  align-items: start;
}
@media (max-width: 920px) { .doc { grid-template-columns: 1fr; gap: var(--space-5); } }

/* Anchor */
.anchor {
  position: sticky;
  top: 88px;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}
@media (max-width: 920px) { .anchor { position: static; } }

.anchor-head { margin-bottom: 0; }
.anchor-title {
  font-size: var(--text-3xl);
  font-weight: 500;
  font-variation-settings: 'opsz' 144, 'wght' 500;
  margin: var(--space-3) 0 0;
  color: var(--ink);
}

.progress-wrap { display: flex; flex-direction: column; gap: var(--space-3); }
.progress-track {
  height: 4px;
  background: var(--paper-3);
  border-radius: var(--radius-pill);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent-bright));
  transition: width 400ms var(--ease-out);
}
.progress-meta {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.05em;
}
.progress-pct { color: var(--accent-bright); font-size: var(--text-sm); }
.progress-stage { color: var(--ink-3); }

.pitch-card {
  padding: var(--space-5);
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.pitch-line {
  font-family: var(--font-display);
  font-style: italic;
  font-weight: 500;
  font-variation-settings: 'opsz' 96, 'wght' 500;
  font-size: var(--text-xl);
  line-height: 1.25;
  margin: 0;
  color: var(--ink);
}
.pitch-row {
  display: flex;
  gap: var(--space-3);
  align-items: baseline;
  font-size: var(--text-sm);
}
.pitch-row-segments { align-items: flex-start; flex-direction: column; gap: var(--space-2); }
.pitch-key {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-3);
  min-width: 70px;
}
.pitch-val { color: var(--ink-2); }
.seg-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.seg-chip {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  padding: 3px 9px;
  background: var(--accent-soft);
  color: var(--accent-bright);
  border-radius: var(--radius-pill);
}

.counter {
  padding: var(--space-5);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  background: var(--paper-2);
}
.counter-num {
  font-family: var(--font-display);
  font-style: italic;
  font-size: var(--text-3xl);
  line-height: 1;
  color: var(--accent-bright);
}
.counter-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin-top: var(--space-2);
}

/* Stream */
.stream-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--rule);
  margin-bottom: var(--space-4);
}
.stream-count {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--ink-3);
}
.stream-empty {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-7);
  color: var(--ink-3);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}
.empty-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent);
}
.empty-dot.pulse { animation: pulse-dot 1.4s var(--ease-in-out) infinite; }

.stream-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.reaction {
  padding: var(--space-4) var(--space-5);
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius-md);
  border-left: 2px solid var(--ink-4);
}
.reaction.tone-skeptical, .reaction.tone-aggressive { border-left-color: var(--warn); }
.reaction.tone-enthusiastic { border-left-color: var(--live); }
.reaction.tone-curious { border-left-color: var(--info); }
.reaction.tone-indifferent { border-left-color: var(--ink-4); opacity: 0.7; }

.r-meta {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.04em;
}
.r-handle { color: var(--ink); font-weight: 500; }
.r-action {
  color: var(--ink-3);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.r-seg { color: var(--ink-4); margin-left: auto; }

.r-text {
  font-family: var(--font-body);
  font-size: var(--text-md);
  line-height: 1.6;
  color: var(--ink);
  margin-bottom: var(--space-3);
}
.r-objections { display: flex; flex-wrap: wrap; gap: 6px; }
.r-obj {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  padding: 2px 8px;
  background: var(--warn-soft);
  color: var(--warn);
  border-radius: var(--radius-sm);
  text-transform: lowercase;
  letter-spacing: 0.04em;
}

.error-box {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-5);
  background: var(--warn-soft);
  border: 1px solid color-mix(in oklch, var(--warn) 60%, transparent);
  border-radius: var(--radius-lg);
  color: var(--warn);
}
.error-box strong { color: var(--ink); font-family: var(--font-display); font-style: italic; font-size: var(--text-lg); }
.retry-btn { align-self: flex-start; }

/* slide-in for new reactions */
.slide-enter-active { transition: transform var(--dur-base) var(--ease-out), opacity var(--dur-base) var(--ease-out); }
.slide-enter-from { opacity: 0; transform: translateX(8px); }
</style>
