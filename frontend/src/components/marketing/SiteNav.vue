<template>
  <header class="nav">
    <router-link to="/" class="brand-mark">Swarmie</router-link>
    <nav class="nav-links" aria-label="Primary">
      <router-link :to="{ path: '/', hash: '#memo' }" class="nav-link">Sample memo</router-link>
      <router-link to="/roasts" class="nav-link">Archive</router-link>
      <router-link :to="{ path: '/', hash: '#pricing' }" class="nav-link">Pricing</router-link>
      <a href="https://github.com/hp-8/swarmie" target="_blank" rel="noopener" class="nav-link">GitHub</a>
      <router-link to="/new" class="nav-cta">Submit a pitch</router-link>
    </nav>
  </header>
</template>

<style scoped>
.nav {
  position: sticky; top: 0; z-index: 30;
  display: flex; align-items: center; justify-content: space-between; gap: var(--space-4);
  padding: var(--space-3) var(--space-6);
  background: oklch(100% 0 0 / 0.94);
  border-bottom: 1px solid var(--rule);
}
.brand-mark { font-size: var(--text-md); font-weight: 700; letter-spacing: -0.01em; }
.nav-links { display: flex; align-items: center; gap: var(--space-5); }
.nav-link { font-size: var(--text-sm); color: var(--ink-2); }
.nav-link:hover { color: var(--ink); text-decoration: underline; text-underline-offset: 3px; }
.nav-cta {
  font-size: var(--text-sm); font-weight: 700; white-space: nowrap;
  padding: 8px 14px; border-radius: var(--radius-sm);
  background: var(--ink); color: var(--paper);
  transition: background var(--dur-fast) var(--ease-out);
}
.nav-cta:hover { background: var(--ink-2); }
@media (max-width: 767px) {
  .nav { padding: var(--space-3) var(--space-4); }
  .nav-link { display: none; }
}
</style>
