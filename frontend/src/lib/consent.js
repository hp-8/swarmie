/**
 * Consent state — single source of truth for cookie/analytics + ToS consent.
 *
 * Privacy-first: nothing non-essential runs until the user picks "Accept all".
 * Choice is stored locally; no tracking happens to record the choice itself.
 *
 * Versioned keys so a future policy change can re-prompt.
 */

import { ref } from 'vue'

const CONSENT_KEY = 'swarmie_consent_v1'   // 'all' | 'essential'
const TOS_KEY = 'swarmie_tos_v1'           // '1' once the run-consent is accepted

const _listeners = new Set()

function _read(key) {
  try { return localStorage.getItem(key) } catch { return null }
}
function _write(key, val) {
  try { localStorage.setItem(key, val) } catch { /* storage blocked */ }
}

/** Banner visibility, shared so a footer "Cookie settings" link can reopen it. */
export const consentBannerOpen = ref(false)

/**
 * Opt-in regions (EU/EEA, UK, Switzerland) need consent before analytics.
 * Elsewhere analytics is on by default with an opt-out. Detected from the
 * browser timezone: no network call, and errs toward opt-in (all Europe/*).
 */
const OPT_IN_ATLANTIC = ['Atlantic/Reykjavik', 'Atlantic/Canary', 'Atlantic/Madeira', 'Atlantic/Azores', 'Atlantic/Faroe']
export function requiresOptIn() {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''
    return !tz || tz.startsWith('Europe/') || OPT_IN_ATLANTIC.includes(tz)
  } catch { return true }
}

/** Stored choice: 'all' | 'essential' | null (not yet chosen). */
function _stored() {
  const v = _read(CONSENT_KEY)
  return v === 'all' || v === 'essential' ? v : null
}

/** Effective consent: stored choice, else 'all' outside opt-in regions. */
export function getConsent() {
  return _stored() ?? (requiresOptIn() ? null : 'all')
}

export function openConsentSettings() {
  consentBannerOpen.value = true
}

// Remove GA4 / Clarity cookies after an opt-out.
function _clearAnalyticsCookies() {
  for (const c of document.cookie.split(';')) {
    const name = c.split('=')[0].trim()
    if (/^(_ga|_gid|_gat|_clck|_clsk|CLID|MUID)/.test(name)) {
      for (const domain of ['', `; domain=${location.hostname}`, `; domain=.${location.hostname}`]) {
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/${domain}`
      }
    }
  }
}

/** True once the user has made any cookie choice (banner can hide). */
export function hasConsentChoice() {
  return getConsent() !== null
}

/** True only when the user accepted non-essential analytics. */
export function hasAnalyticsConsent() {
  return getConsent() === 'all'
}

/** Record the cookie choice and notify listeners. */
export function setConsent(choice) {
  const value = choice === 'all' ? 'all' : 'essential'
  const wasOn = hasAnalyticsConsent()
  _write(CONSENT_KEY, value)
  consentBannerOpen.value = false
  if (wasOn && value === 'essential') {
    // Scripts already loaded can't be unloaded; clear cookies and reload clean.
    _clearAnalyticsCookies()
    location.reload()
    return value
  }
  for (const fn of _listeners) {
    try { fn(value) } catch { /* listener error — ignore */ }
  }
  return value
}

/** Subscribe to consent changes. Returns an unsubscribe fn. */
export function onConsentChange(fn) {
  _listeners.add(fn)
  return () => _listeners.delete(fn)
}

// --- run consent (ToS + AI-data acknowledgement before first run) ---

export function hasAcceptedRunTerms() {
  return _read(TOS_KEY) === '1'
}
export function acceptRunTerms() {
  _write(TOS_KEY, '1')
}
