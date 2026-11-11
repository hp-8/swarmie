<template>
  <div class="page">
    <SiteNav />
    <main class="account">
      <p v-if="mode === 'test'" class="banner banner-test" role="note">
        Test mode: no real charges. Pay with card 4242 4242 4242 4242, any future date and CVC.
      </p>
      <p v-if="purchased" class="banner" role="status">
        Payment received. Your credits appear below within a few seconds.
      </p>

      <section class="sheet">
        <template v-if="!session">
          <h1 class="title">Your account</h1>
          <p class="lede">Sign in to see your review credits and buy packs.</p>
          <router-link to="/signin" class="btn">Sign in</router-link>
        </template>

        <template v-else>
          <div class="head">
            <div>
              <h1 class="title">Your account</h1>
              <p class="who">{{ me?.email || session.user?.email }}</p>
            </div>
            <button class="link" type="button" @click="logout">Sign out</button>
          </div>

          <div class="balance">
            <p class="bal-num">{{ loading ? '…' : (me?.credits ?? 0) }}</p>
            <p class="bal-label">review credits. One credit runs one paid review at any panel size.</p>
          </div>
          <p v-if="error" class="error" role="alert">{{ error }}</p>

          <h2 class="sec">Buy a pack</h2>
          <ul class="packs">
            <li v-for="p in packs" :key="p.key" class="pack" :class="{ 'is-hero': p.key === 'sprint' }">
              <div>
                <p class="pack-name">{{ p.name }}</p>
                <p class="pack-qty">{{ p.credits }} reviews</p>
              </div>
              <div class="pack-buy">
                <p class="pack-price">
                  ${{ dollars(p.price_cents) }}
                  <span v-if="p.launch_price" class="pack-was">launch price, ${{ dollars(p.regular_cents) }} after</span>
                </p>
                <button class="btn btn-sm" type="button" :disabled="buying === p.key" @click="buy(p.key)">
                  {{ buying === p.key ? 'Opening checkout…' : 'Buy' }}
                </button>
              </div>
            </li>
          </ul>
          <p v-if="launchLeft !== null && launchLeft > 0" class="fine">Launch prices for the next {{ launchLeft }} buyers.</p>
          <p class="fine">Payments are handled by Stripe. A review that fails returns its credit automatically.</p>
        </template>
      </section>
    </main>
    <SiteFooter />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SiteNav from '../components/marketing/SiteNav.vue'
import SiteFooter from '../components/marketing/SiteFooter.vue'
import { session, signOut } from '../lib/account'
import { billingApi, buyPack } from '../api/billing'

const route = useRoute()
const router = useRouter()
const me = ref(null)
const packs = ref([])
const launchLeft = ref(null)
const mode = ref('')
const loading = ref(false)
const buying = ref('')
const error = ref('')
const purchased = route.query.purchase === 'success'

const dollars = (cents) => (cents / 100).toFixed(cents % 100 ? 2 : 0)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [m, p] = await Promise.all([billingApi.me(), billingApi.packs()])
    me.value = m
    packs.value = p.packs
    launchLeft.value = p.launch_remaining
    mode.value = p.mode || ''
  } catch (e) {
    error.value = e?.response?.data?.error || 'Could not load your account. Refresh to try again.'
  } finally {
    loading.value = false
  }
}

async function buy(pack) {
  buying.value = pack
  error.value = ''
  try {
    await buyPack(pack)
  } catch (e) {
    error.value = e?.response?.data?.error || 'Could not open checkout. Try again in a moment.'
    buying.value = ''
  }
}

async function logout() {
  await signOut()
  router.push('/')
}

// Session arrives asynchronously after a magic-link redirect.
watch(session, (s) => {
  if (!s) return
  load().then(() => {
    // Came from "Buy" while signed out: continue straight to checkout once.
    const want = route.query.buy
    if (typeof want === 'string' && packs.value.some((p) => p.key === want)) {
      router.replace({ query: {} })
      buy(want)
    }
  })
  // The webhook can land a moment after the redirect: refresh once.
  if (purchased) setTimeout(load, 4000)
}, { immediate: true })
</script>

<style scoped>
.page { min-height: 100vh; color: var(--ink); background: var(--paper-2); display: flex; flex-direction: column; }
.account { flex: 1; width: min(720px, 100%); margin: 0 auto; padding: var(--space-8) var(--space-4); }
.banner { margin: 0 0 var(--space-4); padding: var(--space-3) var(--space-4); background: var(--live-soft); color: var(--ink); border-radius: var(--radius-sm); font-weight: 600; }
.banner-test { background: var(--info-soft); }
.sheet { background: var(--paper); border: 1px solid var(--rule); box-shadow: 0 24px 48px -36px oklch(20% 0.02 250 / 0.4); padding: var(--space-7) var(--space-6); }
.head { display: flex; justify-content: space-between; align-items: start; gap: var(--space-4); }
.title { margin: 0; font-family: var(--font-display); font-weight: 600; font-size: var(--text-3xl); letter-spacing: -0.015em; }
.who { margin: var(--space-1) 0 0; color: var(--ink-3); overflow-wrap: anywhere; }
.lede { margin: var(--space-3) 0 var(--space-5); color: var(--ink-2); }
.balance { margin-top: var(--space-6); padding: var(--space-5) 0; border-top: 2px solid var(--ink); border-bottom: 1px solid var(--rule); display: flex; align-items: baseline; gap: var(--space-4); flex-wrap: wrap; }
.bal-num { margin: 0; font-family: var(--font-display); font-weight: 600; font-size: 64px; line-height: 1; font-variant-numeric: tabular-nums; }
.bal-label { margin: 0; color: var(--ink-2); max-width: 36ch; }
.sec { margin: var(--space-7) 0 var(--space-3); font-size: var(--text-lg); font-weight: 700; }
.packs { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-2); }
.pack { display: flex; justify-content: space-between; align-items: center; gap: var(--space-4); padding: var(--space-4); border: 1px solid var(--rule); border-radius: var(--radius-sm); }
.pack.is-hero { border-color: var(--ink); }
.pack-name { margin: 0; font-weight: 700; }
.pack-qty { margin: 2px 0 0; font-size: var(--text-sm); color: var(--ink-3); }
.pack-buy { display: flex; align-items: center; gap: var(--space-4); }
.pack-price { margin: 0; font-weight: 700; font-size: var(--text-lg); text-align: right; font-variant-numeric: tabular-nums; }
.pack-was { display: block; font-size: var(--text-xs); font-weight: 500; color: var(--ink-3); }
.btn { display: inline-block; font: inherit; font-weight: 700; padding: 12px 18px; border: 0; border-radius: var(--radius-sm); background: var(--ink); color: var(--paper); cursor: pointer; }
.btn:hover:not(:disabled) { background: var(--ink-2); }
.btn:disabled { background: var(--paper-4); color: var(--ink-3); cursor: wait; }
.btn-sm { padding: 9px 16px; font-size: var(--text-sm); }
.link { font: inherit; font-size: var(--text-sm); color: var(--ink-2); background: none; border: 0; padding: 0; cursor: pointer; text-decoration: underline; text-underline-offset: 3px; }
.error { margin: var(--space-3) 0 0; color: var(--warn); font-size: var(--text-sm); }
.fine { margin: var(--space-3) 0 0; font-size: var(--text-sm); color: var(--ink-3); }
@media (max-width: 767px) {
  .sheet { padding: var(--space-6) var(--space-4); }
  .pack { flex-direction: column; align-items: stretch; }
  .pack-buy { justify-content: space-between; }
  .pack-price { text-align: left; }
}
</style>
