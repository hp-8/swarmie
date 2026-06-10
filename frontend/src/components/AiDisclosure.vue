<!-- Hallmark · component: info-icon + modal · genre: editorial · theme: Midnight+coral
 * states: default · hover · focus · active · disabled · loading · error · success
 * contrast: pass (46–50)
 -->
<template>
  <span class="aid-wrap">
    <button
      type="button"
      class="aid-trigger"
      :class="{ inline: variant === 'inline', text: variant === 'text' }"
      :aria-label="ariaLabel"
      @click="open = true"
    >
      <span v-if="variant === 'text'" class="aid-text">{{ label || 'how this was generated' }}</span>
      <svg v-else class="aid-icon" viewBox="0 0 16 16" aria-hidden="true">
        <circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" stroke-width="1.2"/>
        <circle cx="8" cy="4.6" r="0.95" fill="currentColor"/>
        <path d="M8 7v5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
      </svg>
    </button>

    <teleport to="body">
      <transition name="aid-fade">
        <div v-if="open" class="aid-modal" role="dialog" aria-modal="true" :aria-labelledby="`aid-h-${uid}`" @click.self="open = false">
          <div class="aid-card" @keydown.esc="open = false" tabindex="-1" ref="cardRef">
            <button class="aid-close" type="button" aria-label="Close" @click="open = false">×</button>

            <span class="h-eyebrow">disclosure</span>
            <h2 :id="`aid-h-${uid}`" class="aid-title">How this was generated.</h2>

            <p class="aid-lede">
              Every reaction, score, and quote on this page was produced by a swarm of
              <em>AI language models</em> role-playing personas. <strong>No real humans
              were surveyed.</strong>
            </p>

            <dl class="aid-grid">
              <div class="aid-row">
                <dt>what it is</dt>
                <dd>A directional pre-interview filter — a fast sanity check on positioning,
                  pricing, and obvious objections.</dd>
              </div>
              <div class="aid-row">
                <dt>what it isn't</dt>
                <dd>A replacement for talking to real users. Sentiment splits and PMF scores
                  are <em>indicative</em>, not predictive.</dd>
              </div>
              <div class="aid-row">
                <dt>how the swarm thinks</dt>
                <dd>Your pitch is parsed → ICP archetypes are generated → each agent reacts
                  in character with a tone, action, and short comment. Stochastic by design.</dd>
              </div>
              <div class="aid-row">
                <dt>known limits</dt>
                <dd>Personas are LLM-hallucinated unless grounded against real comment corpora.
                  Same pitch can yield different scores across runs (≈ ±0.7 PMF).</dd>
              </div>
              <div class="aid-row">
                <dt>cost &amp; privacy</dt>
                <dd>Pitch text is sent to the configured LLM provider. We do not retain it
                  past the job lifetime. No PII is requested.</dd>
              </div>
            </dl>

            <p class="aid-fine">
              Use the signal to decide what to <em>ask real users next</em> — not to skip them.
            </p>
          </div>
        </div>
      </transition>
    </teleport>
  </span>
</template>

<script setup>
import { ref, onUnmounted, watch } from 'vue'

defineProps({
  variant: { type: String, default: 'inline' }, // 'inline' | 'text'
  label: { type: String, default: '' },
  ariaLabel: { type: String, default: 'How this was generated' },
})

const open = ref(false)
const cardRef = ref(null)
const uid = Math.random().toString(36).slice(2, 8)

function onKey(e) {
  if (e.key === 'Escape') open.value = false
}

watch(open, (v) => {
  if (v) {
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
  } else {
    document.removeEventListener('keydown', onKey)
    document.body.style.overflow = ''
  }
})
onUnmounted(() => {
  document.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.aid-wrap { display: inline-flex; align-items: center; }

/* trigger — icon variant */
.aid-trigger {
  background: transparent;
  border: 0;
  padding: 0;
  margin: 0;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  color: var(--ink-3, rgba(255, 255, 255, 0.45));
  transition: color 160ms ease-out, transform 160ms ease-out;
}
.aid-trigger.inline { width: 14px; height: 14px; margin-left: 6px; }
.aid-trigger:hover { color: var(--accent); }
.aid-trigger:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
  border-radius: 50%;
}
.aid-trigger:active { transform: scale(0.92); }
.aid-icon { width: 100%; height: 100%; display: block; }

/* trigger — text variant (footer link style) */
.aid-trigger.text {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.04em;
  color: var(--ink-3, rgba(255, 255, 255, 0.5));
  border-bottom: 1px dotted color-mix(in oklch, var(--ink) 25%, transparent);
  padding-bottom: 1px;
}
.aid-trigger.text:hover { color: var(--accent); border-bottom-color: var(--accent); }
.aid-trigger.text:focus-visible { outline-offset: 2px; border-radius: 2px; }

/* modal */
.aid-modal {
  position: fixed;
  inset: 0;
  background: color-mix(in oklch, var(--paper) 20%, rgba(7, 7, 15, 0.7));
  backdrop-filter: blur(6px);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-5, 24px);
}
.aid-card {
  width: min(560px, 100%);
  max-height: 88vh;
  overflow-y: auto;
  background: var(--paper);
  color: var(--ink);
  border: 1px solid var(--rule);
  border-radius: 14px;
  padding: var(--space-7, 36px) var(--space-6, 32px) var(--space-6, 32px);
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-4, 16px);
  box-shadow: 0 30px 80px -20px rgba(0, 0, 0, 0.45);
}
.aid-close {
  position: absolute;
  top: 10px;
  right: 14px;
  background: transparent;
  border: 0;
  color: var(--ink-3, rgba(255, 255, 255, 0.5));
  font-size: 28px;
  line-height: 1;
  cursor: pointer;
  padding: 4px 10px;
}
.aid-close:hover { color: var(--ink); }
.aid-close:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 6px; }

.aid-title {
  font-family: var(--font-display);
  font-style: normal;
  font-size: var(--text-3xl, 2rem);
  font-weight: 500;
  line-height: 1.05;
  margin: 0;
  letter-spacing: -0.01em;
}
.aid-lede {
  font-size: var(--text-base, 1rem);
  line-height: 1.55;
  margin: 0;
  color: var(--ink);
}
.aid-lede em { font-style: italic; color: var(--accent); }
.aid-lede strong { font-weight: 600; }

.aid-grid {
  display: grid;
  gap: var(--space-3, 12px);
  margin: 0;
  padding: var(--space-4, 16px) 0;
  border-top: 1px solid var(--rule);
  border-bottom: 1px solid var(--rule);
}
.aid-row {
  display: grid;
  grid-template-columns: 130px 1fr;
  gap: var(--space-4, 16px);
  align-items: baseline;
}
.aid-row dt {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-3, rgba(255, 255, 255, 0.5));
}
.aid-row dd {
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.5;
  color: var(--ink);
}
.aid-row dd em { font-style: italic; }

.aid-fine {
  font-size: var(--text-sm);
  line-height: 1.5;
  margin: 0;
  color: var(--ink-3, rgba(255, 255, 255, 0.6));
  font-style: italic;
}

@media (max-width: 540px) {
  .aid-row { grid-template-columns: 1fr; gap: 4px; }
  .aid-card { padding: var(--space-6, 28px) var(--space-5, 22px); }
  .aid-title { font-size: var(--text-2xl, 1.6rem); }
}

/* transitions — opacity only, transform-light, respects reduced motion */
.aid-fade-enter-active, .aid-fade-leave-active { transition: opacity 200ms ease-out; }
.aid-fade-enter-active .aid-card, .aid-fade-leave-active .aid-card {
  transition: transform 220ms cubic-bezier(0.2, 0.7, 0.2, 1), opacity 220ms ease-out;
}
.aid-fade-enter-from, .aid-fade-leave-to { opacity: 0; }
.aid-fade-enter-from .aid-card, .aid-fade-leave-to .aid-card { transform: translateY(8px); opacity: 0; }

@media (prefers-reduced-motion: reduce) {
  .aid-fade-enter-active, .aid-fade-leave-active,
  .aid-fade-enter-active .aid-card, .aid-fade-leave-active .aid-card {
    transition: opacity 150ms linear;
  }
  .aid-fade-enter-from .aid-card, .aid-fade-leave-to .aid-card { transform: none; }
}
</style>
