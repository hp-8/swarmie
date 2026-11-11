<template>
  <article class="memo">
    <header class="memo-head">
      <p v-if="subject" class="memo-re">{{ subject }}</p>
      <dl class="memo-facts">
        <div><dt>Panel</dt><dd>{{ panelLine }}</dd></div>
        <div>
          <dt>Confidence</dt>
          <dd><span class="conf" :class="`is-${report.confidence || 'low'}`">{{ confidenceLabel }}</span></dd>
        </div>
      </dl>
      <p class="memo-disclose">
        AI reviewers, not real users.
        <AiDisclosure variant="text" label="How this works" />
      </p>
    </header>

    <div class="board">
      <section class="cell cell-rec" aria-labelledby="rec-title">
        <h1 id="rec-title" class="rec-verdict" :class="verdict.cls">{{ recTitle }}</h1>
        <p v-if="report.verdict_reason" class="rec-reason">{{ report.verdict_reason }}</p>
        <p v-if="report.confidence_reason" class="rec-conf">{{ report.confidence_reason }}</p>
        <div v-if="working.length" id="working" class="working">
          <h2>What's working</h2>
          <ul class="plain plain-good">
            <li v-for="(w, i) in working" :key="i">{{ w }}</li>
          </ul>
        </div>
        <SharpenPanel :report="report" :parsed-pitch="parsedPitch" />
      </section>

      <section class="cell cell-act" aria-label="What to do next">
        <p v-if="thisWeek" class="rec-action">
          <strong class="act-label">This week</strong>
          <span class="act-text">{{ thisWeek }}</span>
        </p>
        <dl v-if="branchSteps.length" id="path" class="path">
          <div v-for="s in branchSteps" :key="s.key">
            <dt>{{ s.label }}</dt><dd>{{ s.text }}</dd>
          </div>
        </dl>
        <div v-if="fixes.length" class="reword">
          <h2>Reword the pitch</h2>
          <ul class="plain">
            <li v-for="g in fixes" :key="g">{{ g }}</li>
          </ul>
        </div>
      </section>

      <section v-if="risks.length" id="risks" class="cell cell-risks">
        <h2>Hidden risks</h2>
        <ol class="findings">
          <li v-for="(r, i) in risks" :id="`risk-${i + 1}`" :key="i" class="finding">
            <p class="f-title"><span class="flag">Risk {{ i + 1 }}</span>{{ r.risk }}</p>
            <p v-if="r.why_non_obvious" class="f-line"><em>Easy to miss:</em> {{ r.why_non_obvious }}</p>
            <p v-if="r.cheap_test" class="f-line"><em>Test it:</em> {{ r.cheap_test }}</p>
            <button type="button" class="f-link" :aria-label="`Copy link to risk ${i + 1}`" @click="copyAnchor(`risk-${i + 1}`)">
              {{ copiedAnchor === `risk-${i + 1}` ? 'Link copied' : 'Copy link' }}
            </button>
          </li>
        </ol>
      </section>

      <section id="objections" class="cell cell-objections">
        <h2>{{ capitalize(copy.objections) }}</h2>
        <ObjectionList :objections="report.top_objections" :copy="copy" :job-id="jobId" />
      </section>

      <figure class="cell cell-ex">
        <figcaption>How the {{ spokeCount }} who spoke felt</figcaption>
        <div class="sent" role="img" :aria-label="sentimentAria">
          <span v-for="k in SENT" :key="k" class="sent-seg" :class="k" :style="{ flexGrow: report.sentiment_split[k] || 0 }"></span>
        </div>
        <ul class="sent-key">
          <li v-for="k in SENT" :key="k"><span class="dot" :class="k"></span>{{ capitalize(k) }} <b>{{ report.sentiment_split[k] }}%</b></li>
        </ul>
      </figure>

      <figure v-if="report.ignore_reasons?.length" class="cell cell-ex">
        <figcaption>{{ capitalize(copy.silence(Math.round(report.silent_share_pct || 0))) }}</figcaption>
        <ul class="bars">
          <li v-for="ir in report.ignore_reasons" :key="ir.category">
            <div class="bar-row"><span>{{ ir.label }}</span><b>{{ ir.share_pct }}%</b></div>
            <span class="bar" :style="{ '--w': `${ir.share_pct}%` }"></span>
            <p v-if="ir.implication || ir.example" class="bar-note">{{ ir.implication || ir.example }}</p>
          </li>
        </ul>
      </figure>

      <figure v-if="segments.length" class="cell cell-ex">
        <figcaption>{{ capitalize(copy.segments) }}</figcaption>
        <ul class="bars">
          <li v-for="s in segments" :key="s.name">
            <div class="bar-row"><span>{{ capitalize(s.name) }}</span><b>{{ s.count ?? '' }}</b></div>
            <span class="bar is-muted" :style="{ '--w': `${segShare(s.count)}%` }"></span>
          </li>
        </ul>
      </figure>

      <figure v-if="voices.length" class="cell cell-voices">
        <figcaption>{{ capitalize(copy.voices) }}</figcaption>
        <QuotesList :quotes="voices" />
      </figure>
    </div>

    <footer class="memo-foot">
      <details v-if="report.narrative" id="summary" class="summary">
        <summary>Read the panel's full summary</summary>
        <p class="prose">{{ report.narrative }}</p>
      </details>
      <p v-if="usage" class="cost">
        This run: <span class="num">{{ costLabel }}</span> · {{ Number(usage.total_tokens || 0).toLocaleString() }} tokens · {{ usage.total_calls }} model calls
      </p>
    </footer>
  </article>
</template>

<script setup>
import { ref, computed } from 'vue'
import AiDisclosure from '../AiDisclosure.vue'
import ObjectionList from './ObjectionList.vue'
import QuotesList from './QuotesList.vue'
import SharpenPanel from './SharpenPanel.vue'
import { verdictMeta, recPhrase } from '../../lib/verdict'

const props = defineProps({
  report: { type: Object, required: true },
  parsedPitch: { type: Object, default: null },
  usage: { type: Object, default: null },
  copy: { type: Object, required: true },
  jobId: { type: String, required: true },
  reactionCount: { type: Number, default: 0 },
})

const SENT = ['positive', 'neutral', 'negative']
const PATH_LABELS = [
  { key: 'this_week', label: 'This week' },
  { key: 'if_confirmed', label: 'If it holds' },
  { key: 'if_not', label: 'If not' },
]

const capitalize = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : '')

const verdict = computed(() => verdictMeta(props.report.verdict))
const recTitle = computed(() => recPhrase(props.report.verdict) || props.report.headline)
const subject = computed(() => props.parsedPitch?.one_liner || props.parsedPitch?.target_icp || '')
const confidenceLabel = computed(() => ({ low: 'Low', med: 'Medium', high: 'High' })[props.report.confidence] || 'Low')

const actions = computed(() => props.report.action_split || {})
const spokeCount = computed(() => (actions.value.comment || 0) + (actions.value.post || 0))
const panelLine = computed(() => {
  const total = props.reactionCount || Object.values(actions.value).reduce((a, b) => a + b, 0)
  return `${total} reviewers · ${spokeCount.value} spoke · ${Math.round(props.report.silent_share_pct || 0)}% scrolled past`
})
const sentimentAria = computed(() => SENT.map((k) => `${props.report.sentiment_split[k]}% ${k}`).join(', '))

const working = computed(() => props.report.what_working || [])
const risks = computed(() => props.report.hidden_risks || [])
// "This week" already leads the action cell (next_action), so the path shows only its branches.
const branchSteps = computed(() => {
  const p = props.report.path_forward || {}
  return PATH_LABELS.filter((s) => s.key !== 'this_week' && p[s.key]).map((s) => ({ ...s, text: p[s.key] }))
})
const fixes = computed(() => props.report.messaging_gaps || [])
const thisWeek = computed(() => props.report.next_action || props.report.path_forward?.this_week || '')

// Objection cards already quote their example; don't show the same line twice.
const voices = computed(() => {
  const shown = new Set((props.report.top_objections || []).map((o) => (o.example_quote || '').trim().toLowerCase()))
  return (props.report.quoted_reactions || []).filter((q) => !shown.has((q.text || '').trim().toLowerCase()))
})

const segments = computed(() =>
  Object.entries(props.report.icp_fit || {}).map(([name, v]) => ({ name, count: v?.count })),
)

const segTotal = computed(() => segments.value.reduce((a, s) => a + (Number(s.count) || 0), 0))
const segShare = (n) => (segTotal.value ? Math.round(((Number(n) || 0) / segTotal.value) * 100) : 0)

// Real cost only. Sub-tenth-of-a-cent runs (local models) say so instead of inventing a figure.
const costLabel = computed(() => {
  const c = Number(props.usage?.total_cost_usd || 0)
  return c >= 0.001 ? `$${c.toFixed(4)}` : 'under $0.001'
})

const copiedAnchor = ref(null)
async function copyAnchor(id) {
  const url = `${window.location.origin}${window.location.pathname}#${id}`
  try { await navigator.clipboard.writeText(url) } catch { /* clipboard blocked */ }
  copiedAnchor.value = id
  setTimeout(() => { if (copiedAnchor.value === id) copiedAnchor.value = null }, 1600)
}
</script>

<style scoped>
/*
 * Layout: one ledger board. Cells share hairline rules (1px gaps over the rule
 * colour) instead of floating cards, so the page reads as one document, scanned
 * in decision order: verdict → this week → risks / what works → objections →
 * evidence → voices.
 */
.memo {
  max-width: 1240px;
  margin: 0 auto;
  padding: var(--space-7) var(--space-6) var(--space-8);
  color: var(--ink);
}

/* Header: subject on the left, the panel facts on one line, disclosure right */
.memo-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--space-2) var(--space-6);
  padding-bottom: var(--space-4);
}
.memo-re { margin: 0; flex: 1 1 32ch; font-weight: 600; line-height: 1.4; max-width: 70ch; }
.memo-facts { display: flex; flex-wrap: wrap; gap: var(--space-1) var(--space-5); margin: 0; font-size: var(--text-sm); }
.memo-facts > div { display: flex; gap: var(--space-2); }
.memo-facts dt { color: var(--ink-3); }
.memo-facts dd { margin: 0; font-weight: 600; font-variant-numeric: tabular-nums; }
.conf { font-weight: 600; }
.conf.is-low { background: var(--warn-hl); padding: 0.05em 0.4em; border-radius: 3px; }
.memo-disclose { margin: 0; font-size: var(--text-sm); color: var(--ink-3); }

/* The board */
.board {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 1px;
  background: var(--rule);
  border: 1px solid var(--rule);
}
.cell { margin: 0; background: var(--paper); padding: var(--space-6); min-width: 0; }
.cell h2,
.cell figcaption { margin: 0 0 var(--space-4); font-size: var(--text-base); font-weight: 700; letter-spacing: -0.005em; }

.cell-rec { grid-column: span 7; padding: var(--space-7) var(--space-6); }
.cell-act { grid-column: span 5; background: var(--paper-2); display: flex; flex-direction: column; gap: var(--space-5); padding: var(--space-7) var(--space-6); }
.cell-risks { grid-column: 1 / -1; }
.cell-objections { grid-column: 1 / -1; }
.cell-ex { grid-column: span 4; }
.cell-voices { grid-column: 1 / -1; }

/* Recommendation */
.rec-verdict {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 600;
  font-size: clamp(40px, 4.6vw, 64px);
  line-height: 1.02;
  letter-spacing: -0.02em;
  text-wrap: balance;
}
.rec-verdict.is-kill, .rec-verdict.is-wrong { background: linear-gradient(transparent 58%, var(--warn-hl) 58%); -webkit-box-decoration-break: clone; box-decoration-break: clone; width: fit-content; }
.rec-reason { margin: var(--space-4) 0 0; font-family: var(--font-display); font-size: clamp(18px, 1.6vw, 21px); line-height: 1.45; color: var(--ink-2); max-width: 56ch; text-wrap: pretty; }
.rec-conf { margin: var(--space-3) 0 0; font-size: var(--text-sm); color: var(--ink-3); max-width: 60ch; }
.cell-rec :deep(.sharpen) { margin-top: var(--space-5); }

/* Action cell: this week leads, branches follow */
.rec-action { margin: 0; display: grid; gap: var(--space-2); }
.act-label { font-size: var(--text-sm); font-weight: 700; color: var(--ink-3); }
.act-text { font-size: var(--text-lg); font-weight: 600; line-height: 1.4; text-wrap: pretty; }
.path { margin: 0; display: grid; gap: var(--space-4); padding-top: var(--space-5); border-top: 1px solid var(--rule-2); }
.path > div { display: grid; gap: var(--space-1); }
.path dt { font-size: var(--text-sm); font-weight: 700; color: var(--ink-3); }
.path dd { margin: 0; line-height: 1.5; color: var(--ink-2); }

/* Hidden risks: two-up inside their cell so three risks fit one screen */
.findings { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--space-5) var(--space-7); }
.finding { position: relative; display: grid; align-content: start; gap: var(--space-2); scroll-margin-top: var(--space-9); }
.finding:target { outline: 2px solid var(--warn-hl); outline-offset: 6px; border-radius: 2px; }
.f-title { margin: 0; font-weight: 600; font-size: var(--text-md); line-height: 1.4; text-wrap: pretty; }
.flag {
  display: inline-block;
  margin-right: var(--space-2);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  background: var(--warn-hl);
  padding: 0.1em 0.45em;
  border-radius: 3px;
  vertical-align: 0.12em;
}
.f-line { margin: 0; color: var(--ink-2); line-height: 1.5; font-size: var(--text-sm); }
.f-line em { font-style: normal; font-weight: 600; color: var(--ink); }
/* Present for keyboard and touch; quiet until the finding is hovered or focused. */
.f-link {
  justify-self: start;
  font: inherit;
  font-size: var(--text-xs);
  color: var(--ink-3);
  background: none;
  border: 0;
  padding: var(--space-1) 0;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
  opacity: 0.55;
  transition: opacity var(--dur-fast) var(--ease-out);
}
.finding:hover .f-link, .f-link:focus-visible { opacity: 1; }
.f-link:hover { color: var(--ink); }

/* What's working (under the verdict) and the rewording list (in the action cell) */
.working { margin-top: var(--space-6); padding-top: var(--space-5); border-top: 1px solid var(--rule); }
.working h2, .reword h2 { font-size: var(--text-sm); font-weight: 700; color: var(--ink-3); margin-bottom: var(--space-3); }
.reword { padding-top: var(--space-5); border-top: 1px solid var(--rule-2); }
.plain { margin: 0; padding-left: 1.1em; display: grid; gap: var(--space-3); line-height: 1.5; font-size: var(--text-sm); color: var(--ink-2); }
.plain-good li::marker { color: var(--live); }

/* Objections: one column each, side by side */
.cell-objections :deep(.obj-list) { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--space-6); }
.cell-objections :deep(.obj-row) { border: 0; padding: 0; }
.cell-objections :deep(.obj-guide > div) { grid-template-columns: minmax(0, 1fr); gap: var(--space-1); }
.cell-objections :deep(.obj-tag) { justify-self: start; }

/* Evidence */
.sent { display: flex; height: 8px; gap: 2px; border-radius: 2px; overflow: hidden; }
.sent-seg { flex-basis: 0; min-width: 0; }
.sent-seg.positive, .dot.positive { background: var(--live); }
.sent-seg.neutral, .dot.neutral { background: var(--rule-2); }
.sent-seg.negative, .dot.negative { background: var(--warn); }
.sent-key { list-style: none; margin: var(--space-4) 0 0; padding: 0; display: grid; gap: var(--space-2); font-size: var(--text-sm); color: var(--ink-2); }
.sent-key li { display: flex; align-items: center; gap: var(--space-2); }
.sent-key b { margin-left: auto; color: var(--ink); font-variant-numeric: tabular-nums; }
.dot { width: 8px; height: 8px; border-radius: 50%; flex: none; }

.bars { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-4); }
.bar-row { display: flex; justify-content: space-between; gap: var(--space-3); font-size: var(--text-sm); }
.bar-row b { font-variant-numeric: tabular-nums; }
.bar { display: block; margin-top: var(--space-2); height: 6px; border-radius: 3px; background: linear-gradient(90deg, var(--ink-2) var(--w), var(--paper-3) var(--w)); }
.bar.is-muted { background: linear-gradient(90deg, var(--ink-4) var(--w), var(--paper-3) var(--w)); }
.bar-note { margin: var(--space-2) 0 0; font-size: var(--text-sm); line-height: 1.45; color: var(--ink-3); }

/* Voices: quotes side by side */
.cell-voices :deep(.quotes-list) { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: var(--space-5) var(--space-6); }
.cell-voices :deep(.quote) { border: 0; padding: 0; }

/* Footer */
.memo-foot { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: var(--space-3) var(--space-6); padding-top: var(--space-5); font-size: var(--text-sm); color: var(--ink-3); }
.summary { flex: 1 1 40ch; max-width: 72ch; }
.summary summary { cursor: pointer; color: var(--ink-2); font-weight: 600; text-decoration: underline; text-underline-offset: 3px; }
.summary[open] summary { margin-bottom: var(--space-3); }
.prose { margin: 0; font-family: var(--font-display); font-size: var(--text-md); line-height: 1.6; color: var(--ink-2); white-space: pre-line; }
.cost .num { color: var(--ink-2); font-weight: 600; font-variant-numeric: tabular-nums; }

/* Settle in once, as one sheet */
.board { animation: settle 460ms var(--ease-out) both; }
@keyframes settle { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
@media (prefers-reduced-motion: reduce) { .board { animation: none; } }

@media (max-width: 1099px) {
  .cell-rec, .cell-act { grid-column: 1 / -1; }
  .cell-ex { grid-column: span 6; }
  .cell-ex:last-of-type:nth-of-type(odd) { grid-column: 1 / -1; }
}
@media (max-width: 767px) {
  .memo { padding: var(--space-5) var(--space-4) var(--space-7); }
  .board { grid-template-columns: minmax(0, 1fr); }
  .cell, .cell-rec, .cell-act { grid-column: 1 / -1; padding: var(--space-5) var(--space-4); }
  .memo-head { gap: var(--space-2); }
}
</style>
