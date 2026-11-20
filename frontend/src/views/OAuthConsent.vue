<template>
  <main class="consent">
    <h1>Connect to Swarmie</h1>
    <p v-if="error" class="error">{{ error }}</p>
    <template v-else-if="details">
      <p><strong>{{ details.client?.name || 'An app' }}</strong> wants to run Swarmie reviews on your account and use your review credits.</p>
      <p class="muted">Signed in as {{ email }}</p>
      <div class="actions">
        <button :disabled="busy" @click="decide(true)">Allow</button>
        <button :disabled="busy" class="secondary" @click="decide(false)">Deny</button>
      </div>
    </template>
    <p v-else>Loading…</p>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'

const route = useRoute()
const router = useRouter()
const details = ref(null)
const email = ref('')
const error = ref('')
const busy = ref(false)
const id = typeof route.query.authorization_id === 'string' ? route.query.authorization_id : ''

onMounted(async () => {
  if (!supabase || !id) { error.value = 'Invalid authorization request.'; return }
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) {
    router.replace({ path: '/signin', query: { next: route.fullPath } })
    return
  }
  email.value = session.user.email
  const { data, error: e } = await supabase.auth.oauth.getAuthorizationDetails(id)
  if (e) { error.value = e.message; return }
  // Already approved before: Supabase hands back the redirect directly.
  if (data.redirect_url && !data.client) { window.location.href = data.redirect_url; return }
  details.value = data
})

async function decide(allow) {
  busy.value = true
  const fn = allow ? 'approveAuthorization' : 'denyAuthorization'
  const { error: e } = await supabase.auth.oauth[fn](id)
  if (e) { error.value = e.message; busy.value = false }
}
</script>

<style scoped>
.consent { max-width: 28rem; margin: 6rem auto; padding: 0 16px; }
.actions { display: flex; gap: 12px; margin-top: 1.5rem; }
.muted { opacity: .7; font-size: .9rem; }
.error { color: #c0392b; }
</style>
