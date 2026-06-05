<template>
  <transition name="consent">
    <div v-if="show" class="consent" role="dialog" aria-label="Cookie consent" aria-live="polite">
      <div class="consent-body">
        <p class="consent-text">
          Cookies keep Swarmie running and help us make it better. The choice is yours.
        </p>
        <p class="consent-sub">
          Reject keeps <em>essentials only</em>.
          <router-link to="/privacy" class="consent-link">Privacy</router-link>
          <span class="consent-dot">·</span>
          <router-link to="/terms" class="consent-link">Terms</router-link>
        </p>
      </div>
      <div class="consent-actions">
        <button type="button" class="consent-btn reject" @click="choose('essential')">Reject</button>
        <button type="button" class="consent-btn accept" @click="choose('all')">Accept all</button>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref } from 'vue'
import { hasConsentChoice, setConsent } from '../lib/consent'

const show = ref(!hasConsentChoice())

function choose(choice) {
  setConsent(choice)
  show.value = false
}
</script>

<style scoped>
.consent {
  position: fixed;
  left: 50%;
  bottom: var(--space-4);
  transform: translateX(-50%);
  z-index: 200;
  width: min(720px, calc(100% - var(--space-6)));
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: var(--space-4) var(--space-5);
  background: var(--paper-2);
  border: 1px solid var(--rule-2);
  border-radius: var(--radius-lg);
  box-shadow: 0 12px 40px color-mix(in oklch, black 45%, transparent);
}
.consent-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.consent-text { margin: 0; font-family: var(--font-body); font-size: var(--text-sm); line-height: 1.5; color: var(--ink-2); }
.consent-sub { margin: 0; font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.04em; color: var(--ink-3); }
.consent-sub em { font-style: normal; color: var(--ink-2); }
.consent-link { color: var(--accent-bright); text-decoration: underline; text-underline-offset: 2px; }
.consent-link:hover { color: var(--accent); }
.consent-dot { margin: 0 6px; color: var(--ink-4); }

.consent-actions { display: flex; gap: var(--space-2); flex-shrink: 0; }
.consent-btn {
  font-family: var(--font-mono); font-size: var(--text-xs);
  letter-spacing: 0.12em; text-transform: uppercase; font-weight: 600;
  padding: 10px 18px; border-radius: var(--radius-pill); cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out),
              border-color var(--dur-fast) var(--ease-out),
              color var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out);
}
.consent-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.consent-btn:active { transform: translateY(1px); }
/* Equal prominence (GDPR/ePrivacy): reject must be as easy + visible as accept.
   Identical chrome; accept steered only by accent-colored label, not a louder fill. */
.consent-btn.reject,
.consent-btn.accept {
  background: var(--paper-3);
  border: 1px solid var(--rule-2);
  color: var(--ink);
}
.consent-btn.reject:hover,
.consent-btn.accept:hover {
  background: var(--paper-4);
  border-color: var(--ink-4);
}
.consent-btn.accept { color: var(--accent-bright); }

@media (max-width: 640px) {
  .consent {
    flex-direction: column; align-items: stretch; gap: var(--space-3);
    bottom: 0; left: 0; transform: none; width: 100%;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    border-bottom: none;
    padding: var(--space-4) var(--space-4) calc(var(--space-4) + env(safe-area-inset-bottom));
  }
  .consent-text { font-size: var(--text-sm); }
  .consent-actions { width: 100%; }
  .consent-btn { flex: 1; min-height: 44px; padding: 12px 18px; }
}

.consent-enter-active { animation: consent-in 280ms var(--ease-out); }
@keyframes consent-in { from { opacity: 0; transform: translateX(-50%) translateY(12px); } to { opacity: 1; } }
@media (max-width: 640px) {
  .consent-enter-active { animation: consent-in-m 280ms var(--ease-out); }
  @keyframes consent-in-m { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; } }
}
@media (prefers-reduced-motion: reduce) {
  .consent-enter-active { animation: none; }
}
</style>
