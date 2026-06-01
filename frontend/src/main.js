import { createApp } from 'vue'
import { inject as injectAnalytics } from '@vercel/analytics'
import App from './App.vue'
import router from './router'
import './styles/tokens.css'
import { registerDevice } from './lib/analytics'
import { hasAnalyticsConsent, onConsentChange } from './lib/consent'

const app = createApp(App)

app.use(router)

app.mount('#app')

// Nothing non-essential runs until the user accepts analytics consent.
let _analyticsOn = false
function enableAnalytics() {
  if (_analyticsOn || !hasAnalyticsConsent()) return
  _analyticsOn = true
  if (import.meta.env.PROD) injectAnalytics()
  registerDevice().catch(() => {})
}

// On if consent was given previously; otherwise wait for the banner choice.
enableAnalytics()
onConsentChange(() => enableAnalytics())
