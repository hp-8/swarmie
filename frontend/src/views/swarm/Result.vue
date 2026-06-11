<template>
  <div class="page page-fixed">
    <header class="rail">
      <router-link to="/" class="brand-mark">
        <span class="dot"></span>
        <span class="brand-text">SWARMIE</span>
      </router-link>
      <span class="rail-context">/ result · {{ jobShort }}</span>
      <div class="rail-right">
        <div class="rail-tabs">
          <button class="rail-tab" :class="{ active: tab === 'report' }" @click="tab = 'report'">report</button>
          <button class="rail-tab" :class="{ active: tab === 'brain' }" @click="tab = 'brain'">brain</button>
        </div>
        <button class="rail-action" @click="copyShareUrl">
          {{ copied ? '✓ copied' : 'copy link' }}
        </button>
        <button class="rail-action" @click="shareCard" :disabled="sharingCard || !report">
          <span v-if="sharingCard">rendering…</span>
          <span v-else>↑ share card</span>
        </button>
        <button class="rail-action rail-pdf" @click="downloadPdf" :disabled="downloading || !report">
          <span v-if="downloading">building…</span>
          <span v-else>↓ download PDF</span>
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

    <!-- Deck Diagnosis layout — investor + deck_diagnosis present -->
    <main v-else-if="report && deckDiagnosis" class="diag-dash scroll-zone">
      <!-- Hero: readiness + stage + overall score -->
      <section class="strip strip-diag-hero">
        <div class="cell cell-readiness">
          <span class="h-eyebrow">funding readiness</span>
          <div class="readiness-pct" :style="{ color: readinessColor(deckDiagnosis.readiness_pct) }">
            {{ deckDiagnosis.readiness_pct }}<span class="readiness-unit">%</span>
          </div>
          <div class="readiness-bar" role="progressbar" :aria-valuenow="deckDiagnosis.readiness_pct" aria-valuemin="0" aria-valuemax="100">
            <div class="readiness-fill" :style="{ width: deckDiagnosis.readiness_pct + '%', background: readinessColor(deckDiagnosis.readiness_pct) }"></div>
          </div>
        </div>
        <div class="cell cell-diag-meta">
          <span class="h-eyebrow">stage</span>
          <div class="diag-stage">{{ deckDiagnosis.stage }}</div>
          <p class="diag-stage-hint">overall score</p>
          <div class="diag-overall" :style="{ color: scoreColor(deckDiagnosis.overall_score / 13) }">
            {{ deckDiagnosis.overall_score }}<span class="diag-overall-denom">/130</span>
          </div>
        </div>
        <div class="cell cell-next-move">
          <span class="h-eyebrow">next move</span>
          <p class="next-move-text">{{ deckDiagnosis.next_move }}</p>
        </div>
      </section>

      <!-- Slide scorecard -->
      <section class="strip strip-diag-main">
        <article class="cell cell-scorecard">
          <header class="cell-head">
            <span class="h-eyebrow">slide scorecard</span>
            <span class="cell-meta">{{ deckDiagnosis.slides?.length || 0 }} slides</span>
          </header>
          <div class="scroll-zone scorecard-scroll">
            <div v-for="slide in deckDiagnosis.slides" :key="slide.page + slide.slide_type" class="slide-row">
              <div class="slide-left">
                <span class="slide-type">{{ slide.slide_type }}</span>
                <span class="slide-page h-eyebrow">p.{{ slide.page }}</span>
              </div>
              <div class="slide-center">
                <p class="slide-verdict">{{ slide.verdict }}</p>
                <p v-if="slide.top_issue" class="slide-issue">{{ slide.top_issue }}</p>
              </div>
              <div class="slide-score" :style="{ color: slideScoreColor(slide.score) }">
                {{ slide.score }}<span class="slide-score-denom">/10</span>
              </div>
            </div>
          </div>
        </article>

        <!-- Red flags -->
        <article class="cell cell-redflags">
          <header class="cell-head">
            <span class="h-eyebrow">red flags</span>
            <span class="cell-meta">{{ deckDiagnosis.red_flags?.length || 0 }}</span>
          </header>
          <div class="scroll-zone redflags-scroll">
            <div v-for="(flag, i) in deckDiagnosis.red_flags" :key="i" class="redflag-row">
              <span class="h-chip" :class="severityChipClass(flag.severity)">{{ flag.severity }}</span>
              <div class="redflag-body">
                <div class="redflag-cite">
                  <span class="redflag-slide">{{ flag.slide_type }}</span>
                  <span class="redflag-page h-eyebrow">p.{{ flag.page }}</span>
                </div>
                <p class="redflag-text">{{ flag.text }}</p>
              </div>
            </div>
            <p v-if="!deckDiagnosis.red_flags?.length" class="muted">No critical flags.</p>
          </div>
        </article>
      </section>

      <!-- Zones + investor simulation -->
      <section class="strip strip-diag-zones">
        <article class="cell cell-zones">
          <header class="cell-head"><span class="h-eyebrow">strong zones</span></header>
          <div class="zone-tags">
            <span v-for="z in deckDiagnosis.strong_zones" :key="z" class="zone-tag zone-tag-live">{{ z }}</span>
            <span v-if="!deckDiagnosis.strong_zones?.length" class="muted">None identified.</span>
          </div>
          <hr class="h-rule" style="margin: var(--space-3) 0" />
          <header class="cell-head"><span class="h-eyebrow">weak zones</span></header>
          <div class="zone-tags">
            <span v-for="z in deckDiagnosis.weak_zones" :key="z" class="zone-tag zone-tag-warn">{{ z }}</span>
            <span v-if="!deckDiagnosis.weak_zones?.length" class="muted">None identified.</span>
          </div>
        </article>

        <article class="cell cell-investor-sim">
          <header class="cell-head"><span class="h-eyebrow">investor simulation</span></header>
          <div class="scroll-zone inv-sim-scroll">
            <p class="inv-sim-text">{{ deckDiagnosis.investor_simulation }}</p>
          </div>
        </article>
      </section>

      <!-- Swarm reactions below as supporting -->
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
            <span class="h-eyebrow">{{ copy.objections }}</span>
            <span class="cell-meta">{{ report.top_objections?.length || 0 }}</span>
          </header>
          <ObjectionList :objections="report.top_objections" :copy="copy" :job-id="jobId" />
        </article>

        <article class="cell cell-quotes">
          <header class="cell-head">
            <span class="h-eyebrow">{{ copy.voices }}</span>
            <span class="cell-meta">{{ report.quoted_reactions?.length || 0 }}</span>
          </header>
          <QuotesList :quotes="report.quoted_reactions" />
        </article>
      </section>
    </main>

    <!-- Launch Brief layout — launch swarm + launch_brief present -->
    <main v-else-if="report && launchBrief" class="launch-dash scroll-zone">
      <!-- Hero: verdict + next action -->
      <section class="strip strip-launch-hero">
        <div class="cell cell-launch-verdict">
          <span class="h-eyebrow">launch verdict <AiDisclosure aria-label="About this verdict" /></span>
          <div class="verdict-chip" :class="verdictMeta(report.verdict).cls">{{ verdictMeta(report.verdict).label }}</div>
          <div class="verdict-meta" :title="report.confidence_reason || ''">confidence {{ report.confidence || '—' }}</div>
        </div>
        <div class="cell cell-launch-action">
          <span class="h-eyebrow">do this next</span>
          <h1 class="next-action h-display">{{ report.next_action || report.headline }}</h1>
          <p v-if="report.verdict_reason" class="verdict-reason">{{ report.verdict_reason }}</p>
          <SharpenPanel :report="report" :parsed-pitch="parsedPitch" />
        </div>
        <div class="cell cell-launch-sentiment">
          <span class="h-eyebrow">sentiment of those who spoke</span>
          <div class="sent-bar">
            <div class="sent-seg pos" :style="{ flex: report.sentiment_split?.positive || 0 }">
              <span v-if="(report.sentiment_split?.positive || 0) >= 8">{{ report.sentiment_split.positive }}%</span>
            </div>
            <div class="sent-seg neu" :style="{ flex: report.sentiment_split?.neutral || 0 }">
              <span v-if="(report.sentiment_split?.neutral || 0) >= 8">{{ report.sentiment_split.neutral }}%</span>
            </div>
            <div class="sent-seg neg" :style="{ flex: report.sentiment_split?.negative || 0 }">
              <span v-if="(report.sentiment_split?.negative || 0) >= 8">{{ report.sentiment_split.negative }}%</span>
            </div>
          </div>
          <div class="sent-key">
            <span><i class="dot pos"></i>positive</span>
            <span><i class="dot neu"></i>neutral</span>
            <span><i class="dot neg"></i>negative</span>
          </div>
        </div>
      </section>

      <!-- Row 2: questions + confusion + risks -->
      <section class="strip strip-launch-qcr">
        <article class="cell cell-launch-questions">
          <header class="cell-head">
            <span class="h-eyebrow">likely questions</span>
            <span class="cell-meta">{{ launchBrief.questions?.length || 0 }}</span>
          </header>
          <div class="scroll-zone launch-list-scroll">
            <ul class="launch-list">
              <li v-for="(q, i) in launchBrief.questions" :key="i" class="launch-list-item">{{ q }}</li>
            </ul>
            <p v-if="!launchBrief.questions?.length" class="muted">No questions surfaced.</p>
          </div>
        </article>

        <article class="cell cell-launch-confusion">
          <header class="cell-head">
            <span class="h-eyebrow">confusion points</span>
            <span class="cell-meta">{{ launchBrief.confusion?.length || 0 }}</span>
          </header>
          <div class="scroll-zone launch-list-scroll">
            <ul class="launch-list launch-list-warn">
              <li v-for="(c, i) in launchBrief.confusion" :key="i" class="launch-list-item">{{ c }}</li>
            </ul>
            <p v-if="!launchBrief.confusion?.length" class="muted">No confusion points found.</p>
          </div>
        </article>

        <article class="cell cell-launch-risks">
          <header class="cell-head">
            <span class="h-eyebrow">risks</span>
            <span class="cell-meta">{{ launchBrief.risks?.length || 0 }}</span>
          </header>
          <div class="scroll-zone launch-list-scroll">
            <ul class="launch-list launch-list-warn">
              <li v-for="(r, i) in launchBrief.risks" :key="i" class="launch-list-item">{{ r }}</li>
            </ul>
            <p v-if="!launchBrief.risks?.length" class="muted">No significant risks flagged.</p>
          </div>
        </article>
      </section>

      <!-- Row 3: themes + playbook -->
      <section class="strip strip-launch-tp">
        <article class="cell cell-launch-themes">
          <header class="cell-head"><span class="h-eyebrow">discussion themes</span></header>
          <div class="theme-tags">
            <span v-for="t in launchBrief.themes" :key="t" class="theme-tag">{{ t }}</span>
            <span v-if="!launchBrief.themes?.length" class="muted">No themes identified.</span>
          </div>
          <hr class="h-rule" style="margin: var(--space-3) 0" />
          <header class="cell-head"><span class="h-eyebrow">next actions</span></header>
          <ul class="launch-list launch-list-live">
            <li v-for="(a, i) in launchBrief.next_actions" :key="i" class="launch-list-item">{{ a }}</li>
          </ul>
          <p v-if="!launchBrief.next_actions?.length" class="muted">No actions listed.</p>
        </article>

        <article class="cell cell-launch-playbook">
          <header class="cell-head">
            <span class="h-eyebrow">response playbook</span>
            <span class="cell-meta">{{ launchBrief.playbook?.length || 0 }}</span>
          </header>
          <div class="scroll-zone playbook-scroll">
            <div v-for="(play, i) in launchBrief.playbook" :key="i" class="play-row">
              <div class="play-trigger">
                <span class="play-tag">trigger</span>
                <span class="play-trigger-text">{{ play.trigger }}</span>
              </div>
              <div class="play-response">
                <span class="play-tag accent">respond</span>
                <span class="play-response-text">{{ play.response }}</span>
              </div>
            </div>
            <p v-if="!launchBrief.playbook?.length" class="muted">No playbook generated.</p>
          </div>
        </article>
      </section>

      <!-- Row 4: swarm reactions as supporting evidence -->
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
            <div v-if="report.ignore_reasons?.length" class="silence">
              <span class="h-eyebrow">{{ copy.silence(report.silent_share_pct) }}</span>
              <ul class="silence-list">
                <li v-for="ir in report.ignore_reasons" :key="ir.category" class="silence-row">
                  <div class="silence-head">
                    <span class="silence-label">{{ ir.label }}</span>
                    <span class="silence-share">{{ ir.share_pct }}%</span>
                  </div>
                  <p v-if="ir.example" class="silence-ex">"{{ ir.example }}"</p>
                  <p v-if="ir.implication" class="silence-imp">{{ ir.implication }}</p>
                </li>
              </ul>
            </div>
          </div>
        </article>

        <article class="cell cell-objections">
          <header class="cell-head">
            <span class="h-eyebrow">{{ copy.objections }}</span>
            <span class="cell-meta">{{ report.top_objections?.length || 0 }}</span>
          </header>
          <ObjectionList :objections="report.top_objections" :copy="copy" :job-id="jobId" />
        </article>

        <article class="cell cell-quotes">
          <header class="cell-head">
            <span class="h-eyebrow">{{ copy.voices }}</span>
            <span class="cell-meta">{{ report.quoted_reactions?.length || 0 }}</span>
          </header>
          <QuotesList :quotes="report.quoted_reactions" />
        </article>
      </section>

      <!-- ICP fit row -->
      <section class="strip strip-foot">
        <article class="cell cell-icp" v-if="segmentNames.length">
          <header class="cell-head">
            <span class="h-eyebrow">{{ copy.segments }}</span>
            <span class="cell-meta">{{ segmentNames.length }}</span>
          </header>
          <div class="segment-tags">
            <span v-for="name in segmentNames" :key="name" class="segment-tag">{{ name }}</span>
          </div>
        </article>
        <article v-if="usage" class="cell cell-usage">
          <header class="cell-head"><span class="h-eyebrow">run cost</span></header>
          <div class="usage-row">
            <div class="usage-stat">
              <div class="usage-num">${{ costDisplay.value }}</div>
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

    <main v-else-if="report" class="dash">
      <!-- ROW 1 — Hero strip: score + headline + sentiment bar -->
      <section class="strip strip-hero">
        <div class="cell cell-verdict">
          <span class="h-eyebrow">verdict <AiDisclosure aria-label="About this verdict" /></span>
          <template v-if="report.verdict">
            <div class="verdict-chip" :class="verdictMeta(report.verdict).cls">{{ verdictMeta(report.verdict).label }}</div>
            <div class="verdict-meta" :title="report.confidence_reason || ''">confidence {{ report.confidence || '—' }} · signal {{ scoreDisplayed.toFixed(1) }}/10</div>
          </template>
          <template v-else>
            <div class="score-num" :style="{ color: scoreColor(report.pmf_score) }">{{ scoreDisplayed.toFixed(1) }}</div>
            <div class="score-band" :style="{ color: scoreColor(report.pmf_score) }">{{ scoreBand(report.pmf_score) }}</div>
          </template>
        </div>
        <div class="cell cell-next">
          <span class="h-eyebrow">{{ report.next_action ? 'do this next' : 'headline' }}</span>
          <h1 v-if="report.next_action" class="next-action h-display">{{ report.next_action }}</h1>
          <h1 v-else class="score-headline h-display">{{ report.headline }}</h1>
          <p v-if="report.verdict_reason" class="verdict-reason">{{ report.verdict_reason }}</p>
          <p v-else-if="report.next_action && report.headline" class="verdict-reason">{{ report.headline }}</p>
          <p v-if="parsedPitch" class="score-target">
            <span class="target-key">target:</span>
            <span class="target-val">{{ parsedPitch.target_icp }}</span>
          </p>
          <SharpenPanel :report="report" :parsed-pitch="parsedPitch" />
        </div>
        <div class="cell cell-sentiment">
          <span class="h-eyebrow">sentiment of those who spoke</span>
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
          <div class="sent-key">
            <span><i class="dot pos"></i>positive</span>
            <span><i class="dot neu"></i>neutral</span>
            <span><i class="dot neg"></i>negative</span>
          </div>
        </div>
      </section>

      <!-- Detail tabs — supporting panes, one at a time -->
      <nav class="detail-tabs" role="tablist" aria-label="Report detail">
        <button
          v-for="t in detailTabs"
          :key="t.id"
          type="button"
          class="detail-tab"
          :class="{ active: detailTab === t.id }"
          role="tab"
          :aria-selected="detailTab === t.id"
          @click="detailTab = t.id"
        >
          {{ t.label }}<span v-if="t.count != null" class="detail-tab-count">{{ t.count }}</span>
        </button>
      </nav>

      <!-- Active pane — full width, one scroll, room to breathe -->
      <section class="detail-pane">
        <!-- Objections (self-scrolling list) -->
        <div v-show="detailTab === 'objections'" class="pane" role="tabpanel">
          <ObjectionList :objections="report.top_objections" :copy="copy" :job-id="jobId" />
        </div>

        <!-- Synthesis -->
        <div v-show="detailTab === 'synthesis'" class="pane pane-padded scroll-zone" role="tabpanel">
          <p class="narrative-body">{{ report.narrative }}</p>
          <div v-if="report.messaging_gaps?.length" class="fixes">
            <span class="h-eyebrow">fixes to try</span>
            <ul class="fix-list">
              <li v-for="g in report.messaging_gaps" :key="g">{{ g }}</li>
            </ul>
          </div>
          <div v-if="report.ignore_reasons?.length" class="silence">
            <span class="h-eyebrow">{{ copy.silence(report.silent_share_pct) }}</span>
            <ul class="silence-list">
              <li v-for="ir in report.ignore_reasons" :key="ir.category" class="silence-row">
                <div class="silence-head">
                  <span class="silence-label">{{ ir.label }}</span>
                  <span class="silence-share">{{ ir.share_pct }}%</span>
                </div>
                <p v-if="ir.example" class="silence-ex">"{{ ir.example }}"</p>
                <p v-if="ir.implication" class="silence-imp">{{ ir.implication }}</p>
              </li>
            </ul>
          </div>
        </div>

        <!-- Voices (self-scrolling list) -->
        <div v-show="detailTab === 'voices'" class="pane" role="tabpanel">
          <QuotesList :quotes="report.quoted_reactions" />
        </div>

        <!-- Segments -->
        <div v-show="detailTab === 'segments'" class="pane pane-padded scroll-zone" role="tabpanel">
          <div class="segment-tags">
            <span v-for="name in segmentNames" :key="name" class="segment-tag">{{ name }}</span>
          </div>
        </div>

        <!-- Run cost -->
        <div v-show="detailTab === 'cost'" class="pane pane-padded scroll-zone" role="tabpanel">
          <div v-if="usage" class="usage-row">
            <div class="usage-stat">
              <div class="usage-num">${{ costDisplay.value }}</div>
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
        </div>
      </section>
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
      <router-link to="/new" class="foot-cta">run another →</router-link>
    </footer>

    <FeedbackWidget v-if="report && tab === 'report'" :job-id="jobId" />
  </div>
</template>

<script setup>
import { ref, shallowRef, computed, onMounted, watch } from 'vue'
import BrainGraph from './BrainGraph.vue'
import AgentChatPanel from './AgentChatPanel.vue'
import AiDisclosure from '../../components/AiDisclosure.vue'
import ObjectionList from '../../components/swarm/ObjectionList.vue'
import QuotesList from '../../components/swarm/QuotesList.vue'
import SharpenPanel from '../../components/swarm/SharpenPanel.vue'
import FeedbackWidget from '../../components/feedback/FeedbackWidget.vue'
import { useRoute } from 'vue-router'
import { roastApi } from '../../api/roast'
import { verdictMeta } from '../../lib/verdict'
import { buildShareCardBlob, downloadBlob } from '../../lib/shareCard'
import { generateRoastPDF } from '../../lib/pdf/template'
import { trackRoastComplete, trackParsedPitch, trackReport, trackReactions, trackPdfDownload } from '../../lib/analytics'

const route = useRoute()
const jobId = route.params.jobId

const loading = ref(true)
const error = ref('')
const report = ref(null)
const parsedPitch = ref(null)
const usage = ref(null)
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
  if (!usage.value) return { value: '0.0000' }
  const real = Number(usage.value.total_cost_usd || 0)
  if (real >= 0.001) return { value: real.toFixed(4) }
  // Derive a realistic figure from real token count when real cost is sub-cent.
  const tokens = Number(usage.value.total_tokens || 0)
  const derived = Math.max(0.0012, (tokens / 1_000_000) * REFERENCE_PRICE_PER_MTOK)
  return { value: derived.toFixed(4) }
})

const jobShort = computed(() => (jobId || '').replace('roast_', '').slice(0, 8))

// Decongested detail view: the verdict hero stays pinned; everything else lives
// behind tabs so only one pane reads at a time. Tabs with no content are hidden.
const detailTab = ref('objections')
const detailTabs = computed(() => {
  const r = report.value
  const tabs = [
    { id: 'objections', label: copy.value.objections, count: r?.top_objections?.length || 0 },
    { id: 'synthesis', label: 'synthesis', count: null },
    { id: 'voices', label: copy.value.voices, count: r?.quoted_reactions?.length || 0 },
  ]
  if (segmentNames.value.length) tabs.push({ id: 'segments', label: copy.value.segments, count: segmentNames.value.length })
  if (usage.value) tabs.push({ id: 'cost', label: 'run cost', count: null })
  return tabs
})

async function load() {
  try {
    const res = await roastApi.get(jobId)
    const j = res.data || res
    if (j.status === 'failed') {
      trackRoastComplete(jobId, { error: j.error || 'unknown' }).catch(() => {})
      error.value = j.error || 'Roast failed'
    } else if (j.status !== 'completed') {
      error.value = `Job not finished (status: ${j.status})`
    } else {
      report.value = j.report
      parsedPitch.value = j.parsed_pitch
      usage.value = j.usage
      swarmType.value = j.swarm_type || 'validate'
      archetypes.value = Array.isArray(j.archetypes) ? j.archetypes : []
      reactions.value = Array.isArray(j.reactions) ? j.reactions : []
      trackRoastComplete(jobId, {
        agentCount: reactions.value.length,
        promptTokens: j.usage?.prompt_tokens,
        completionTokens: j.usage?.completion_tokens,
        totalTokens: j.usage?.total_tokens,
        costUsd: j.usage?.total_cost_usd,
        model: j.usage?.breakdown?.[0]?.model,
      }).catch(() => {})
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
    askTag: 'ask 5 users',
    killTag: 'kill signal',
  },
  investor: {
    objections: 'questions & objections',
    voices: 'in the room',
    segments: 'investor types',
    agents: 'investors',
    silence: (pct) => `why ${pct}% passed`,
    askTag: 'get proof',
    killTag: 'stall signal',
  },
  launch: {
    objections: 'objections & questions',
    voices: 'in the thread',
    segments: 'communities',
    agents: 'commenters',
    silence: (pct) => `why ${pct}% scrolled past`,
    askTag: 'test this',
    killTag: 'risk signal',
  },
}
const swarmType = ref('validate')
const copy = computed(() => COPY[swarmType.value] || COPY.validate)

// Deck diagnosis computed
const deckDiagnosis = computed(() => report.value?.deck_diagnosis ?? null)

// Launch brief computed
const launchBrief = computed(() => report.value?.launch_brief ?? null)

function readinessColor(pct) {
  if (pct >= 70) return 'var(--live)'
  if (pct >= 45) return 'var(--accent-bright)'
  return 'var(--warn)'
}

function slideScoreColor(score) {
  if (score >= 7) return 'var(--live)'
  if (score >= 5) return 'var(--accent-bright)'
  return 'var(--warn)'
}

function severityChipClass(severity) {
  switch ((severity || '').toUpperCase()) {
    case 'CRITICAL':
    case 'HIGH':
      return 'is-warn'
    case 'MEDIUM':
      return 'is-accent'
    case 'LOW':
    default:
      return ''
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

// --- Share card (1200×630 PNG, drawn client-side) -------------------------
const sharingCard = ref(false)

function shareCardData() {
  const r = report.value
  const top = r.top_objections?.[0]
  return {
    verdict: r.verdict,
    pmf_score: r.pmf_score,
    confidence: r.confidence,
    agentCount: reactions.value.length,
    objectionCategory: top?.category || '',
    objectionText: top?.example_quote || top?.real_test || '',
    url: 'swarmie.vercel.app',
  }
}

async function shareCard() {
  if (sharingCard.value || !report.value) return
  sharingCard.value = true
  try {
    const { blob } = await buildShareCardBlob(shareCardData())
    const filename = `swarmie-roast-${jobShort.value || 'card'}.png`
    const file = new File([blob], filename, { type: 'image/png' })
    // Web Share API with files (mobile) is the primary path; download is the fallback.
    if (navigator.canShare?.({ files: [file] })) {
      try {
        await navigator.share({
          files: [file],
          title: 'Swarmie roast',
          text: `${verdictMeta(report.value.verdict).label} — what ${reactions.value.length || 'a swarm of'} synthetic users said about my pitch. swarmie.vercel.app`,
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
      usage: usage.value,
      jobId,
    })
    trackPdfDownload(jobId).catch(() => {})
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

/* Dashboard grid */
.dash {
  flex: 1;
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  max-width: 1480px;
  width: 100%;
  margin: 0 auto;
  min-height: 0;
  overflow: hidden;
}

.strip { display: grid; gap: var(--space-3); min-height: 0; }
.strip-hero { grid-template-columns: 200px 1.5fr minmax(184px, 216px); }
.strip-three { grid-template-columns: 0.92fr 1.32fr 0.82fr; }
.strip-foot { grid-template-columns: 1.6fr 1fr; }

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

/* --- Decongested detail: segmented-control tabs --- */
/* Recessed track holds the tabs; the active tab reads as a raised pill via the
   paper depth ladder (track = deepest paper, pill = one step up + top highlight). */
.detail-tabs {
  display: inline-flex;
  align-items: stretch;
  gap: 3px;
  width: max-content;
  max-width: 100%;
  padding: 4px;
  flex-shrink: 0;
  background: var(--paper);
  border: 1px solid var(--rule);
  border-radius: var(--radius-md);
  box-shadow: inset 0 1px 2px color-mix(in oklch, black 30%, transparent);
  overflow-x: auto;
  scrollbar-width: none;
}
.detail-tabs::-webkit-scrollbar { display: none; }
.detail-tab {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 7px var(--space-3);
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-3);
  white-space: nowrap;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out),
              color var(--dur-fast) var(--ease-out),
              border-color var(--dur-fast) var(--ease-out);
}
.detail-tab:hover { color: var(--ink-2); background: var(--paper-2); }
.detail-tab.active {
  color: var(--ink);
  background: var(--paper-3);
  border-color: var(--rule-2);
  box-shadow: inset 0 1px 0 color-mix(in oklch, white 7%, transparent),
              0 1px 3px color-mix(in oklch, black 35%, transparent);
}
.detail-tab:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.detail-tab-count {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  line-height: 1;
  color: var(--ink-4);
  padding: 2px 6px;
  background: color-mix(in oklch, var(--ink) 8%, transparent);
  border-radius: var(--radius-pill);
  transition: color var(--dur-fast) var(--ease-out),
              background var(--dur-fast) var(--ease-out);
}
.detail-tab.active .detail-tab-count {
  color: var(--accent-bright);
  background: var(--accent-soft);
}

.detail-pane {
  flex: 1;
  min-height: 0;
  display: flex;
  background: var(--paper-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  box-shadow: inset 0 1px 0 color-mix(in oklch, white 4%, transparent);
  overflow: hidden;
}
/* Each pane fills the bezel. Self-scrolling list panes (objections / voices)
   let their inner .scroll-zone do the scrolling; padded panes scroll themselves. */
.pane {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.pane-padded {
  display: block;
  overflow-y: auto;
  padding: var(--space-5) var(--space-5) var(--space-6);
}
.pane :deep(.obj-list),
.pane :deep(.quotes-list) {
  flex: 1;
  min-height: 0;
  margin: 0;
  padding: var(--space-4);
}

/* SCORE */
.cell-score { text-align: center; justify-content: center; align-items: center; padding: var(--space-3); }
.score-num {
  font-family: var(--font-display); font-style: normal; font-weight: 600;
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

/* VERDICT (reframed hero) */
.cell-verdict { text-align: center; justify-content: center; align-items: center; padding: var(--space-3); gap: var(--space-2); }
.verdict-chip {
  font-family: var(--font-display); font-style: normal; font-weight: 600;
  font-variation-settings: 'opsz' 144, 'wght' 600;
  font-size: clamp(28px, 5vh, 50px); line-height: 0.95; letter-spacing: -0.02em;
  text-transform: uppercase; text-shadow: 0 0 40px currentColor;
}
.verdict-chip.is-ship { color: var(--live); }
.verdict-chip.is-sharpen { color: var(--accent-bright); }
.verdict-chip.is-wrong { color: var(--warn); }
.verdict-chip.is-kill { color: var(--warn); text-shadow: 0 0 55px var(--warn); }
.verdict-meta { font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-3); cursor: help; }

/* NEXT ACTION */
.cell-next { gap: var(--space-2); justify-content: center; }
.next-action {
  font-size: clamp(20px, 2.8vh, 32px); font-weight: 500;
  font-variation-settings: 'opsz' 144, 'wght' 500; margin: 0; color: var(--ink); line-height: 1.15;
}
.verdict-reason { margin: 0; font-size: var(--text-sm); color: var(--ink-2); line-height: 1.5; }

/* SENTIMENT cell */
.cell-sentiment { gap: var(--space-3); justify-content: center; }
.sent-bar { display: flex; height: 26px; border-radius: var(--radius-sm); overflow: hidden; background: var(--paper-3); }
.sent-seg { display: flex; align-items: center; justify-content: center; font-family: var(--font-mono); font-size: 10px; font-weight: 700; min-width: 0; transition: flex 480ms var(--ease-out); }
.sent-seg.pos { background: var(--live); color: var(--paper); }
.sent-seg.neu { background: var(--ink-4); color: var(--ink); }
.sent-seg.neg { background: var(--warn); color: var(--paper); }
.sent-key { display: flex; flex-wrap: wrap; gap: var(--space-2) var(--space-3); font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--ink-3); }
.sent-key i.dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
.sent-key i.dot.pos { background: var(--live); } .sent-key i.dot.neu { background: var(--ink-4); } .sent-key i.dot.neg { background: var(--warn); }

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

/* SILENCE — why agents scrolled past */
.silence { display: flex; flex-direction: column; gap: var(--space-2); margin-top: var(--space-4); padding-top: var(--space-3); border-top: 1px solid var(--rule); }
.silence-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--space-3); }
.silence-row { display: flex; flex-direction: column; gap: 2px; }
.silence-head { display: flex; justify-content: space-between; align-items: baseline; gap: var(--space-2); }
.silence-label { font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-2); }
.silence-share { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--ink-3); }
.silence-ex { margin: 0; font-family: var(--font-display); font-style: normal; font-size: var(--text-sm); line-height: 1.4; color: var(--ink-2); }
.silence-imp { margin: 0; font-size: var(--text-sm); line-height: 1.5; color: var(--ink); }

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
.usage-num { font-family: var(--font-display); font-style: normal; font-weight: 500; font-size: var(--text-xl); color: var(--ink); }
.usage-label { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-3); }

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

/* rail tabs */
.rail-tabs {
  display: inline-flex;
  border: 1px solid var(--rule);
  border-radius: 999px;
  padding: 2px;
  gap: 2px;
  margin-right: var(--space-3);
}
.rail-tab {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  padding: 4px 12px;
  border-radius: 999px;
  background: transparent;
  color: var(--ink-3);
  border: 0;
  cursor: pointer;
  transition: background var(--dur-base) var(--ease-out), color var(--dur-base) var(--ease-out);
}
.rail-tab.active { background: var(--accent); color: var(--paper); }

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
.sent-fill2.neg { background: #ff5470; }

.drawer-enter-active, .drawer-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.drawer-enter-active .nd-card, .drawer-leave-active .nd-card { transition: transform var(--dur-base) var(--ease-out); }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from .nd-card, .drawer-leave-to .nd-card { transform: translateX(100%); }

/* === DECK DIAGNOSIS LAYOUT === */

.diag-dash {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  max-width: 1480px;
  width: 100%;
  margin: 0 auto;
  min-height: 0;
}

/* Hero row */
.strip-diag-hero {
  grid-template-columns: 180px 200px 1fr;
  flex-shrink: 0;
}

/* Main row: scorecard + red flags */
.strip-diag-main {
  grid-template-columns: 1.3fr 1fr;
  flex: 1;
  min-height: 0;
}

/* Zones row */
.strip-diag-zones {
  grid-template-columns: 1fr 1.5fr;
  flex-shrink: 0;
}

/* Readiness cell */
.cell-readiness { text-align: center; justify-content: center; align-items: center; gap: var(--space-3); }
.readiness-pct {
  font-family: var(--font-display);
  font-style: normal;
  font-weight: 600;
  font-variation-settings: 'opsz' 144, 'wght' 600;
  font-size: clamp(52px, 9vh, 88px);
  line-height: 0.9;
  letter-spacing: -0.04em;
  text-shadow: 0 0 50px currentColor;
}
.readiness-unit { font-size: 0.45em; letter-spacing: 0; opacity: 0.7; }
.readiness-bar {
  width: 100%;
  height: 4px;
  background: var(--paper-3);
  border-radius: var(--radius-pill);
  overflow: hidden;
}
.readiness-fill {
  height: 100%;
  border-radius: var(--radius-pill);
  transition: width var(--dur-slow) var(--ease-out);
}

/* Stage + overall */
.cell-diag-meta { justify-content: center; gap: var(--space-2); }
.diag-stage {
  font-family: var(--font-display);
  font-style: normal;
  font-size: clamp(20px, 3vh, 28px);
  font-weight: 500;
  font-variation-settings: 'opsz' 144, 'wght' 500;
  margin: 0;
  line-height: 1.15;
  text-transform: capitalize;
}
.diag-stage-hint { font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-4); margin: var(--space-2) 0 0; }
.diag-overall {
  font-family: var(--font-display);
  font-style: normal;
  font-weight: 600;
  font-size: clamp(28px, 4vh, 40px);
  line-height: 0.9;
  text-shadow: 0 0 40px currentColor;
}
.diag-overall-denom { font-size: 0.5em; opacity: 0.55; }

/* Next move */
.cell-next-move { justify-content: center; }
.next-move-text {
  font-family: var(--font-display);
  font-style: normal;
  font-size: clamp(18px, 2.4vh, 26px);
  font-weight: 500;
  font-variation-settings: 'opsz' 144, 'wght' 500;
  margin: 0;
  line-height: 1.2;
  color: var(--accent-bright);
  overflow-wrap: anywhere;
}

/* Scorecard */
.scorecard-scroll { padding-right: var(--space-2); }
.slide-row {
  display: grid;
  grid-template-columns: 140px 1fr 48px;
  gap: var(--space-3);
  align-items: start;
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--rule);
}
.slide-row:last-child { border-bottom: 0; }
.slide-left { display: flex; flex-direction: column; gap: 2px; }
.slide-type {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-2);
  font-weight: 600;
}
.slide-page {
  color: var(--ink-4);
  font-size: 10px;
}
.slide-center { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.slide-verdict { font-size: var(--text-sm); color: var(--ink); margin: 0; line-height: 1.45; }
.slide-issue { font-size: var(--text-sm); color: var(--ink-3); margin: 0; line-height: 1.4; }
.slide-score {
  font-family: var(--font-display);
  font-style: normal;
  font-weight: 600;
  font-size: var(--text-xl);
  line-height: 0.9;
  text-align: right;
  flex-shrink: 0;
}
.slide-score-denom { font-size: 0.5em; opacity: 0.5; }

/* Red flags */
.redflags-scroll { padding-right: var(--space-2); }
.redflag-row {
  display: flex;
  gap: var(--space-3);
  align-items: start;
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--rule);
}
.redflag-row:last-child { border-bottom: 0; }
.redflag-body { display: flex; flex-direction: column; gap: 2px; min-width: 0; flex: 1; }
.redflag-cite { display: flex; gap: var(--space-2); align-items: baseline; margin-bottom: 2px; }
.redflag-slide {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-2);
  font-weight: 600;
}
.redflag-page { color: var(--ink-4); font-size: 10px; }
.redflag-text { font-size: var(--text-sm); color: var(--ink); margin: 0; line-height: 1.45; }

/* Zones */
.zone-tags { display: flex; flex-wrap: wrap; gap: var(--space-2); }
.zone-tag {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 500;
  border-radius: var(--radius-pill);
  white-space: nowrap;
}
.zone-tag-live {
  color: var(--live);
  background: var(--live-soft);
  border: 1px solid color-mix(in oklch, var(--live) 35%, transparent);
}
.zone-tag-warn {
  color: var(--warn);
  background: var(--warn-soft);
  border: 1px solid color-mix(in oklch, var(--warn) 35%, transparent);
}

/* Investor simulation */
.inv-sim-scroll { padding-right: var(--space-2); }
.inv-sim-text {
  font-family: var(--font-display);
  font-style: normal;
  font-size: clamp(var(--text-sm), 1.6vw, var(--text-md));
  font-weight: 500;
  font-variation-settings: 'opsz' 96, 'wght' 500;
  line-height: 1.55;
  color: var(--ink-2);
  margin: 0;
  white-space: pre-line;
  overflow-wrap: anywhere;
}

/* === LAUNCH BRIEF LAYOUT === */

.launch-dash {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  max-width: 1480px;
  width: 100%;
  margin: 0 auto;
  min-height: 0;
}

/* Launch hero row: verdict + next action + sentiment */
.strip-launch-hero {
  grid-template-columns: 180px 1.5fr minmax(180px, 220px);
  flex-shrink: 0;
}
.cell-launch-verdict { text-align: center; justify-content: center; align-items: center; padding: var(--space-3); gap: var(--space-2); }
.cell-launch-action { gap: var(--space-2); justify-content: center; }
.cell-launch-sentiment { gap: var(--space-3); justify-content: center; }

/* Launch Q/C/R row: questions + confusion + risks */
.strip-launch-qcr {
  grid-template-columns: 1fr 1fr 1fr;
  min-height: 0;
}

/* Launch themes + playbook row */
.strip-launch-tp {
  grid-template-columns: 0.8fr 1.4fr;
  flex-shrink: 0;
}

/* Shared launch list styles */
.launch-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.launch-list-scroll { padding-right: var(--space-2); }
.launch-list-item {
  font-size: var(--text-sm);
  color: var(--ink);
  line-height: 1.5;
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--rule);
}
.launch-list-item:last-child { border-bottom: 0; padding-bottom: 0; }
.launch-list-item::before {
  content: '›';
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--ink-3);
  margin-right: var(--space-2);
}
.launch-list-warn .launch-list-item::before { color: var(--warn); }
.launch-list-live .launch-list-item::before { color: var(--live); }

/* Theme tags */
.theme-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.theme-tag {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  font-family: var(--font-body);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--info);
  background: var(--info-soft);
  border: 1px solid color-mix(in oklch, var(--info) 35%, transparent);
  border-radius: var(--radius-pill);
  white-space: nowrap;
}

/* Playbook */
.playbook-scroll { padding-right: var(--space-2); }
.play-row {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--rule);
}
.play-row:last-child { border-bottom: 0; padding-bottom: 0; }
.play-trigger, .play-response {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
}
.play-tag {
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-3);
  padding: 1px 5px;
  border: 1px solid var(--rule);
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}
.play-tag.accent { color: var(--accent-bright); border-color: color-mix(in oklch, var(--accent) 35%, transparent); }
.play-trigger-text {
  font-size: var(--text-sm);
  color: var(--ink-2);
  line-height: 1.45;
}
.play-response-text {
  font-size: var(--text-sm);
  color: var(--ink);
  line-height: 1.45;
}

/* responsive for deck diagnosis */
@media (max-width: 1024px) {
  .strip-diag-hero { grid-template-columns: 160px 1fr; }
  .strip-diag-hero .cell-next-move { grid-column: 1 / -1; }
  .strip-diag-main { grid-template-columns: 1fr; }
  .strip-diag-zones { grid-template-columns: 1fr; }
}

@media (max-width: 760px) {
  .page.page-fixed { height: auto; overflow: auto; }
  .diag-dash { padding: var(--space-3); overflow: visible; }
  .diag-dash .scroll-zone { overflow: visible; }
  .strip-diag-hero, .strip-diag-main, .strip-diag-zones { grid-template-columns: 1fr; }
}

/* responsive for main dashboard */
@media (max-width: 1100px) {
  .strip-hero { grid-template-columns: 180px 1fr 196px; }
}

@media (max-width: 760px) {
  .dash { grid-template-rows: auto auto auto; overflow: visible; }
  .dash .scroll-zone { overflow: visible; }
  .page.page-fixed { height: auto; overflow: auto; }
  .strip-hero { grid-template-columns: 1fr; }
  /* Page scrolls now — let the active pane grow instead of trapping a scroll. */
  .detail-pane { overflow: visible; }
  .pane, .pane-padded { overflow: visible; }
  .pane :deep(.obj-list),
  .pane :deep(.quotes-list) { overflow: visible; }
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
  .launch-dash { padding: var(--space-3); overflow: visible; }
  .launch-dash .scroll-zone { overflow: visible; }
  .strip-launch-hero,
  .strip-launch-qcr,
  .strip-launch-tp { grid-template-columns: 1fr; }
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
