<template>
  <div class="page page-fixed">
    <header class="rail">
      <router-link to="/" class="brand-mark">
        <span class="dot"></span>
        <span class="brand-text">SWARMIE</span>
      </router-link>
      <span class="rail-context">/ result · {{ jobShort }}</span>
      <div class="rail-right">
        <button class="rail-action" @click="copyShareUrl">
          {{ copied ? '✓ copied' : 'copy link' }}
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

    <main v-else-if="report" class="dash">
      <!-- ROW 1 — Hero strip: score + headline + sentiment bar -->
      <section class="strip strip-hero">
        <div class="cell cell-score">
          <span class="h-eyebrow">PMF · /10</span>
          <div class="score-num" :style="{ color: scoreColor(report.pmf_score) }">{{ scoreDisplayed.toFixed(1) }}</div>
          <div class="score-band" :style="{ color: scoreColor(report.pmf_score) }">{{ scoreBand(report.pmf_score) }}</div>
        </div>
        <div class="cell cell-headline">
          <span class="h-eyebrow">headline</span>
          <h1 class="score-headline h-display">{{ report.headline }}</h1>
          <p v-if="parsedPitch" class="score-target">
            <span class="target-key">target:</span>
            <span class="target-val">{{ parsedPitch.target_icp }}</span>
          </p>
        </div>
        <div class="cell cell-sentiment">
          <span class="h-eyebrow">sentiment</span>
          <div class="sent-bar">
            <div class="sent-seg pos" :style="{ flex: report.sentiment_split.positive }">
              <span v-if="report.sentiment_split.positive >= 10">{{ report.sentiment_split.positive }}%</span>
            </div>
            <div class="sent-seg neu" :style="{ flex: report.sentiment_split.neutral }">
              <span v-if="report.sentiment_split.neutral >= 10">{{ report.sentiment_split.neutral }}%</span>
            </div>
            <div class="sent-seg neg" :style="{ flex: report.sentiment_split.negative }">
              <span v-if="report.sentiment_split.negative >= 10">{{ report.sentiment_split.negative }}%</span>
            </div>
          </div>
          <div class="sent-legend">
            <span><i class="dot pos"></i>{{ report.sentiment_split.positive }}%</span>
            <span><i class="dot neu"></i>{{ report.sentiment_split.neutral }}%</span>
            <span><i class="dot neg"></i>{{ report.sentiment_split.negative }}%</span>
          </div>
          <div class="action-mini">
            <span v-for="(count, key) in report.action_split" :key="key" class="action-mini-cell">
              <span class="amc-num">{{ count }}</span>
              <span class="amc-lbl">{{ key }}</span>
            </span>
          </div>
        </div>
      </section>

      <!-- ROW 2 — Three columns: narrative · objections · quotes -->
      <section class="strip strip-three">
        <article class="cell cell-narrative">
          <header class="cell-head"><span class="h-eyebrow">synthesis</span></header>
          <div class="scroll-zone narrative-scroll">
            <p class="narrative-body">{{ report.narrative }}</p>
            <div v-if="report.messaging_gaps?.length" class="fixes">
              <span class="h-eyebrow">fixes to try</span>
              <ul class="fix-list">
                <li v-for="g in report.messaging_gaps" :key="g">{{ g }}</li>
              </ul>
            </div>
          </div>
        </article>

        <article class="cell cell-objections">
          <header class="cell-head">
            <span class="h-eyebrow">top objections</span>
            <span class="cell-meta">{{ report.top_objections?.length || 0 }}</span>
          </header>
          <ol v-if="report.top_objections?.length" class="obj-list scroll-zone">
            <li v-for="(obj, i) in report.top_objections" :key="obj.category" class="obj-row">
              <span class="obj-rank">{{ String(i + 1).padStart(2, '0') }}</span>
              <div class="obj-body">
                <div class="obj-head-row">
                  <span class="obj-cat">{{ obj.category }}</span>
                  <span class="obj-count">{{ obj.count }}×</span>
                </div>
                <p v-if="obj.example_quote" class="obj-quote">"{{ obj.example_quote }}"</p>
              </div>
            </li>
          </ol>
          <p v-else class="muted">No clear clusters.</p>
        </article>

        <article class="cell cell-quotes">
          <header class="cell-head">
            <span class="h-eyebrow">loudest voices</span>
            <span class="cell-meta">{{ report.quoted_reactions?.length || 0 }}</span>
          </header>
          <div class="quotes-list scroll-zone">
            <article v-for="q in report.quoted_reactions" :key="q.agent_id" class="quote" :class="'tone-' + q.tone">
              <div class="q-handle">@{{ q.name }}</div>
              <p class="q-text">{{ q.text }}</p>
              <div class="q-meta">
                <span class="q-tone">{{ q.tone }}</span>
                <span class="q-seg">{{ q.segment }}</span>
              </div>
            </article>
            <p v-if="!report.quoted_reactions?.length" class="muted">No standout reactions.</p>
          </div>
        </article>
      </section>

      <!-- ROW 3 — ICP fit + usage strip -->
      <section class="strip strip-foot">
        <article class="cell cell-icp" v-if="segmentNames.length">
          <header class="cell-head">
            <span class="h-eyebrow">segments</span>
            <span class="cell-meta">{{ segmentNames.length }}</span>
          </header>
          <div class="segment-tags">
            <span v-for="name in segmentNames" :key="name" class="segment-tag">{{ name }}</span>
          </div>
        </article>

        <article v-if="usage" class="cell cell-usage">
          <header class="cell-head">
            <span class="h-eyebrow">run cost</span>
            <span v-if="costDisplay.equiv" class="cost-equiv-tag">gpt-4o-mini equiv</span>
          </header>
          <div class="usage-row">
            <div class="usage-stat">
              <div class="usage-num">
                <span v-if="costDisplay.equiv" class="approx">≈</span>${{ costDisplay.value }}
              </div>
              <div class="usage-label">total</div>
            </div>
            <div class="usage-stat">
              <div class="usage-num">{{ formatTokens(usage.total_tokens) }}</div>
              <div class="usage-label">tokens</div>
            </div>
            <div class="usage-stat">
              <div class="usage-num">{{ usage.total_calls }}</div>
              <div class="usage-label">calls</div>
            </div>
          </div>
        </article>
      </section>
    </main>

    <footer v-if="report" class="foot-strip">
      Alpha · AI agents, <em>not real users</em>. Pre-interview filter only.
      <span class="foot-sep">·</span>
      <router-link to="/new" class="foot-cta">run another →</router-link>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
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

// Animated score count-up
const scoreDisplayed = ref(0)

// Equivalent cost: when real run cost is sub-cent (e.g. local Ollama) we still
// show what the same workload would have cost on a known commercial model.
// Reference: gpt-4o-mini blended pricing — input $0.15 / output $0.60 per 1M.
// Use 0.7×input + 0.3×output as a rough mix.
const REFERENCE_PRICE_PER_MTOK = (0.7 * 0.15) + (0.3 * 0.60) // = $0.285 / 1M

// Plain list of segment names — display only. No sorting, no ranking.
const segmentNames = computed(() => {
  const icp = report.value?.icp_fit
  if (!icp) return []
  return Object.keys(icp)
})

const costDisplay = computed(() => {
  if (!usage.value) return { value: '0.0000', equiv: false }
  const real = Number(usage.value.total_cost_usd || 0)
  if (real >= 0.001) {
    return { value: real.toFixed(4), equiv: false }
  }
  // Derive equivalent from token count
  const tokens = Number(usage.value.total_tokens || 0)
  const derived = Math.max(0.0012, (tokens / 1_000_000) * REFERENCE_PRICE_PER_MTOK)
  return { value: derived.toFixed(4), equiv: true }
})

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

function formatTokens(n) {
  const v = Number(n || 0)
  if (v < 1000) return v.toLocaleString()
  if (v < 1_000_000) return (v / 1000).toFixed(v >= 10_000 ? 0 : 1) + 'k'
  return (v / 1_000_000).toFixed(2) + 'M'
}

async function copyShareUrl() {
  await navigator.clipboard.writeText(window.location.href)
  copied.value = true
  setTimeout(() => (copied.value = false), 1500)
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

onMounted(load)
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
.brand-mark { display: inline-flex; align-items: center; gap: var(--space-2); font-family: var(--font-mono); font-size: var(--text-xs); font-weight: 600; letter-spacing: 0.22em; }
.brand-mark .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 14px var(--accent); }
.rail-context { font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.08em; color: var(--ink-2); }
.rail-right { margin-left: auto; display: flex; gap: var(--space-2); }
.rail-action {
  font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.06em;
  padding: 7px 13px; background: transparent;
  border: 1px solid var(--rule-2); color: var(--ink-2);
  border-radius: var(--radius-pill); cursor: pointer;
  transition: all var(--dur-fast) var(--ease-out);
}
.rail-action:hover { color: var(--ink); border-color: var(--ink-2); }
.rail-action.accent { background: var(--accent); border-color: var(--accent); color: var(--paper); }
.rail-action:active { transform: scale(0.96); }

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

/* Dashboard grid */
.dash {
  flex: 1;
  display: grid;
  grid-template-rows: minmax(150px, 0.7fr) minmax(0, 1.4fr) minmax(110px, 0.4fr);
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  max-width: 1480px;
  width: 100%;
  margin: 0 auto;
  min-height: 0;
  overflow: hidden;
}

.strip { display: grid; gap: var(--space-3); min-height: 0; }
.strip-hero { grid-template-columns: 220px 1.4fr 1fr; }
.strip-three { grid-template-columns: 1fr 1fr 1fr; }
.strip-foot { grid-template-columns: 1.6fr 1fr; }

@media (max-width: 1100px) {
  .strip-hero { grid-template-columns: 180px 1fr 1fr; }
  .strip-three { grid-template-columns: 1fr 1fr; }
  .strip-three .cell-quotes { display: none; }
}
@media (max-width: 760px) {
  .dash { grid-template-rows: auto auto auto; overflow-y: auto; }
  .page.page-fixed { height: auto; overflow: auto; }
  .strip-hero, .strip-three, .strip-foot { grid-template-columns: 1fr; }
}

.cell {
  padding: var(--space-4);
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-height: 0;
  overflow: hidden;
  opacity: 0;
  transform: translateY(8px);
  animation: cell-in var(--dur-slow) var(--ease-out) forwards;
}
.strip-hero .cell { animation-delay: 60ms; }
.strip-three .cell-narrative { animation-delay: 140ms; }
.strip-three .cell-objections { animation-delay: 200ms; }
.strip-three .cell-quotes { animation-delay: 260ms; }
.strip-foot .cell { animation-delay: 340ms; }

@keyframes cell-in {
  to { opacity: 1; transform: translateY(0); }
}

.cell-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-shrink: 0;
}
.cell-meta { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--ink-3); }

/* SCORE */
.cell-score { text-align: center; justify-content: center; align-items: center; padding: var(--space-3); }
.score-num {
  font-family: var(--font-display); font-style: italic; font-weight: 600;
  font-variation-settings: 'opsz' 144, 'wght' 600;
  font-size: clamp(72px, 11vh, 120px);
  line-height: 0.85; letter-spacing: -0.05em;
  text-shadow: 0 0 60px currentColor;
}
.score-band { font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.16em; text-transform: uppercase; }

/* HEADLINE */
.cell-headline { gap: var(--space-2); justify-content: center; }
.score-headline {
  font-size: clamp(20px, 2.6vh, 30px);
  font-weight: 500; font-variation-settings: 'opsz' 144, 'wght' 500;
  margin: 0; color: var(--ink);
}
.score-target { display: flex; gap: var(--space-2); align-items: baseline; margin: 0; font-size: var(--text-sm); }
.target-key { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--ink-3); text-transform: uppercase; letter-spacing: 0.08em; }
.target-val { color: var(--ink-2); }

/* SENTIMENT cell */
.cell-sentiment { gap: var(--space-2); }
.sent-bar { display: flex; height: 22px; border-radius: var(--radius-sm); overflow: hidden; background: var(--paper-3); }
.sent-seg { display: flex; align-items: center; justify-content: center; font-family: var(--font-mono); font-size: 10px; font-weight: 700; min-width: 0; transition: flex 480ms var(--ease-out); }
.sent-seg.pos { background: var(--live); color: var(--paper); }
.sent-seg.neu { background: var(--ink-4); color: var(--ink); }
.sent-seg.neg { background: var(--warn); color: var(--paper); }
.sent-legend { display: flex; gap: var(--space-4); font-family: var(--font-mono); font-size: var(--text-xs); color: var(--ink-2); }
.sent-legend i.dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
.sent-legend i.dot.pos { background: var(--live); } .sent-legend i.dot.neu { background: var(--ink-4); } .sent-legend i.dot.neg { background: var(--warn); }
.action-mini { display: flex; gap: var(--space-4); margin-top: var(--space-1); }
.action-mini-cell { display: flex; flex-direction: column; gap: 1px; }
.amc-num { font-family: var(--font-display); font-style: italic; font-weight: 500; font-size: var(--text-md); color: var(--ink); }
.amc-lbl { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-3); }

/* NARRATIVE */
.narrative-scroll { padding-right: var(--space-3); }
.narrative-body {
  font-family: var(--font-body);
  font-size: var(--text-sm); line-height: 1.6; color: var(--ink);
  margin: 0 0 var(--space-4); white-space: pre-line;
}
.fixes { display: flex; flex-direction: column; gap: var(--space-2); }
.fix-list { margin: 0; padding-left: var(--space-4); line-height: 1.55; color: var(--ink); font-size: var(--text-sm); }
.fix-list li::marker { color: var(--accent-bright); }

/* OBJECTIONS */
.obj-list { list-style: none; padding: 0 var(--space-3) 0 0; margin: 0; display: flex; flex-direction: column; gap: var(--space-3); }
.obj-row { display: grid; grid-template-columns: 28px 1fr; gap: var(--space-3); align-items: start; }
.obj-rank {
  font-family: var(--font-display); font-style: italic; font-weight: 500;
  font-size: var(--text-lg); color: var(--accent-bright); line-height: 1;
}
.obj-head-row { display: flex; justify-content: space-between; gap: var(--space-3); margin-bottom: 2px; }
.obj-cat { font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink); }
.obj-count { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--ink-3); }
.obj-quote {
  font-family: var(--font-display); font-style: italic; font-weight: 500;
  font-variation-settings: 'opsz' 72, 'wght' 500;
  font-size: var(--text-sm); line-height: 1.5; color: var(--ink-2); margin: 0;
}

/* QUOTES */
.quotes-list { padding: 0 var(--space-3) 0 0; display: flex; flex-direction: column; gap: var(--space-3); }
.quote {
  padding: var(--space-3) var(--space-4);
  background: var(--paper-3);
  border-left: 2px solid var(--ink-4);
  border-radius: var(--radius-sm);
  transition: transform var(--dur-fast) var(--ease-out),
              background var(--dur-base) var(--ease-out),
              border-left-width var(--dur-fast) var(--ease-out);
}
.quote:hover {
  transform: translateX(2px);
  background: var(--paper-4);
}
.quote.tone-skeptical, .quote.tone-aggressive { border-left-color: var(--warn); }
.quote.tone-enthusiastic { border-left-color: var(--live); }
.quote.tone-curious { border-left-color: var(--info); }
.q-handle { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.06em; color: var(--accent-bright); margin-bottom: 4px; }
.q-text {
  font-family: var(--font-display); font-style: italic; font-weight: 500;
  font-size: var(--text-sm); line-height: 1.45; color: var(--ink); margin: 0 0 var(--space-2);
}
.q-meta { display: flex; justify-content: space-between; font-family: var(--font-mono); font-size: 10px; color: var(--ink-3); }
.q-tone { text-transform: uppercase; letter-spacing: 0.08em; }

/* ICP fit — plain orange tags. Nothing else. */
.cell-icp { gap: var(--space-3); }
.segment-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  padding-right: var(--space-2);
}
.segment-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--accent-bright);
  background: var(--accent-soft);
  border: 1px solid color-mix(in oklch, var(--accent) 35%, transparent);
  border-radius: var(--radius-pill);
  white-space: nowrap;
}

/* USAGE */
.cell-usage { gap: var(--space-3); }
.usage-row { display: flex; gap: var(--space-5); }
.usage-stat { display: flex; flex-direction: column; gap: 1px; }
.usage-num { font-family: var(--font-display); font-style: italic; font-weight: 500; font-size: var(--text-xl); color: var(--ink); }
.usage-label { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-3); }
.approx { color: var(--ink-3); font-style: normal; margin-right: 2px; }
.cost-equiv-tag {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.06em;
  color: var(--accent-bright);
  background: var(--accent-soft);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
}

/* FOOT */
.foot-strip {
  flex-shrink: 0;
  padding: var(--space-2) var(--space-6);
  border-top: 1px solid var(--rule);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--ink-3);
  text-align: center;
}
.foot-strip em { color: var(--ink); font-style: italic; }
.foot-sep { margin: 0 var(--space-2); color: var(--rule-2); }
.foot-cta { color: var(--accent-bright); }
.foot-cta:hover { color: var(--ink); }

.muted { color: var(--ink-3); font-size: var(--text-sm); margin: 0; }
</style>
