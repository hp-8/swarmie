import { createApp } from 'vue'
import { inject as injectAnalytics } from '@vercel/analytics'
import App from './App.vue'
import router from './router'
import './styles/tokens.css'

const app = createApp(App)

app.use(router)

app.mount('#app')

// Vercel Web Analytics — privacy-friendly, no cookies.
if (import.meta.env.PROD) {
  injectAnalytics()
}
