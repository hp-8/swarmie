<template>
  <div class="result">
    <header class="nav">
      <div class="brand" @click="$router.push('/')">SWARMIE</div>
      <div class="actions">
        <button class="ghost" @click="copyShareUrl">{{ copied ? 'Copied!' : 'Copy link' }}</button>
        <button class="ghost" @click="$router.push('/new')">New roast</button>
      </div>
    </header>

    <main v-if="loading" class="loading">Loading report…</main>
    <main v-else-if="error" class="error-page">
      <h2>Report unavailable</h2>
      <p>{{ error }}</p>
      <button class="cta-btn" @click="$router.push('/new')">Start a new roast</button>
    </main>

    <main v-else-if="report" class="content">
      <!-- Score card -->
      <section class="card hero">
        <div class="score-block">
          <div class="score-num" :style="{ color: scoreColor(report.pmf_score) }">
            {{ report.pmf_score }}<span class="of-ten">/10</span>
          </div>
          <div class="score-label">PMF Score</div>
        </div>
        <div class="headline-block">
          <div class="kicker">Headline</div>
          <h1 class="headline">{{ report.headline }}</h1>
          <p v-if="parsedPitch" class="pitch-oneliner">
            For: <strong>{{ parsedPitch.target_icp }}</strong>
          </p>
        </div>
      </section>

      <!-- Narrative -->
      <section class="card">
        <h2 class="card-title">Synthesis</h2>
        <p class="narrative">{{ report.narrative }}</p>
      </section>

      <!-- Top objections -->
      <section class="card">
        <h2 class="card-title">Top objections</h2>
        <div v-if="report.top_objections?.length" class="objections-list">
          <div v-for="obj in report.top_objections" :key="obj.category" class="obj-row">
            <div class="obj-head">
              <span class="obj-cat">{{ obj.category }}</span>
              <span class="obj-count">{{ obj.count }} mentions</span>
            </div>
            <div v-if="obj.example_quote" class="obj-quote">"{{ obj.example_quote }}"</div>
          </div>
        </div>
        <p v-else class="muted">No clear objection clusters surfaced.</p>
      </section>

      <!-- Messaging fixes -->
      <section v-if="report.messaging_gaps?.length" class="card">
        <h2 class="card-title">Messaging fixes to try</h2>
        <ul class="gap-list">
          <li v-for="g in report.messaging_gaps" :key="g">{{ g }}</li>
        </ul>
      </section>

      <!-- Sentiment + action splits -->
      <section class="card splits">
        <div class="split-block">
          <h2 class="card-title">Sentiment</h2>
          <div class="bar-stack">
            <div class="bar pos" :style="{ width: report.sentiment_split.positive + '%' }">
              <span>{{ report.sentiment_split.positive }}%</span>
            </div>
            <div class="bar neu" :style="{ width: report.sentiment_split.neutral + '%' }">
              <span>{{ report.sentiment_split.neutral }}%</span>
            </div>
            <div class="bar neg" :style="{ width: report.sentiment_split.negative + '%' }">
              <span>{{ report.sentiment_split.negative }}%</span>
            </div>
          </div>
          <div class="bar-legend">
            <span><i class="dot pos"></i>Positive</span>
            <span><i class="dot neu"></i>Neutral</span>
            <span><i class="dot neg"></i>Negative</span>
          </div>
        </div>
        <div class="split-block">
          <h2 class="card-title">Actions</h2>
          <div class="action-grid">
            <div v-for="(count, key) in report.action_split" :key="key" class="action-tile">
              <div class="action-count">{{ count }}</div>
              <div class="action-label">{{ key }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- ICP fit -->
      <section v-if="report.icp_fit" class="card">
        <h2 class="card-title">Per-segment fit</h2>
        <div class="icp-list">
          <div v-for="(stats, seg) in report.icp_fit" :key="seg" class="icp-row">
            <div class="icp-name">{{ seg }}</div>
            <div class="icp-meta">
              <span>{{ stats.count }} agents</span>
              <span>avg sentiment: {{ stats.avg_sentiment > 0 ? '+' : '' }}{{ stats.avg_sentiment }}</span>
              <span>{{ stats.dominant_action }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Quoted reactions -->
      <section v-if="report.quoted_reactions?.length" class="card">
        <h2 class="card-title">Most informative reactions</h2>
        <div class="quotes">
          <div v-for="q in report.quoted_reactions" :key="q.agent_id" class="quote-row" :class="'tone-' + q.tone">
            <div class="quote-head">
              <span class="quote-name">@{{ q.name }}</span>
              <span class="quote-tone">{{ q.tone }}</span>
              <span class="quote-seg">{{ q.segment }}</span>
            </div>
            <div class="quote-text">{{ q.text }}</div>
          </div>
        </div>
      </section>

      <!-- Usage -->
      <section v-if="usage" class="card usage">
        <h2 class="card-title">Run cost</h2>
        <div class="usage-meta">
          <span><strong>${{ usage.total_cost_usd?.toFixed(4) || '0.0000' }}</strong> total</span>
          <span>{{ usage.total_tokens?.toLocaleString() }} tokens</span>
          <span>{{ usage.total_calls }} LLM calls</span>
        </div>
      </section>

      <footer class="footer">
        <p>Swarmie is alpha. Reactions are AI-simulated, not real users. Use this as a pre-interview filter, not a replacement for real conversations.</p>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { roastApi } from '../../api/roast'

const route = useRoute()
const jobId = route.params.jobId

const loading = ref(true)
const error = ref('')
const report = ref(null)
const parsedPitch = ref(null)
const usage = ref(null)
const copied = ref(false)

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
      usage.value = j.usage
    }
  } catch (e) {
    error.value = e?.message || 'Failed to load report'
  } finally {
    loading.value = false
  }
}

function scoreColor(score) {
  if (score >= 7) return '#4ade80'
  if (score >= 5) return '#f59e0b'
  return '#f87171'
}

async function copyShareUrl() {
  await navigator.clipboard.writeText(window.location.href)
  copied.value = true
  setTimeout(() => (copied.value = false), 1500)
}

onMounted(load)
</script>

<style scoped>
.result { min-height: 100vh; background: #0b0c10; color: #f4f4f5; font-family: 'Inter', system-ui, sans-serif; }
.nav { display: flex; justify-content: space-between; align-items: center; padding: 20px 32px; border-bottom: 1px solid rgba(255,255,255,0.08); }
.brand { font-weight: 800; letter-spacing: 0.18em; font-size: 14px; cursor: pointer; }
.actions { display: flex; gap: 8px; }
.ghost {
  background: transparent;
  border: 1px solid rgba(255,255,255,0.15);
  color: inherit;
  padding: 8px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.ghost:hover { background: rgba(255,255,255,0.05); }

.content { max-width: 880px; margin: 0 auto; padding: 40px 32px 96px; display: flex; flex-direction: column; gap: 18px; }
.loading, .error-page { max-width: 600px; margin: 80px auto; padding: 0 32px; text-align: center; color: rgba(255,255,255,0.6); }

.card {
  padding: 24px 28px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
}

.card-title { font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em; color: rgba(255,255,255,0.5); margin: 0 0 14px; font-weight: 600; }

.hero { display: flex; align-items: center; gap: 32px; padding: 32px 28px; }
.score-block { text-align: center; flex-shrink: 0; }
.score-num { font-size: 72px; font-weight: 800; line-height: 1; letter-spacing: -0.04em; }
.of-ten { font-size: 28px; font-weight: 500; color: rgba(255,255,255,0.4); margin-left: 4px; }
.score-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.12em; color: rgba(255,255,255,0.5); margin-top: 6px; }

.headline-block { flex: 1; }
.kicker { font-size: 11px; text-transform: uppercase; letter-spacing: 0.12em; color: rgba(255,255,255,0.4); margin-bottom: 6px; }
.headline { font-size: 26px; font-weight: 700; line-height: 1.25; margin: 0; }
.pitch-oneliner { margin: 14px 0 0; color: rgba(255,255,255,0.55); font-size: 14px; }

.narrative { font-size: 16px; line-height: 1.65; color: rgba(255,255,255,0.85); margin: 0; white-space: pre-line; }

.objections-list { display: flex; flex-direction: column; gap: 14px; }
.obj-row { padding: 12px 14px; background: rgba(255,255,255,0.02); border-radius: 8px; border-left: 3px solid #f87171; }
.obj-head { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
.obj-cat { font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #fff; }
.obj-count { color: rgba(255,255,255,0.5); font-size: 12px; }
.obj-quote { font-size: 14px; line-height: 1.5; color: rgba(255,255,255,0.65); font-style: italic; }

.gap-list { margin: 0; padding-left: 20px; line-height: 1.7; color: rgba(255,255,255,0.85); }

.splits { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
@media (max-width: 720px) { .splits { grid-template-columns: 1fr; } }

.bar-stack { display: flex; height: 24px; border-radius: 6px; overflow: hidden; background: rgba(255,255,255,0.05); }
.bar { display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: #0b0c10; transition: width 0.5s; min-width: 0; }
.bar span { padding: 0 6px; }
.bar.pos { background: #4ade80; }
.bar.neu { background: rgba(255,255,255,0.25); color: #fff; }
.bar.neg { background: #f87171; }
.bar-legend { display: flex; gap: 14px; margin-top: 10px; font-size: 12px; color: rgba(255,255,255,0.55); }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; vertical-align: middle; }
.dot.pos { background: #4ade80; } .dot.neu { background: rgba(255,255,255,0.4); } .dot.neg { background: #f87171; }

.action-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.action-tile { padding: 14px 10px; background: rgba(255,255,255,0.04); border-radius: 8px; text-align: center; }
.action-count { font-size: 22px; font-weight: 700; }
.action-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: rgba(255,255,255,0.5); margin-top: 4px; }

.icp-list { display: flex; flex-direction: column; gap: 8px; }
.icp-row { display: flex; justify-content: space-between; padding: 10px 14px; background: rgba(255,255,255,0.02); border-radius: 6px; font-size: 14px; }
.icp-name { font-weight: 500; }
.icp-meta { display: flex; gap: 14px; color: rgba(255,255,255,0.55); font-size: 12px; }

.quotes { display: flex; flex-direction: column; gap: 10px; }
.quote-row { padding: 12px 14px; background: rgba(255,255,255,0.02); border-left: 3px solid rgba(255,255,255,0.15); border-radius: 6px; }
.quote-row.tone-skeptical, .quote-row.tone-aggressive { border-left-color: #f87171; }
.quote-row.tone-enthusiastic { border-left-color: #4ade80; }
.quote-row.tone-curious { border-left-color: #60a5fa; }
.quote-head { display: flex; gap: 10px; font-size: 12px; margin-bottom: 4px; }
.quote-name { font-weight: 600; }
.quote-tone { color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 0.06em; }
.quote-seg { color: rgba(255,255,255,0.35); margin-left: auto; }
.quote-text { font-size: 14px; line-height: 1.5; color: rgba(255,255,255,0.85); }

.usage .usage-meta { display: flex; gap: 24px; font-size: 13px; color: rgba(255,255,255,0.6); }

.muted { color: rgba(255,255,255,0.5); margin: 0; }

.footer { margin-top: 24px; padding: 20px 0; font-size: 12px; color: rgba(255,255,255,0.4); border-top: 1px solid rgba(255,255,255,0.05); line-height: 1.6; }

.cta-btn { background: linear-gradient(90deg, #ff6b35, #f59e0b); color: #0b0c10; font-weight: 700; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; margin-top: 16px; }
</style>
