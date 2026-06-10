<template>
  <div class="quotes-list scroll-zone">
    <article v-for="q in quotes" :key="q.agent_id" class="quote" :class="'tone-' + q.tone">
      <div class="q-handle">@{{ q.name }}</div>
      <p class="q-text">{{ q.text }}</p>
      <div class="q-meta">
        <span class="q-tone">{{ q.tone }}</span>
        <span class="q-seg">{{ q.segment }}</span>
      </div>
    </article>
    <p v-if="!quotes?.length" class="muted">No standout reactions.</p>
  </div>
</template>

<script setup>
defineProps({ quotes: { type: Array, default: () => [] } })
</script>

<style scoped>
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
  font-family: var(--font-display); font-style: normal; font-weight: 500;
  font-size: var(--text-sm); line-height: 1.45; color: var(--ink); margin: 0 0 var(--space-2);
}
.q-meta { display: flex; justify-content: space-between; font-family: var(--font-mono); font-size: 10px; color: var(--ink-3); }
.q-tone { text-transform: uppercase; letter-spacing: 0.08em; }
.muted { color: var(--ink-3); font-size: var(--text-sm); margin: 0; }
</style>
