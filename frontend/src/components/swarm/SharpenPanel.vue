<template>
  <div class="sharpen">
    <button class="h-btn is-accent sharpen-trigger" type="button" @click="open">
      Sharpen this →
    </button>

    <transition name="sharpen-fade">
      <div v-if="visible" class="sharpen-overlay" @click.self="visible = false">
        <div class="sharpen-card" role="dialog" aria-label="Sharpen plan">
          <header class="sharpen-head">
            <span class="h-eyebrow">sharpen <AiDisclosure aria-label="How this plan was generated" /></span>
            <button class="sharpen-close" type="button" @click="visible = false" aria-label="Close">×</button>
          </header>

          <!-- Signup gate (after the first free sharpen) -->
          <div v-if="gated" class="sharpen-gate">
            <h2 class="sharpen-gate-title h-display">One more sharpen.</h2>
            <p class="sharpen-gate-copy">
              Your first sharpen was on the house. Drop an email to keep turning
              verdicts into moves — and to save them.
            </p>
            <form class="sharpen-gate-form" @submit.prevent="unlock">
              <input
                v-model="email"
                type="email"
                required
                class="sharpen-input"
                placeholder="you@founder.com"
                autocomplete="email"
              />
              <button class="h-btn is-accent" type="submit">Unlock</button>
            </form>
            <p class="sharpen-gate-fine">No spam. Used to save your roasts and sharpens.</p>
          </div>

          <!-- The plan -->
          <div v-else class="sharpen-plan">
            <section class="sharpen-block">
              <span class="h-eyebrow">sharper positioning</span>
              <p class="sharpen-positioning">{{ plan.positioning }}</p>
            </section>

            <section class="sharpen-block">
              <span class="h-eyebrow">fix these, in order</span>
              <ol class="sharpen-fixes">
                <li v-for="(fix, i) in plan.fixes" :key="i" class="sharpen-fix">
                  <span class="sharpen-fix-num">{{ i + 1 }}</span>
                  <span class="sharpen-fix-text">{{ fix }}</span>
                </li>
              </ol>
            </section>

            <section class="sharpen-block">
              <span class="h-eyebrow">re-roast draft</span>
              <p class="sharpen-draft">{{ plan.draft }}</p>
            </section>

            <footer class="sharpen-foot">
              <router-link to="/new" class="h-btn is-accent">Re-roast the sharpened pitch →</router-link>
              <span class="sharpen-foot-note">See the verdict move.</span>
            </footer>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import AiDisclosure from '../AiDisclosure.vue'

const props = defineProps({
  report: { type: Object, default: () => ({}) },
  parsedPitch: { type: Object, default: null },
})

// --- Signup gate (frontend stub) ---
// First sharpen is free; after that, an email unlocks it. Persisted locally
// until a real auth backend lands.
const USED_KEY = 'swarmie_sharpen_used'
const USER_KEY = 'swarmie_user_email'

const visible = ref(false)
const gated = ref(false)
const email = ref('')

const signedUp = () => !!localStorage.getItem(USER_KEY)
const usedFree = () => localStorage.getItem(USED_KEY) === '1'

function open() {
  if (signedUp() || !usedFree()) {
    localStorage.setItem(USED_KEY, '1')
    gated.value = false
  } else {
    gated.value = true
  }
  visible.value = true
}

function unlock() {
  if (!email.value) return
  localStorage.setItem(USER_KEY, email.value)
  gated.value = false
  // TODO(backend): POST email -> create account / mailing list.
}

// --- Plan (mocked, seeded from the real report so it reads live) ---
// TODO(backend): replace with POST /roast/:jobId/sharpen.
const topObjection = computed(() => {
  const o = props.report?.top_objections?.[0]
  if (!o) return null
  return typeof o === 'string' ? o : (o.text || o.objection || o.label || null)
})

const gaps = computed(() => {
  const g = props.report?.messaging_gaps
  return Array.isArray(g) ? g.filter(Boolean) : []
})

const plan = computed(() => {
  const obj = topObjection.value
  const oneLiner = props.parsedPitch?.one_liner || props.parsedPitch?.solution || 'your pitch'

  const fixes = []
  if (obj) fixes.push(`Lead with the answer to the loudest objection: “${obj}”. Put it above the fold, not in an FAQ.`)
  for (const g of gaps.value.slice(0, 2)) fixes.push(`Close the gap: ${g}`)
  if (props.report?.next_action) fixes.push(props.report.next_action)
  while (fixes.length < 3) {
    fixes.push('Name the specific buyer in the first line — vague ICP is why the silent ones scrolled past.')
  }

  return {
    positioning: obj
      ? `Reframe so the first sentence kills “${obj}”. Same product — but the buyer hears the answer before the doubt.`
      : `Tighten ${oneLiner} to one sentence a skeptic can’t argue with.`,
    fixes: fixes.slice(0, 3),
    draft: `${oneLiner} — now rewritten to front-load the proof the swarm asked for, and to speak to one buyer instead of everyone. Paste this back into a new roast and watch the verdict shift.`,
  }
})
</script>

<style scoped>
.sharpen { display: inline-block; }
.sharpen-trigger { margin-top: var(--space-3); }

.sharpen-overlay {
  position: fixed; inset: 0; z-index: 300;
  display: flex; align-items: center; justify-content: center;
  padding: var(--space-4);
  background: color-mix(in oklch, black 60%, transparent);
  backdrop-filter: blur(4px);
}
.sharpen-card {
  width: min(560px, 100%); max-height: 88vh; overflow-y: auto;
  background: var(--paper-2); border: 1px solid var(--rule-2);
  border-radius: var(--radius-lg); padding: var(--space-5);
  box-shadow: 0 24px 60px color-mix(in oklch, black 55%, transparent);
}
.sharpen-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-4); }
.sharpen-close {
  background: none; border: none; color: var(--ink-3); font-size: 1.5rem;
  line-height: 1; cursor: pointer; padding: 0 4px;
}
.sharpen-close:hover { color: var(--ink); }

.sharpen-block { margin-bottom: var(--space-4); }
.sharpen-positioning { margin: 6px 0 0; font-family: var(--font-body); font-size: var(--text-md); line-height: 1.55; color: var(--ink); }
.sharpen-draft { margin: 6px 0 0; font-family: var(--font-body); font-size: var(--text-sm); line-height: 1.6; color: var(--ink-2); }

.sharpen-fixes { list-style: none; margin: 8px 0 0; padding: 0; display: flex; flex-direction: column; gap: var(--space-3); }
.sharpen-fix { display: flex; gap: var(--space-3); align-items: baseline; }
.sharpen-fix-num {
  flex-shrink: 0; width: 22px; height: 22px; display: grid; place-items: center;
  border: 1px solid var(--accent); border-radius: 999px;
  font-family: var(--font-mono); font-size: var(--text-xs); color: var(--accent-bright);
}
.sharpen-fix-text { font-family: var(--font-body); font-size: var(--text-sm); line-height: 1.5; color: var(--ink-2); }

.sharpen-foot { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3); margin-top: var(--space-5); padding-top: var(--space-4); border-top: 1px solid var(--rule); }
.sharpen-foot-note { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--ink-3); }

/* Gate */
.sharpen-gate-title { margin: 0 0 var(--space-2); font-size: var(--text-2xl); }
.sharpen-gate-copy { margin: 0 0 var(--space-4); font-family: var(--font-body); font-size: var(--text-sm); line-height: 1.55; color: var(--ink-2); }
.sharpen-gate-form { display: flex; gap: var(--space-2); }
.sharpen-input {
  flex: 1; min-width: 0; padding: 10px 14px;
  background: var(--paper); border: 1px solid var(--rule-2); border-radius: var(--radius-md);
  color: var(--ink); font-family: var(--font-body); font-size: var(--text-sm);
}
.sharpen-input:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.sharpen-gate-fine { margin: var(--space-3) 0 0; font-family: var(--font-mono); font-size: var(--text-xs); color: var(--ink-4); }

.sharpen-fade-enter-active, .sharpen-fade-leave-active { transition: opacity var(--dur-base) var(--ease-out); }
.sharpen-fade-enter-from, .sharpen-fade-leave-to { opacity: 0; }

@media (max-width: 540px) {
  .sharpen-gate-form { flex-direction: column; }
  .sharpen-foot { flex-direction: column; align-items: stretch; }
}
@media (prefers-reduced-motion: reduce) {
  .sharpen-fade-enter-active, .sharpen-fade-leave-active { transition: none; }
}
</style>
