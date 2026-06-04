<template>
  <router-view />
  <ConsentBanner />
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import ConsentBanner from './components/ConsentBanner.vue'
import { startSmoothScroll, stopSmoothScroll } from './lib/smoothScroll'

onMounted(() => startSmoothScroll())
onBeforeUnmount(() => stopSmoothScroll())
</script>

<style>
/* Global app shell. Token system lives in src/styles/tokens.css. */

#app {
  min-height: 100vh;
  background: var(--paper);
  color: var(--ink);
  font-family: var(--font-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

button {
  font-family: inherit;
}

/* Scrollbar — themed to dark */
::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}
::-webkit-scrollbar-track {
  background: var(--paper-2);
}
::-webkit-scrollbar-thumb {
  background: var(--paper-4);
  border-radius: 999px;
  border: 2px solid var(--paper-2);
}
::-webkit-scrollbar-thumb:hover {
  background: var(--rule-2);
}
</style>
