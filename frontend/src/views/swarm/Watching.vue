<template>
  <div class="watching">
    <header class="nav">
      <div class="brand" @click="$router.push('/')">SWARMIE</div>
      <div class="status-pill" :class="statusClass">{{ statusLabel }}</div>
    </header>

    <main class="content">
      <h1 class="title">{{ headline }}</h1>
      <p class="sub">{{ subline }}</p>

      <div class="progress-track">
        <div class="progress-fill" :style="{ width: progressPct + '%' }"></div>
      </div>
      <div class="progress-meta">{{ progressPct }}% — {{ stageLabel }}</div>

      <div v-if="parsedPitch" class="pitch-summary">
        <div class="kv"><span>One-liner:</span> {{ parsedPitch.one_liner }}</div>
        <div class="kv"><span>Target ICP:</span> {{ parsedPitch.target_icp }}</div>
        <div class="kv segments">
          <span>Segments:</span>
          <span v-for="s in parsedPitch.icp_segments" :key="s" class="chip">{{ s }}</span>
        </div>
      </div>

      <section class="feed">
        <h2 class="feed-title">Live reactions <span class="count">{{ reactions.length }}</span></h2>
        <transition-group name="fade" tag="div" class="feed-list">
          <article
            v-for="r in visibleReactions"
            :key="r.agent_id"
            class="reaction"
            :class="['tone-' + r.tone, 'action-' + r.action]"
          >
            <div class="r-head">
              <span class="r-name">@{{ r.name }}</span>
              <span class="r-tag">{{ r.action }}</span>
              <span class="r-seg">{{ r.segment }}</span>
            </div>
            <div v-if="r.text" class="r-body">{{ r.text }}</div>
            <div v-if="r.objections?.length" class="r-objections">
              <span v-for="o in r.objections" :key="o" class="obj-chip">{{ o }}</span>
            </div>
          </article>
        </transition-group>
      </section>

      <div v-if="error" class="error-box">
        <strong>Roast failed:</strong> {{ error }}
        <button class="retry-btn" @click="$router.push('/new')">Try again</button>
      </div>
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

const progressPct = computed(() => Math.round(progress.value * 100))

const statusLabel = computed(() => {
  const map = {
    pending: 'Queued',
    parsing: 'Parsing pitch',
    generating_archetypes: 'Designing agents',
    running_swarm: 'Agents reacting',
    reporting: 'Synthesizing',
    completed: 'Done',
    failed: 'Failed',
    cancelled: 'Cancelled',
  }
  return map[status.value] || status.value
})

const statusClass = computed(() => {
  if (['completed'].includes(status.value)) return 'good'
  if (['failed', 'cancelled'].includes(status.value)) return 'bad'
  return 'running'
})

const stageLabel = computed(() => {
  if (status.value === 'running_swarm') return `${reactions.value.length} reactions in`
  return statusLabel.value
})

const headline = computed(() => {
  if (status.value === 'completed') return 'Roast complete.'
  if (status.value === 'failed') return 'Something broke.'
  return 'Running the swarm…'
})

const subline = computed(() => {
  if (status.value === 'completed') return 'Loading your report…'
  return 'Watch the agents react in real time. This takes about a minute.'
})

const visibleReactions = computed(() => {
  // Newest first, cap to last 50 to keep DOM light.
  return [...reactions.value]
    .filter((r) => r.text || r.action === 'upvote')
    .slice(-50)
    .reverse()
})

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
      try {
        handleEvent(name, JSON.parse(e.data))
      } catch (err) {
        console.warn('Bad SSE payload', name, err)
      }
    })
  }
  evtSource.onerror = () => {
    // EventSource auto-reconnects; if it doesn't, fall back to polling.
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
    } catch (err) {
      console.warn('poll failed', err)
    }
  }, 2000)
}

onMounted(() => {
  startStream()
})

onBeforeUnmount(() => {
  if (evtSource) evtSource.close()
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.watching { min-height: 100vh; background: #0b0c10; color: #f4f4f5; font-family: 'Inter', system-ui, sans-serif; }
.nav { display: flex; justify-content: space-between; align-items: center; padding: 20px 32px; border-bottom: 1px solid rgba(255,255,255,0.08); }
.brand { font-weight: 800; letter-spacing: 0.18em; font-size: 14px; cursor: pointer; }
.status-pill { font-size: 12px; padding: 6px 12px; border-radius: 999px; border: 1px solid rgba(255,255,255,0.12); }
.status-pill.running { color: #f59e0b; border-color: rgba(245,158,11,0.3); }
.status-pill.good { color: #4ade80; border-color: rgba(74,222,128,0.3); }
.status-pill.bad { color: #f87171; border-color: rgba(248,113,113,0.3); }

.content { max-width: 880px; margin: 0 auto; padding: 48px 32px 96px; }
.title { font-size: 36px; font-weight: 700; line-height: 1.2; margin: 0 0 8px; }
.sub { color: rgba(255,255,255,0.5); margin: 0 0 28px; }

.progress-track { height: 6px; background: rgba(255,255,255,0.06); border-radius: 999px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #ff6b35, #f59e0b); transition: width 0.4s ease; }
.progress-meta { margin-top: 10px; font-size: 13px; color: rgba(255,255,255,0.5); }

.pitch-summary {
  margin: 32px 0;
  padding: 16px 20px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  font-size: 14px;
  display: flex; flex-direction: column; gap: 8px;
}
.kv { color: rgba(255,255,255,0.75); }
.kv > span:first-child { color: rgba(255,255,255,0.45); margin-right: 8px; }
.segments { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.chip { background: rgba(245,158,11,0.12); color: #f59e0b; padding: 3px 10px; border-radius: 999px; font-size: 12px; }

.feed-title { font-size: 14px; text-transform: uppercase; letter-spacing: 0.08em; color: rgba(255,255,255,0.5); margin: 32px 0 16px; }
.count { color: #f59e0b; }

.feed-list { display: flex; flex-direction: column; gap: 10px; }
.reaction {
  padding: 14px 16px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-left: 3px solid rgba(255,255,255,0.15);
  border-radius: 8px;
}
.reaction.tone-skeptical, .reaction.tone-aggressive { border-left-color: #f87171; }
.reaction.tone-enthusiastic { border-left-color: #4ade80; }
.reaction.tone-curious { border-left-color: #60a5fa; }
.reaction.tone-indifferent { border-left-color: rgba(255,255,255,0.2); }

.r-head { display: flex; gap: 10px; align-items: baseline; margin-bottom: 6px; font-size: 12px; }
.r-name { font-weight: 600; color: #fff; }
.r-tag { color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 0.08em; }
.r-seg { color: rgba(255,255,255,0.35); margin-left: auto; }
.r-body { font-size: 14px; line-height: 1.5; color: rgba(255,255,255,0.85); }
.r-objections { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; }
.obj-chip { font-size: 11px; padding: 2px 8px; border-radius: 4px; background: rgba(248,113,113,0.1); color: #f87171; text-transform: uppercase; letter-spacing: 0.05em; }

.fade-enter-active { transition: all 0.25s; }
.fade-enter-from { opacity: 0; transform: translateY(-6px); }

.error-box {
  margin-top: 32px;
  padding: 16px;
  background: rgba(248,113,113,0.08);
  border: 1px solid rgba(248,113,113,0.2);
  border-radius: 10px;
  color: #f87171;
}
.retry-btn {
  margin-left: 12px;
  padding: 6px 12px;
  background: transparent;
  border: 1px solid currentColor;
  border-radius: 6px;
  color: inherit;
  cursor: pointer;
}
</style>
