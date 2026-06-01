<!-- Hallmark · component: product feedback widget · genre: feedback · theme: Midnight+coral
 * states: idle · panel-open · submitted · dismissed
 * entry: corner button (trigger:'button') OR auto-popup (trigger:'popup')
 * z-index: 70 (below brain drawer at 80)
 * contrast: pass
 -->
<template>
  <teleport to="body">
    <!-- Persistent corner pill -->
    <button
      v-if="!submitted && !panelOpen"
      type="button"
      class="fw-pill"
      aria-label="Give feedback"
      @click="openPanel('button')"
    >
      <svg class="fw-pill-icon" viewBox="0 0 16 16" aria-hidden="true" width="12" height="12">
        <path d="M8 1C4.13 1 1 3.69 1 7c0 1.77.82 3.37 2.14 4.5L2.5 14.5l3.3-1.65C6.5 13 7.23 13.1 8 13.1c3.87 0 7-2.69 7-6.1C15 3.69 11.87 1 8 1z"
          fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
      </svg>
      Feedback
    </button>

    <!-- Panel (corner card) -->
    <transition name="fw-slide">
      <div
        v-if="panelOpen"
        class="fw-card"
        role="dialog"
        aria-modal="false"
        aria-label="Product feedback"
        @keydown.esc="closePanel"
      >
        <!-- close -->
        <button type="button" class="fw-close" aria-label="Close feedback" @click="closePanel">×</button>

        <!-- step 1: helpful prompt -->
        <template v-if="!submitted">
          <p class="fw-prompt">Did this help you decide what to test next?</p>
          <div class="fw-vote-row">
            <button
              type="button"
              class="fw-vote-btn"
              :class="{ active: helpful === true }"
              aria-label="Yes, it helped"
              @click="selectHelpful(true)"
            >👍</button>
            <button
              type="button"
              class="fw-vote-btn"
              :class="{ active: helpful === false }"
              aria-label="No, it didn't help"
              @click="selectHelpful(false)"
            >👎</button>
          </div>

          <!-- step 2: optional detail — expands after vote -->
          <transition name="fw-expand">
            <div v-if="helpful !== null" class="fw-detail">
              <textarea
                v-model="comment"
                class="fw-textarea"
                placeholder="What would make it more useful? (optional)"
                rows="3"
                maxlength="600"
              />
              <input
                v-model="email"
                type="email"
                class="fw-email"
                placeholder="Email for follow-up (optional)"
                maxlength="200"
              />
              <button
                type="button"
                class="fw-send"
                :disabled="sending"
                @click="send"
              >
                {{ sending ? 'Sending…' : 'Send' }}
              </button>
            </div>
          </transition>
        </template>

        <!-- thanks state -->
        <template v-else>
          <p class="fw-thanks">Thanks — this trains the swarm.</p>
        </template>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { trackProductFeedback } from '../../lib/analytics.js'

const props = defineProps({
  jobId: { type: String, required: true },
})

const lsKey = () => `swv:fb:${props.jobId}`

const panelOpen = ref(false)
const submitted = ref(false)
const helpful = ref(null)
const comment = ref('')
const email = ref('')
const sending = ref(false)
const activeTrigger = ref('popup')

// Auto-popup guard — check if already shown for this job
function alreadyShown() {
  return !!localStorage.getItem(lsKey())
}

function setShown() {
  localStorage.setItem(lsKey(), '1')
}

function openPanel(trigger) {
  if (submitted.value) return
  activeTrigger.value = trigger
  panelOpen.value = true
}

// Close the panel only — the corner pill stays available for re-open.
// setShown() guards the auto-popup from re-firing, but never hides the pill.
function closePanel() {
  panelOpen.value = false
  setShown()
}

async function selectHelpful(v) {
  helpful.value = v
  // Record immediately so we capture signal even if user doesn't send detail
  await trackProductFeedback(props.jobId, {
    helpful: v,
    comment: null,
    email: null,
    trigger: activeTrigger.value,
  })
}

async function send() {
  if (sending.value) return
  sending.value = true
  await trackProductFeedback(props.jobId, {
    helpful: helpful.value,
    comment: comment.value || null,
    email: email.value || null,
    trigger: activeTrigger.value,
  })
  sending.value = false
  submitted.value = true
  setShown()
  setTimeout(() => {
    panelOpen.value = false
  }, 1500)
}

// --- Auto-popup logic ---
let dwellTimer = null
let scrollHandler = null

function tryAutoPopup() {
  if (alreadyShown()) return
  openPanel('popup')
  setShown()
  cleanup()
}

function onScroll() {
  const scrolled = window.scrollY + window.innerHeight
  const total = document.documentElement.scrollHeight
  if (total > 0 && scrolled / total >= 0.6) {
    tryAutoPopup()
  }
}

function cleanup() {
  if (dwellTimer) { clearTimeout(dwellTimer); dwellTimer = null }
  if (scrollHandler) { window.removeEventListener('scroll', scrollHandler, { passive: true }); scrollHandler = null }
}

onMounted(() => {
  if (alreadyShown()) return
  // Dwell timer — 15 s
  dwellTimer = setTimeout(() => { tryAutoPopup() }, 15000)
  // Scroll threshold — 60 %
  scrollHandler = onScroll
  window.addEventListener('scroll', scrollHandler, { passive: true })
})

onUnmounted(() => { cleanup() })
</script>

<style scoped>
/* Corner pill — always visible while not dismissed/submitted */
.fw-pill {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 70;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--paper-2, rgba(255, 255, 255, 0.06));
  border: 1px solid var(--rule, rgba(255, 255, 255, 0.12));
  border-radius: var(--radius-pill, 999px);
  padding: 6px 14px 6px 10px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-3, rgba(255, 255, 255, 0.5));
  cursor: pointer;
  backdrop-filter: blur(8px);
  transition: border-color 150ms ease-out, color 150ms ease-out, background 150ms ease-out;
}
.fw-pill:hover {
  border-color: var(--accent, #e05a2b);
  color: var(--ink, #fff);
  background: color-mix(in oklch, var(--accent, #e05a2b) 10%, var(--paper-2, rgba(255,255,255,0.06)));
}
.fw-pill:focus-visible {
  outline: 2px solid var(--accent, #e05a2b);
  outline-offset: 2px;
}
.fw-pill-icon {
  flex-shrink: 0;
  color: inherit;
}

/* Panel card — corner toast */
.fw-card {
  position: fixed;
  bottom: 60px;
  right: 20px;
  z-index: 70;
  width: min(320px, calc(100vw - 32px));
  background: var(--paper, #0b0b12);
  border: 1px solid var(--rule, rgba(255, 255, 255, 0.12));
  border-radius: var(--radius-lg, 14px);
  padding: var(--space-5, 20px) var(--space-5, 20px) var(--space-4, 16px);
  box-shadow: 0 16px 48px -8px rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  gap: var(--space-3, 12px);
}

.fw-close {
  position: absolute;
  top: 8px;
  right: 12px;
  background: transparent;
  border: 0;
  color: var(--ink-3, rgba(255, 255, 255, 0.4));
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
  padding: 2px 6px;
}
.fw-close:hover { color: var(--ink, #fff); }
.fw-close:focus-visible {
  outline: 2px solid var(--accent, #e05a2b);
  outline-offset: 2px;
  border-radius: 4px;
}

.fw-prompt {
  font-size: var(--text-sm, 0.875rem);
  line-height: 1.45;
  color: var(--ink, #fff);
  margin: 0;
  padding-right: 18px; /* room for close btn */
}

.fw-vote-row {
  display: flex;
  gap: var(--space-2, 8px);
}

.fw-vote-btn {
  flex: 1;
  background: var(--paper-2, rgba(255, 255, 255, 0.04));
  border: 1px solid var(--rule, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-lg, 10px);
  padding: var(--space-3, 10px);
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  transition: border-color 140ms ease-out, background 140ms ease-out, transform 100ms ease-out;
}
.fw-vote-btn:hover {
  border-color: var(--accent, #e05a2b);
  background: color-mix(in oklch, var(--accent, #e05a2b) 12%, transparent);
}
.fw-vote-btn:active { transform: scale(0.94); }
.fw-vote-btn:focus-visible {
  outline: 2px solid var(--accent, #e05a2b);
  outline-offset: 2px;
}
.fw-vote-btn.active {
  border-color: var(--accent, #e05a2b);
  background: color-mix(in oklch, var(--accent, #e05a2b) 18%, transparent);
}

/* optional detail section */
.fw-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-2, 8px);
  overflow: hidden;
}

.fw-textarea {
  width: 100%;
  background: var(--paper-3, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--rule, rgba(255, 255, 255, 0.1));
  border-radius: 8px;
  padding: 8px 10px;
  font-family: inherit;
  font-size: var(--text-sm, 0.875rem);
  line-height: 1.5;
  color: var(--ink, #fff);
  resize: vertical;
  box-sizing: border-box;
}
.fw-textarea::placeholder { color: var(--ink-3, rgba(255, 255, 255, 0.35)); }
.fw-textarea:focus {
  outline: none;
  border-color: var(--accent, #e05a2b);
}

.fw-email {
  width: 100%;
  background: var(--paper-3, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--rule, rgba(255, 255, 255, 0.1));
  border-radius: 8px;
  padding: 7px 10px;
  font-family: inherit;
  font-size: var(--text-sm, 0.875rem);
  color: var(--ink, #fff);
  box-sizing: border-box;
}
.fw-email::placeholder { color: var(--ink-3, rgba(255, 255, 255, 0.35)); }
.fw-email:focus {
  outline: none;
  border-color: var(--accent, #e05a2b);
}

.fw-send {
  align-self: flex-end;
  background: var(--accent, #e05a2b);
  border: 0;
  border-radius: var(--radius-pill, 999px);
  padding: 6px 18px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #fff;
  cursor: pointer;
  transition: opacity 140ms ease-out;
}
.fw-send:hover:not(:disabled) { opacity: 0.88; }
.fw-send:disabled { opacity: 0.45; cursor: not-allowed; }
.fw-send:focus-visible {
  outline: 2px solid var(--accent-bright, #ff7a50);
  outline-offset: 2px;
}

.fw-thanks {
  font-size: var(--text-sm, 0.875rem);
  color: var(--live, #4ade80);
  margin: 0;
  text-align: center;
  padding: var(--space-2, 8px) 0;
}

/* --- Transitions --- */
.fw-slide-enter-active {
  transition: opacity 220ms ease-out, transform 240ms cubic-bezier(0.2, 0.7, 0.2, 1);
}
.fw-slide-leave-active {
  transition: opacity 160ms ease-out, transform 160ms ease-out;
}
.fw-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.fw-slide-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

.fw-expand-enter-active {
  transition: opacity 200ms ease-out, max-height 280ms ease-out;
  max-height: 300px;
}
.fw-expand-leave-active {
  transition: opacity 150ms ease-out, max-height 200ms ease-out;
}
.fw-expand-enter-from {
  opacity: 0;
  max-height: 0;
}
.fw-expand-leave-to {
  opacity: 0;
  max-height: 0;
}

@media (prefers-reduced-motion: reduce) {
  .fw-pill,
  .fw-vote-btn { transition: none; }
  .fw-slide-enter-active,
  .fw-slide-leave-active { transition: opacity 120ms linear; }
  .fw-slide-enter-from,
  .fw-slide-leave-to { transform: none; }
  .fw-expand-enter-active,
  .fw-expand-leave-active { transition: opacity 100ms linear; }
}
</style>
