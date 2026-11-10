/**
 * GA4 + Microsoft Clarity loader. Called only after analytics consent
 * (see main.js). IDs are public; set VITE_GA_ID / VITE_CLARITY_ID in Vercel.
 * Page views: GA4 Enhanced Measurement (history changes) — never send manually.
 */
const GA_ID = import.meta.env.VITE_GA_ID || 'G-7X7E1L8EEL'
const CLARITY_ID = import.meta.env.VITE_CLARITY_ID || 'zbc7wl350c'

function loadScript(src) {
  const s = document.createElement('script')
  s.async = true
  s.src = src
  document.head.appendChild(s)
}

export function loadThirdParty() {
  if (GA_ID && !window.gtag) {
    window.dataLayer = window.dataLayer || []
    window.gtag = function () { window.dataLayer.push(arguments) }
    window.gtag('js', new Date())
    window.gtag('config', GA_ID)
    loadScript(`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`)
  }
  if (CLARITY_ID && !window.clarity) {
    window.clarity = function () { (window.clarity.q = window.clarity.q || []).push(arguments) }
    loadScript(`https://www.clarity.ms/tag/${CLARITY_ID}`)
  }
}

/** GA4 event; no-op without consent/ID. */
export function track(name, params = {}) {
  try { window.gtag?.('event', name, params) } catch { /* ignore */ }
}
