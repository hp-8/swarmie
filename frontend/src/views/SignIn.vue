<template>
  <div class="page">
    <SiteNav />
    <main class="signin">
      <div class="sheet">
        <h1 class="title">Sign in to Swarmie</h1>
        <p class="lede">We'll email you a sign-in link. No password. You need an account to buy review packs and run larger panels; free reviews work without one.</p>

        <form v-if="!sent" class="form" @submit.prevent="submit">
          <label for="email" class="label">Email</label>
          <input id="email" v-model.trim="email" class="input" type="email" required autocomplete="email" placeholder="you@company.com" :disabled="busy" />
          <button class="btn" type="submit" :disabled="busy || !email">{{ busy ? 'Sending…' : 'Email me a sign-in link' }}</button>
          <p v-if="error" class="error" role="alert">{{ error }}</p>
        </form>

        <div v-else class="sent" role="status">
          <p class="sent-title">Check your inbox.</p>
          <p class="sent-copy">We sent a sign-in link to <strong>{{ email }}</strong>. Open it on this device to continue. It can take a minute, and may land in spam.</p>
          <div class="sent-actions">
            <button class="btn btn-ghost" type="button" :disabled="busy || cooldown > 0" @click="resend">
              {{ busy ? 'Sending…' : cooldown > 0 ? `Resend link in ${cooldown}s` : 'Resend link' }}
            </button>
            <button class="link" type="button" @click="changeEmail">Use a different email</button>
          </div>
          <p v-if="resent" class="note">Sent again. Use the newest email; earlier links stop working.</p>
          <p v-if="error" class="error" role="alert">{{ error }}</p>
        </div>
      </div>
    </main>
    <SiteFooter />
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import SiteNav from '../components/marketing/SiteNav.vue'
import SiteFooter from '../components/marketing/SiteFooter.vue'
import { sendMagicLink } from '../lib/account'

const route = useRoute()
const email = ref('')
const busy = ref(false)
const sent = ref(false)
const error = ref('')
const resent = ref(false)
// Supabase allows one email per address about every 60s.
const COOLDOWN_S = 60
const cooldown = ref(0)
let timer = null
function startCooldown() {
  cooldown.value = COOLDOWN_S
  clearInterval(timer)
  timer = setInterval(() => {
    cooldown.value -= 1
    if (cooldown.value <= 0) clearInterval(timer)
  }, 1000)
}
onBeforeUnmount(() => clearInterval(timer))

// Return to the account page, carrying the pack the visitor meant to buy.
function nextPath() {
  const pack = typeof route.query.pack === 'string' ? route.query.pack : ''
  return pack ? `/account?buy=${encodeURIComponent(pack)}` : '/account'
}

async function submit() {
  busy.value = true
  error.value = ''
  try {
    await sendMagicLink(email.value, nextPath())
    sent.value = true
    startCooldown()
  } catch (e) {
    error.value = e?.message || 'Could not send the link. Try again in a moment.'
  } finally {
    busy.value = false
  }
}

async function resend() {
  resent.value = false
  await submit()
  if (!error.value) resent.value = true
}

function changeEmail() {
  sent.value = false
  resent.value = false
  error.value = ''
}
</script>

<style scoped>
.page { min-height: 100vh; color: var(--ink); background: var(--paper-2); display: flex; flex-direction: column; }
.signin { flex: 1; display: grid; place-items: start center; padding: var(--space-9) var(--space-4); }
.sheet { width: min(520px, 100%); background: var(--paper); border: 1px solid var(--rule); box-shadow: 0 24px 48px -36px oklch(20% 0.02 250 / 0.4); padding: var(--space-7) var(--space-6); }
.title { margin: 0; font-family: var(--font-display); font-weight: 600; font-size: var(--text-3xl); line-height: 1.1; letter-spacing: -0.015em; }
.lede { margin: var(--space-3) 0 var(--space-6); color: var(--ink-2); line-height: 1.6; }
.form { display: grid; gap: var(--space-2); }
.label { font-size: var(--text-sm); font-weight: 700; }
.input { font: inherit; padding: 12px 14px; border: 1px solid var(--rule-2); border-radius: var(--radius-sm); color: var(--ink); background: var(--paper); }
.input:focus { outline: none; border-color: var(--ink); box-shadow: 0 0 0 3px oklch(50% 0.11 250 / 0.15); }
.btn { margin-top: var(--space-2); font: inherit; font-weight: 700; padding: 13px 18px; border: 0; border-radius: var(--radius-sm); background: var(--ink); color: var(--paper); cursor: pointer; }
.btn:hover:not(:disabled) { background: var(--ink-2); }
.btn:disabled { background: var(--paper-4); color: var(--ink-3); cursor: not-allowed; }
.error { margin: var(--space-2) 0 0; font-size: var(--text-sm); color: var(--warn); }
.sent-title { margin: 0; font-weight: 700; font-size: var(--text-lg); }
.sent-copy { margin: var(--space-2) 0 var(--space-4); color: var(--ink-2); line-height: 1.6; overflow-wrap: anywhere; }
.sent-actions { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-4); }
.btn-ghost { margin-top: 0; background: var(--paper); color: var(--ink); border: 1px solid var(--rule-2); }
.btn-ghost:hover:not(:disabled) { background: var(--paper-3); }
.btn-ghost:disabled { background: var(--paper-2); color: var(--ink-3); cursor: not-allowed; }
.note { margin: var(--space-3) 0 0; font-size: var(--text-sm); color: var(--ink-2); }
.link { font: inherit; font-size: var(--text-sm); color: var(--ink-2); background: none; border: 0; padding: 0; cursor: pointer; text-decoration: underline; text-underline-offset: 3px; }
</style>
