<template>
  <article class="memo">
    <header class="memo-head">
      <dl class="memo-fields">
        <div><dt>To</dt><dd>Founder</dd></div>
        <div v-if="subject"><dt>Re</dt><dd>{{ subject }}</dd></div>
        <div><dt>Panel</dt><dd>{{ panelLine }}</dd></div>
        <div>
          <dt>Confidence</dt>
          <dd>
            <span class="conf" :class="`is-${report.confidence || 'low'}`">{{ confidenceLabel }}</span>
            <span v-if="report.confidence_reason" class="conf-why">{{ report.confidence_reason }}</span>
          </dd>
        </div>
      </dl>
      <p class="memo-disclose">
        Reviewers are AI agents, not real users. Directional only.
        <AiDisclosure variant="text" label="How this was generated" />
      </p>
    </header>

    <section class="memo-rec" aria-labelledby="rec-title">
      <h1 id="rec-title" class="rec-verdict" :class="verdict.cls">{{ recTitle }}</h1>
      <p v-if="report.verdict_reason" class="rec-reason">{{ report.verdict_reason }}</p>
      <p v-if="report.next_action" class="rec-action"><strong>This week.</strong> {{ report.next_action }}</p>
      <SharpenPanel :report="report" :parsed-pitch="parsedPitch" />
    </section>

    <section v-if="working.length" id="working" class="memo-sec">
      <h2>What's working</h2>
      <ul class="plain">
        <li v-for="(w, i) in working" :key="i">{{ w }}</li>
      </ul>
    </section>

    <section v-if="risks.length" id="risks" class="memo-sec">
      <h2>Hidden risks</h2>
      <ol class="findings">
        <li v-for="(r, i) in risks" :id="`risk-${i + 1}`" :key="i" class="finding">
          <span class="f-num">{{ i + 1 }}</span>
          <div class="f-body">
            <p class="f-title"><span class="flag">Risk</span>{{ r.risk }}</p>
            <p v-if="r.why_non_obvious" class="f-line"><em>Easy to miss because</em> {{ lowerFirst(r.why_non_obvious) }}</p>
            <p v-if="r.cheap_test" class="f-line"><em>Test it:</em> {{ r.cheap_test }}</p>
          </div>
          <button type="button" class="f-link" @click="copyAnchor(`risk-${i + 1}`)">
            {{ copiedAnchor === `risk-${i + 1}` ? 'Link copied' : 'Copy link' }}
          </button>
        </li>
      </ol>
    </section>

    <section id="objections" class="memo-sec">
      <h2>{{ capitalize(copy.objections) }}</h2>
      <ObjectionList :objections="report.top_objections" :copy="copy" :job-id="jobId" />
    </section>

    <section v-if="pathSteps.length > 1" id="path" class="memo-sec">
      <h2>Path forward</h2>
      <dl class="path">
        <div v-for="s in pathSteps" :key="s.key">
          <dt>{{ s.label }}</dt><dd>{{ s.text }}</dd>
        </div>
      </dl>
    </section>

    <section v-if="report.narrative" id="summary" class="memo-sec">
      <h2>Summary</h2>
      <p class="prose">{{ report.narrative }}</p>
      <template v-if="report.messaging_gaps?.length">
        <h3>Fixes to try</h3>
        <ul class="plain">
          <li v-for="g in report.messaging_gaps" :key="g">{{ g }}</li>
        </ul>
      </template>
    </section>

    <section id="exhibits" class="memo-sec exhibits">
      <h2>Exhibits</h2>

      <figure class="exhibit">
        <figcaption><span class="ex-id">A</span>How the {{ spokeCount }} who spoke felt</figcaption>
        <div class="sent" role="img" :aria-label="sentimentAria">
          <span v-for="k in SENT" :key="k" class="sent-seg" :class="k" :style="{ flexGrow: report.sentiment_split[k] || 0 }"></span>
        </div>
        <table class="ex-table">
          <tbody>
            <tr v-for="k in SENT" :key="k"><th scope="row">{{ k }}</th><td class="num">{{ report.sentiment_split[k] }}%</td></tr>
          </tbody>
        </table>
      </figure>

      <figure v-if="report.ignore_reasons?.length" class="exhibit">
        <figcaption><span class="ex-id">B</span>{{ capitalize(copy.silence(report.silent_share_pct)) }}</figcaption>
        <table class="ex-table">
          <thead><tr><th scope="col">Reason</th><th scope="col">What it means</th><th scope="col" class="num">Share</th></tr></thead>
          <tbody>
            <tr v-for="ir in report.ignore_reasons" :key="ir.category">
              <th scope="row">{{ ir.label }}</th>
              <td>{{ ir.implication || ir.example }}</td>
              <td class="num">{{ ir.share_pct }}%</td>
            </tr>
          </tbody>
        </table>
      </figure>

      <figure v-if="report.quoted_reactions?.length" class="exhibit">
        <figcaption><span class="ex-id">{{ exId('voices') }}</span>{{ capitalize(copy.voices) }}</figcaption>
        <QuotesList :quotes="report.quoted_reactions" />
      </figure>

      <figure v-if="segments.length" class="exhibit">
        <figcaption><span class="ex-id">{{ exId('segments') }}</span>{{ capitalize(copy.segments) }}</figcaption>
        <table class="ex-table">
          <thead><tr><th scope="col">Segment</th><th scope="col" class="num">Reviewers</th></tr></thead>
          <tbody>
            <tr v-for="s in segments" :key="s.name"><th scope="row">{{ s.name }}</th><td class="num">{{ s.count ?? '' }}</td></tr>
          </tbody>
        </table>
      </figure>

      <figure v-if="usage" class="exhibit">
        <figcaption><span class="ex-id">{{ exId('cost') }}</span>Run cost</figcaption>
        <table class="ex-table">
          <tbody>
            <tr><th scope="row">Cost</th><td class="num">{{ costLabel }}</td></tr>
            <tr><th scope="row">Tokens</th><td class="num">{{ Number(usage.total_tokens || 0).toLocaleString() }}</td></tr>
            <tr><th scope="row">Model calls</th><td class="num">{{ usage.total_calls }}</td></tr>
          </tbody>
        </table>
      </figure>
    </section>
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
const lowerFirst = (s) => (s ? s.charAt(0).toLowerCase() + s.slice(1) : '')

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
const pathSteps = computed(() => {
  const p = props.report.path_forward || {}
  return PATH_LABELS.filter((s) => p[s.key]).map((s) => ({ ...s, text: p[s.key] }))
})

const segments = computed(() =>
  Object.entries(props.report.icp_fit || {}).map(([name, v]) => ({ name, count: v?.count })),
)

// Exhibit letters follow whichever exhibits actually render.
const exhibitOrder = computed(() => [
  'sentiment',
  props.report.ignore_reasons?.length && 'silence',
  props.report.quoted_reactions?.length && 'voices',
  segments.value.length && 'segments',
  props.usage && 'cost',
].filter(Boolean))
const exId = (key) => String.fromCharCode(65 + exhibitOrder.value.indexOf(key))

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
.memo {
  max-width: 880px;
  margin: 0 auto;
  padding: var(--space-8) var(--space-6) var(--space-9);
  color: var(--ink);
}

/* Header block: the memo's routing fields */
.memo-head { border-bottom: 2px solid var(--ink); padding-bottom: var(--space-5); }
.memo-fields { display: grid; gap: var(--space-2); margin: 0; }
.memo-fields > div { display: grid; grid-template-columns: 112px minmax(0, 1fr); gap: var(--space-4); align-items: baseline; }
.memo-fields dt { font-size: var(--text-sm); color: var(--ink-3); }
.memo-fields dd { margin: 0; font-size: var(--text-base); font-weight: 600; overflow-wrap: anywhere; }
.conf { font-weight: 600; }
.conf.is-low { color: var(--warn); }
.conf-why { display: block; font-weight: 400; color: var(--ink-3); font-size: var(--text-sm); }
.memo-disclose { margin: var(--space-4) 0 0; font-size: var(--text-sm); color: var(--ink-3); }

/* Recommendation */
.memo-rec { padding: var(--space-7) 0 var(--space-6); border-bottom: 1px solid var(--rule); animation: settle 520ms var(--ease-out) both; }
.rec-verdict {
  margin: 0;
  font-family: var(--font-display);
  font-weight: 600;
  font-size: clamp(40px, 6vw, 68px);
  line-height: 1.02;
  letter-spacing: -0.02em;
  text-wrap: balance;
  overflow-wrap: anywhere;
}
.rec-verdict.is-kill, .rec-verdict.is-wrong { color: var(--warn); }
.rec-reason {
  margin: var(--space-4) 0 0;
  font-family: var(--font-display);
  font-size: clamp(19px, 2.2vw, 23px);
  line-height: 1.45;
  color: var(--ink-2);
  max-width: 62ch;
}
.rec-action {
  margin: var(--space-6) 0 var(--space-5);
  padding: var(--space-4) var(--space-5);
  background: var(--paper-2);
  border-top: 1px solid var(--rule-2);
  font-size: var(--text-md);
  line-height: 1.5;
  max-width: 68ch;
}
.rec-action strong { font-weight: 700; margin-right: var(--space-1); }

/* Sections */
.memo-sec { padding: var(--space-7) 0 0; }
.memo-sec h2 {
  margin: 0 0 var(--space-4);
  font-size: var(--text-lg);
  font-weight: 700;
  letter-spacing: -0.01em;
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--rule);
}
.memo-sec h3 { margin: var(--space-6) 0 var(--space-3); font-size: var(--text-base); font-weight: 700; }
.prose { margin: 0; font-family: var(--font-display); font-size: var(--text-md); line-height: 1.65; max-width: 68ch; color: var(--ink-2); white-space: pre-line; }
.plain { margin: 0; padding-left: 1.1em; display: grid; gap: var(--space-2); max-width: 68ch; line-height: 1.55; }

/* Numbered findings with margin flags */
.findings { list-style: none; margin: 0; padding: 0; display: grid; }
.finding {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) auto;
  gap: var(--space-4);
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--rule);
  scroll-margin-top: var(--space-9);
}
.finding:target { background: var(--warn-soft); }
.f-num { font-weight: 700; color: var(--ink-3); font-variant-numeric: tabular-nums; }
.f-title { margin: 0; font-weight: 600; font-size: var(--text-md); line-height: 1.4; }
.flag {
  display: inline-block;
  margin-right: var(--space-2);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--warn);
  vertical-align: 0.12em;
}
.f-line { margin: var(--space-2) 0 0; color: var(--ink-2); line-height: 1.55; max-width: 66ch; }
.f-line em { font-style: normal; font-weight: 600; color: var(--ink); }
.f-link {
  align-self: start;
  font: inherit;
  font-size: var(--text-sm);
  color: var(--ink-3);
  background: none;
  border: 0;
  padding: var(--space-1) 0;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
  white-space: nowrap;
}
.f-link:hover { color: var(--ink); }

/* Path forward */
.path { margin: 0; display: grid; }
.path > div { display: grid; grid-template-columns: 112px minmax(0, 1fr); gap: var(--space-4); padding: var(--space-3) 0; border-bottom: 1px solid var(--rule); }
.path dt { font-weight: 700; }
.path dd { margin: 0; color: var(--ink-2); line-height: 1.55; }

/* Exhibits */
.exhibits { display: grid; gap: var(--space-6); }
.exhibits h2 { margin-bottom: 0; }
.exhibit { margin: 0; }
.exhibit figcaption { font-weight: 700; margin-bottom: var(--space-3); }
.ex-id { display: inline-block; min-width: 1.6em; color: var(--ink-3); }
.sent { display: flex; height: 10px; gap: 2px; margin-bottom: var(--space-3); }
.sent-seg { flex-basis: 0; min-width: 0; }
.sent-seg.positive { background: var(--live); }
.sent-seg.neutral { background: var(--rule-2); }
.sent-seg.negative { background: var(--warn); }
.ex-table { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
.ex-table th, .ex-table td { text-align: left; padding: var(--space-2) var(--space-3) var(--space-2) 0; border-bottom: 1px solid var(--rule); vertical-align: top; }
.ex-table thead th { color: var(--ink-3); font-weight: 600; border-bottom-color: var(--ink); }
.ex-table tbody th { font-weight: 600; }
.ex-table tbody th::first-letter { text-transform: uppercase; }
.ex-table .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; padding-right: 0; }

@keyframes settle { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }

@media (max-width: 767px) {
  .memo { padding: var(--space-6) var(--space-4) var(--space-8); }
  .memo-fields > div, .path > div { grid-template-columns: 88px minmax(0, 1fr); gap: var(--space-3); }
  .finding { grid-template-columns: 24px minmax(0, 1fr); }
  .f-link { grid-column: 2; justify-self: start; }
}
</style>
