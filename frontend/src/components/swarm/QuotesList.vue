<template>
  <div class="quotes-list">
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
.quotes-list { display: grid; }
.quote {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  grid-template-areas: "handle text" "meta text";
  column-gap: var(--space-5);
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--rule);
}
.q-handle { grid-area: handle; font-size: var(--text-sm); font-weight: 600; color: var(--ink); overflow-wrap: anywhere; }
.q-text {
  grid-area: text;
  margin: 0;
  font-family: var(--font-display);
  font-size: var(--text-md);
  line-height: 1.5;
  color: var(--ink-2);
  max-width: 64ch;
}
.q-meta { grid-area: meta; display: flex; flex-wrap: wrap; gap: 0 var(--space-2); font-size: var(--text-sm); color: var(--ink-3); }
.q-tone::first-letter { text-transform: uppercase; }
.quote.tone-skeptical .q-tone, .quote.tone-aggressive .q-tone { color: var(--warn); }
.quote.tone-enthusiastic .q-tone { color: var(--live); }
.muted { color: var(--ink-3); font-size: var(--text-sm); margin: 0; }

@media (max-width: 767px) {
  .quote { grid-template-columns: minmax(0, 1fr); grid-template-areas: "handle" "text" "meta"; row-gap: var(--space-1); }
}
</style>
