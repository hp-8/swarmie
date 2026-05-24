<template>
  <div class="page">
    <header class="rail">
      <router-link to="/" class="brand-mark">
        <span class="dot"></span>
        <span class="brand-text">SWARMIE</span>
      </router-link>
      <span class="rail-context">/ result · {{ jobShort }}</span>
      <div class="rail-right">
        <button class="rail-action" @click="copyShareUrl">
          {{ copied ? '✓ link copied' : 'copy link' }}
        </button>
        <router-link to="/new" class="rail-action accent">new roast →</router-link>
      </div>
    </header>

    <main v-if="loading" class="state-msg">Loading report…</main>

    <main v-else-if="error" class="state-msg">
      <h2 class="state-title h-display">Report unavailable.</h2>
      <p>{{ error }}</p>
      <router-link to="/new" class="h-btn is-accent">Start a new roast →</router-link>
    </main>

    <main v-else-if="report" class="body">
      <!-- HERO — score is the headline -->
      <section class="score-hero">
        <div class="score-left">
          <span class="h-eyebrow">PMF score · /10</span>
          <div class="score-num" :style="{ color: scoreColor(report.pmf_score) }">
            {{ report.pmf_score }}
          </div>
          <div class="score-band" :style="{ color: scoreColor(report.pmf_score) }">
            {{ scoreBand(report.pmf_score) }}
          </div>
        </div>
        <div class="score-right">
          <h1 class="score-headline h-display">{{ report.headline }}</h1>
          <p v-if="parsedPitch" class="score-target">
            <span class="h-eyebrow">target</span>
            <span class="target-val">{{ parsedPitch.target_icp }}</span>
          </p>
        </div>
      </section>

      <hr class="h-rule" />

      <!-- NARRATIVE -->
      <section class="narrative">
        <span class="h-eyebrow">synthesis</span>
        <p class="narrative-body">{{ report.narrative }}</p>
      </section>

      <!-- BENTO — objections (wide) + splits (tall) -->
      <section class="bento">
        <article class="cell cell-objections span-wide">
          <header class="cell-head">
            <span class="h-eyebrow">top objections</span>
            <span class="cell-meta">{{ report.top_objections?.length || 0 }} clusters</span>
          </header>
          <ol v-if="report.top_objections?.length" class="obj-list">
            <li v-for="(obj, i) in report.top_objections" :key="obj.category" class="obj-row">
              <span class="obj-rank">{{ String(i + 1).padStart(2, '0') }}</span>
              <div class="obj-body">
                <div class="obj-head">
                  <span class="obj-cat">{{ obj.category }}</span>
                  <span class="obj-count">{{ obj.count }} mentions</span>
                </div>
                <p v-if="obj.example_quote" class="obj-quote">"{{ obj.example_quote }}"</p>
              </div>
            </li>
          </ol>
          <p v-else class="muted">No clear objection clusters.</p>
        </article>

        <article class="cell cell-sentiment">
          <header class="cell-head"><span class="h-eyebrow">sentiment</span></header>
          <div class="sent-bar">
            <div class="sent-seg pos" :style="{ flex: report.sentiment_split.positive }">
              <span v-if="report.sentiment_split.positive >= 8">{{ report.sentiment_split.positive }}%</span>
            </div>
            <div class="sent-seg neu" :style="{ flex: report.sentiment_split.neutral }">
              <span v-if="report.sentiment_split.neutral >= 8">{{ report.sentiment_split.neutral }}%</span>
            </div>
            <div class="sent-seg neg" :style="{ flex: report.sentiment_split.negative }">
              <span v-if="report.sentiment_split.negative >= 8">{{ report.sentiment_split.negative }}%</span>
            </div>
          </div>
          <div class="sent-legend">
            <span><i class="dot pos"></i> {{ report.sentiment_split.positive }}% positive</span>
            <span><i class="dot neu"></i> {{ report.sentiment_split.neutral }}% neutral</span>
            <span><i class="dot neg"></i> {{ report.sentiment_split.negative }}% negative</span>
          </div>
        </article>

        <article class="cell cell-actions">
          <header class="cell-head"><span class="h-eyebrow">actions</span></header>
          <div class="action-grid">
            <div v-for="(count, key) in report.action_split" :key="key" class="action-tile">
              <div class="action-count">{{ count }}</div>
              <div class="action-label">{{ key }}</div>
            </div>
          </div>
        </article>

        <article v-if="report.messaging_gaps?.length" class="cell cell-fixes span-wide">
          <header class="cell-head"><span class="h-eyebrow">messaging fixes to try</span></header>
          <ul class="fix-list">
            <li v-for="g in report.messaging_gaps" :key="g">{{ g }}</li>
          </ul>
        </article>
      </section>

      <!-- ICP fit -->
      <section v-if="report.icp_fit && Object.keys(report.icp_fit).length" class="icp">
        <header class="icp-head">
          <span class="h-eyebrow">per-segment fit</span>
          <h2 class="icp-title h-display">Who's the swarm rooting for?</h2>
        </header>
        <div class="icp-grid">
          <div v-for="(stats, seg) in report.icp_fit" :key="seg" class="icp-row">
            <div class="icp-name">{{ seg }}</div>
            <div class="icp-stats">
              <span class="icp-stat">
                <span class="stat-num">{{ stats.count }}</span>
                <span class="stat-label">agents</span>
              </span>
              <span class="icp-stat">
                <span class="stat-num" :class="sentClass(stats.avg_sentiment)">
                  {{ stats.avg_sentiment > 0 ? '+' : '' }}{{ stats.avg_sentiment }}
                </span>
                <span class="stat-label">sentiment</span>
              </span>
              <span class="icp-stat">
                <span class="stat-num small">{{ stats.dominant_action }}</span>
                <span class="stat-label">mostly</span>
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- Quoted reactions -->
      <section v-if="report.quoted_reactions?.length" class="quotes-section">
        <header class="qs-head">
          <span class="h-eyebrow">the loudest voices</span>
          <h2 class="qs-title h-display">What they actually said.</h2>
        </header>
        <div class="quotes">
          <article v-for="q in report.quoted_reactions" :key="q.agent_id" class="quote" :class="'tone-' + q.tone">
            <div class="q-handle">@{{ q.name }}</div>
            <p class="q-text">{{ q.text }}</p>
            <div class="q-meta">
              <span class="q-tone">{{ q.tone }}</span>
              <span class="q-seg">{{ q.segment }}</span>
            </div>
          </article>
        </div>
      </section>

      <!-- Run cost -->
      <section v-if="usage" class="usage">
        <span class="h-eyebrow">run cost</span>
        <div class="usage-row">
          <div class="usage-stat">
            <div class="usage-num">${{ (usage.total_cost_usd || 0).toFixed(4) }}</div>
            <div class="usage-label">total</div>
          </div>
          <div class="usage-stat">
            <div class="usage-num">{{ (usage.total_tokens || 0).toLocaleString() }}</div>
            <div class="usage-label">tokens</div>
          </div>
          <div class="usage-stat">
            <div class="usage-num">{{ usage.total_calls }}</div>
            <div class="usage-label">LLM calls</div>
          </div>
        </div>
      </section>

      <footer class="foot">
        <p>
          Swarmie is alpha. Reactions are AI-simulated, <em>not real users</em>.
          Use as a pre-interview filter — not a replacement for real conversations.
        </p>
        <p class="foot-cta">
          <router-link to="/new">Run another →</router-link>
          <a href="https://github.com/hp-8/swarmie" target="_blank">github ↗</a>
        </p>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
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
      usage.value = j.usage
    }
  } catch (e) {
    error.value = e?.message || 'Failed to load report'
  } finally {
    loading.value = false
  }
}

function scoreColor(s) {
  if (s >= 7) return 'var(--live)'
  if (s >= 5) return 'var(--accent-bright)'
  return 'var(--warn)'
}
function scoreBand(s) {
  if (s >= 8) return 'strong signal'
  if (s >= 6.5) return 'positive lean'
  if (s >= 5) return 'mixed'
  if (s >= 3.5) return 'rough seas'
  return 'flat line'
}
function sentClass(v) {
  if (v > 0.15) return 'pos'
  if (v < -0.15) return 'neg'
  return ''
}

async function copyShareUrl() {
  await navigator.clipboard.writeText(window.location.href)
  copied.value = true
  setTimeout(() => (copied.value = false), 1500)
}

onMounted(load)
</script>

<style scoped>
/* Hallmark · page: Result · macrostructure: Stat-Led + Bento
 * archetypes: N-rail-actions · H-score-hero · S-narrative · F-bento · Ft-quiet
 * theme: Midnight+coral (atmospheric)
 */

.page { min-height: 100vh; color: var(--ink); }

/* Rail with action buttons */
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
  z-index: 20;
}
.brand-mark {
  display: inline-flex; align-items: center; gap: var(--space-2);
  font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.22em;
}
.brand-mark .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 14px var(--accent); }
.rail-context {
  font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.08em; color: var(--ink-3);
}
.rail-right { margin-left: auto; display: flex; gap: var(--space-2); }
.rail-action {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.06em;
  padding: 8px 14px;
  background: transparent;
  border: 1px solid var(--rule-2);
  color: var(--ink-2);
  border-radius: var(--radius-pill);
  cursor: pointer;
  transition: all var(--dur-fast) var(--ease-out);
}
.rail-action:hover { color: var(--ink); border-color: var(--ink-2); }
.rail-action.accent {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--paper);
}

/* state msgs */
.state-msg {
  max-width: 560px;
  margin: var(--space-10) auto;
  padding: 0 var(--space-5);
  text-align: center;
  color: var(--ink-2);
}
.state-title { font-size: var(--text-3xl); color: var(--ink); margin: 0 0 var(--space-3); }

.body {
  max-width: var(--max-content);
  margin: 0 auto;
  padding: var(--space-7) var(--space-6) var(--space-10);
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

/* SCORE HERO */
.score-hero {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--space-8);
  align-items: center;
  padding: var(--space-6) 0 var(--space-7);
}
@media (max-width: 720px) {
  .score-hero { grid-template-columns: 1fr; gap: var(--space-5); }
}
.score-left { text-align: center; }
.score-num {
  font-family: var(--font-display);
  font-style: italic;
  font-weight: 600;
  font-variation-settings: 'opsz' 144, 'wght' 600;
  font-size: clamp(120px, 22vw, 220px);
  line-height: 0.85;
  letter-spacing: -0.05em;
  margin-top: var(--space-3);
  text-shadow: 0 0 60px currentColor;
}
.score-band {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  margin-top: var(--space-3);
}

.score-right { display: flex; flex-direction: column; gap: var(--space-4); }
.score-headline {
  font-size: clamp(28px, 4.5vw, 44px);
  font-weight: 500;
  font-variation-settings: 'opsz' 144, 'wght' 500;
  margin: 0;
  color: var(--ink);
}
.score-target { display: flex; flex-direction: column; gap: var(--space-2); margin: 0; }
.target-val { color: var(--ink-2); font-size: var(--text-md); }

/* NARRATIVE */
.narrative { display: flex; flex-direction: column; gap: var(--space-4); max-width: var(--max-prose); }
.narrative-body {
  font-family: var(--font-body);
  font-size: var(--text-lg);
  line-height: 1.65;
  color: var(--ink);
  margin: 0;
  white-space: pre-line;
}

/* BENTO grid */
.bento {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
}
@media (max-width: 880px) { .bento { grid-template-columns: 1fr; } }

.cell {
  padding: var(--space-5) var(--space-6);
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.cell.span-wide { grid-column: span 2; }
@media (max-width: 880px) { .cell.span-wide { grid-column: span 1; } }

.cell-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.cell-meta { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--ink-3); }

.obj-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: var(--space-4); }
.obj-row { display: grid; grid-template-columns: 36px 1fr; gap: var(--space-4); align-items: start; }
.obj-rank {
  font-family: var(--font-display);
  font-style: italic;
  font-size: var(--text-xl);
  color: var(--accent-bright);
}
.obj-head {
  display: flex; justify-content: space-between; align-items: baseline; gap: var(--space-3);
  margin-bottom: var(--space-2);
}
.obj-cat {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink);
}
.obj-count { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--ink-3); }
.obj-quote {
  font-family: var(--font-display);
  font-style: italic;
  font-weight: 500;
  font-variation-settings: 'opsz' 96, 'wght' 500;
  font-size: var(--text-md);
  line-height: 1.55;
  color: var(--ink);
  margin: 0;
}

.sent-bar { display: flex; height: 32px; border-radius: var(--radius-md); overflow: hidden; background: var(--paper-3); }
.sent-seg { display: flex; align-items: center; justify-content: center; font-family: var(--font-mono); font-size: var(--text-xs); font-weight: 600; min-width: 0; transition: flex 480ms var(--ease-out); }
.sent-seg.pos { background: var(--live); color: var(--paper); }
.sent-seg.neu { background: var(--ink-4); color: var(--ink); }
.sent-seg.neg { background: var(--warn); color: var(--paper); }
.sent-legend { display: flex; flex-direction: column; gap: var(--space-2); font-size: var(--text-xs); font-family: var(--font-mono); color: var(--ink-3); }
.sent-legend i.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: var(--space-2); }
.sent-legend i.dot.pos { background: var(--live); } .sent-legend i.dot.neu { background: var(--ink-4); } .sent-legend i.dot.neg { background: var(--warn); }

.action-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-3); }
.action-tile {
  padding: var(--space-4);
  background: var(--paper-3);
  border-radius: var(--radius-md);
  text-align: center;
}
.action-count {
  font-family: var(--font-display);
  font-style: italic;
  font-weight: 500;
  font-variation-settings: 'opsz' 96, 'wght' 500;
  font-size: var(--text-2xl);
  color: var(--ink);
}
.action-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin-top: 4px;
}

.fix-list { margin: 0; padding-left: var(--space-5); line-height: 1.7; color: var(--ink); }
.fix-list li::marker { color: var(--accent-bright); }

/* ICP */
.icp-head { margin-bottom: var(--space-5); }
.icp-title {
  font-size: var(--text-3xl);
  font-weight: 500;
  font-variation-settings: 'opsz' 144, 'wght' 500;
  margin: var(--space-2) 0 0;
}
.icp-grid { display: flex; flex-direction: column; gap: var(--space-2); }
.icp-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--space-5);
  padding: var(--space-4) var(--space-5);
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius-md);
  align-items: center;
}
.icp-name { font-size: var(--text-md); color: var(--ink); }
.icp-stats { display: flex; gap: var(--space-5); align-items: center; }
.icp-stat { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.stat-num { font-family: var(--font-mono); font-size: var(--text-md); color: var(--ink); }
.stat-num.small { font-size: var(--text-sm); }
.stat-num.pos { color: var(--live); }
.stat-num.neg { color: var(--warn); }
.stat-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-4);
}

/* QUOTES */
.qs-head { margin-bottom: var(--space-5); }
.qs-title {
  font-size: var(--text-3xl);
  font-weight: 500;
  font-variation-settings: 'opsz' 144, 'wght' 500;
  margin: var(--space-2) 0 0;
}
.quotes {
  columns: 2;
  column-gap: var(--space-4);
}
@media (max-width: 720px) { .quotes { columns: 1; } }
.quote {
  break-inside: avoid;
  margin-bottom: var(--space-4);
  padding: var(--space-5);
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius-md);
  border-left: 2px solid var(--ink-4);
}
.quote.tone-skeptical, .quote.tone-aggressive { border-left-color: var(--warn); }
.quote.tone-enthusiastic { border-left-color: var(--live); }
.quote.tone-curious { border-left-color: var(--info); }

.q-handle {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.06em;
  color: var(--accent-bright);
  margin-bottom: var(--space-2);
}
.q-text {
  font-family: var(--font-display);
  font-style: italic;
  font-weight: 500;
  font-variation-settings: 'opsz' 96, 'wght' 500;
  font-size: var(--text-md);
  line-height: 1.55;
  color: var(--ink);
  margin: 0 0 var(--space-3);
}
.q-meta {
  display: flex;
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--ink-3);
}
.q-tone { text-transform: uppercase; letter-spacing: 0.08em; }

/* USAGE */
.usage { padding: var(--space-5) 0; border-top: 1px solid var(--rule); display: flex; flex-direction: column; gap: var(--space-3); }
.usage-row { display: flex; gap: var(--space-7); flex-wrap: wrap; }
.usage-stat { display: flex; flex-direction: column; gap: 2px; }
.usage-num {
  font-family: var(--font-display);
  font-style: italic;
  font-weight: 500;
  font-variation-settings: 'opsz' 96, 'wght' 500;
  font-size: var(--text-2xl);
  color: var(--ink);
}
.usage-label {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-3);
}

/* FOOT */
.foot {
  padding: var(--space-5) 0;
  border-top: 1px solid var(--rule);
  font-size: var(--text-sm);
  color: var(--ink-3);
  line-height: 1.6;
}
.foot em { color: var(--ink); font-style: italic; }
.foot-cta { display: flex; gap: var(--space-5); margin-top: var(--space-3); font-family: var(--font-mono); font-size: var(--text-xs); }
.foot-cta a { color: var(--ink-2); }
.foot-cta a:hover { color: var(--accent-bright); }

.muted { color: var(--ink-3); font-size: var(--text-sm); margin: 0; }
</style>
