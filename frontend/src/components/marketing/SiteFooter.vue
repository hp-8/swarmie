<template>
  <footer class="foot">
    <span class="brand-mark">Swarmie</span>
    <span class="foot-meta">v2 · AGPL-3.0 · open source · reviewers are synthetic, always disclosed</span>
    <nav class="foot-links" aria-label="Footer">
      <router-link to="/terms">Terms</router-link>
      <router-link to="/privacy">Privacy</router-link>
      <a href="#" @click.prevent="openConsentSettings">Cookie settings</a>
    </nav>
  </footer>
</template>

<script setup>
import { openConsentSettings } from '../../lib/consent'
</script>

<style scoped>
.foot { max-width: 1320px; margin: 0 auto; padding: var(--space-6); border-top: 1px solid var(--rule); display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3) var(--space-6); font-size: var(--text-sm); color: var(--ink-3); }
.brand-mark { font-size: var(--text-md); font-weight: 700; color: var(--ink); }
.foot-links { margin-left: auto; display: flex; flex-wrap: wrap; gap: var(--space-5); }
.foot-links a { color: var(--ink-2); }
.foot-links a:hover { color: var(--ink); text-decoration: underline; text-underline-offset: 3px; }
@media (max-width: 767px) {
  .foot { padding-inline: var(--space-4); }
  .foot-links { margin-left: 0; }
}
</style>
