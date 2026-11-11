<template>
  <div class="x-rows">
    <section v-if="b.questions?.length || b.confusion?.length || b.risks?.length" class="x-row" aria-label="What the thread will raise">
      <div v-if="b.questions?.length" class="x-cell">
        <h2>Questions you'll get</h2>
        <ul class="ticks"><li v-for="(q, i) in b.questions" :key="i">{{ q }}</li></ul>
      </div>
      <div v-if="b.confusion?.length" class="x-cell">
        <h2>Where readers get confused</h2>
        <ul class="ticks bad"><li v-for="(c, i) in b.confusion" :key="i">{{ c }}</li></ul>
      </div>
      <div v-if="b.risks?.length" class="x-cell">
        <h2>Launch risks</h2>
        <ul class="ticks bad"><li v-for="(r, i) in b.risks" :key="i">{{ r }}</li></ul>
      </div>
    </section>

    <section v-if="b.playbook?.length || b.next_actions?.length || b.themes?.length" class="x-row">
      <div v-if="b.playbook?.length" class="x-cell x-wide">
        <h2>Reply playbook</h2>
        <dl class="plays">
          <div v-for="(p, i) in b.playbook" :key="i" class="play">
            <dt>If someone says: <span>{{ p.trigger }}</span></dt>
            <dd>{{ p.response }}</dd>
          </div>
        </dl>
      </div>
      <div v-if="b.next_actions?.length || b.themes?.length" class="x-cell">
        <template v-if="b.next_actions?.length">
          <h2>Before you post</h2>
          <ul class="ticks good"><li v-for="(a, i) in b.next_actions" :key="i">{{ a }}</li></ul>
        </template>
        <template v-if="b.themes?.length">
          <h2 :class="{ 'h-gap': b.next_actions?.length }">What the thread will talk about</h2>
          <ul class="themes"><li v-for="t in b.themes" :key="t">{{ t }}</li></ul>
        </template>
      </div>
    </section>
  </div>
</template>

<script setup>
defineProps({ b: { type: Object, required: true } })
</script>

<style scoped>
/* Extra memo rows: same hairline ledger as DecisionMemo's board. */
.x-rows { grid-column: 1 / -1; display: grid; gap: 1px; }
.x-row { display: flex; flex-wrap: wrap; gap: 1px; }
.x-cell { flex: 1 1 260px; margin: 0; min-width: 0; background: var(--paper); padding: var(--space-6); }
.x-wide { flex: 2 1 440px; }
h2 { margin: 0 0 var(--space-4); font-size: var(--text-base); font-weight: 700; }
.h-gap { margin-top: var(--space-6); }

.ticks { margin: 0; padding-left: 1.1em; display: grid; gap: var(--space-3); font-size: var(--text-sm); line-height: 1.5; color: var(--ink-2); }
.ticks.good li::marker { color: var(--live); }
.ticks.bad li::marker { color: var(--warn); }

.plays { margin: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: var(--space-5) var(--space-6); }
.play dt { font-size: var(--text-sm); font-weight: 600; color: var(--ink-3); line-height: 1.45; }
.play dt span { color: var(--ink); font-weight: 600; }
.play dd { margin: var(--space-2) 0 0; font-size: var(--text-sm); line-height: 1.5; color: var(--ink-2); }

.themes { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: var(--space-2); }
.themes li { font-size: var(--text-sm); padding: 0.2em 0.6em; border: 1px solid var(--rule-2); border-radius: 999px; color: var(--ink-2); }

@media (max-width: 767px) { .x-cell { padding: var(--space-5) var(--space-4); } }
</style>
