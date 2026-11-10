<template>
  <div class="page roasts">
    <SiteNav />

    <main class="archive">
      <section class="archive-head">
        <h1 class="archive-title">The memo archive</h1>
        <div class="archive-intro">
          <p class="lede">
            Famous pitches, as they were actually told, put through the same panel you get. Hindsight
            makes everyone a genius; the interesting part is which objection the panel raises first.
          </p>
          <p class="fine">
            Real runs from {{ runDate }}, {{ roasts.length }} pitches, 100 synthetic reviewers each.
            Recommendations and quotes are unedited panel output.
          </p>
        </div>
      </section>

      <section class="archive-grid" aria-label="Archived memos">
        <MemoArchiveCard
          v-for="(r, i) in roasts"
          :key="r.slug"
          :memo="r"
          :featured="i === 0"
        />
      </section>

      <section class="archive-close">
        <h2 class="close-title">Your pitch, through the same panel.</h2>
        <router-link to="/new" class="close-btn">Submit a pitch</router-link>
      </section>
    </main>

    <SiteFooter />
  </div>
</template>

<script setup>
import SiteNav from '../components/marketing/SiteNav.vue'
import SiteFooter from '../components/marketing/SiteFooter.vue'
import MemoArchiveCard from '../components/marketing/MemoArchiveCard.vue'
import data from '../data/famousRoasts.json'

const roasts = data.roasts
const runDate = new Date(`${data.run_date}T00:00:00`).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
</script>

<style scoped>
.page { min-height: 100vh; color: var(--ink); background: var(--paper-2); }
.archive { max-width: 1320px; margin: 0 auto; padding: var(--space-9) var(--space-6) var(--space-8); }

.archive-head { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr); gap: var(--space-8); align-items: end; padding-bottom: var(--space-7); border-bottom: 2px solid var(--ink); }
.archive-title { margin: 0; font-family: var(--font-display); font-weight: 600; font-size: clamp(44px, 5.6vw, 80px); line-height: 1; letter-spacing: -0.025em; text-wrap: balance; }
.lede { margin: 0; font-family: var(--font-display); font-size: var(--text-lg); line-height: 1.55; color: var(--ink-2); max-width: 58ch; }
.fine { margin: var(--space-3) 0 0; font-size: var(--text-sm); color: var(--ink-3); }

.archive-grid { margin-top: var(--space-7); display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-5); }
.archive-grid > :first-child { grid-column: 1 / -1; }

.archive-close { margin-top: var(--space-9); display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: var(--space-5); }
.close-title { margin: 0; font-family: var(--font-display); font-weight: 600; font-size: clamp(28px, 3vw, 40px); letter-spacing: -0.02em; }
.close-btn { font-weight: 700; padding: 13px 20px; border-radius: var(--radius-sm); background: var(--ink); color: var(--paper); transition: background var(--dur-fast) var(--ease-out); }
.close-btn:hover { background: var(--ink-2); }

@media (max-width: 1024px) {
  .archive-head { grid-template-columns: minmax(0, 1fr); gap: var(--space-4); }
}
@media (max-width: 767px) {
  .archive { padding: var(--space-7) var(--space-4) var(--space-7); }
  .archive-grid { grid-template-columns: minmax(0, 1fr); }
}
</style>
