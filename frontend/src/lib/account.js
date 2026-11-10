// Account session (Supabase Auth, email magic link). Billing UI shows only when
// VITE_BILLING_ENABLED is true; the backend enforces credits either way.
import { ref } from 'vue'
import { supabase } from './supabase'

export const BILLING_ENABLED = import.meta.env.VITE_BILLING_ENABLED === 'true'

export const session = ref(null)

if (supabase && BILLING_ENABLED) {
  supabase.auth.getSession().then(({ data }) => { session.value = data.session })
  supabase.auth.onAuthStateChange((_event, s) => { session.value = s })
}

export function accessToken() {
  return session.value?.access_token || null
}

export async function sendMagicLink(email, next = '/account') {
  if (!supabase) throw new Error('Sign-in is not configured.')
  const { error } = await supabase.auth.signInWithOtp({
    email,
    options: { emailRedirectTo: `${window.location.origin}${next}` },
  })
  if (error) throw error
}

export async function signOut() {
  if (supabase) await supabase.auth.signOut()
  session.value = null
}
