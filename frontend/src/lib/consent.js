/**
 * Consent state — single source of truth for cookie/analytics + ToS consent.
 *
 * Privacy-first: nothing non-essential runs until the user picks "Accept all".
 * Choice is stored locally; no tracking happens to record the choice itself.
 *
 * Versioned keys so a future policy change can re-prompt.
 */

const CONSENT_KEY = 'swarmie_consent_v1'   // 'all' | 'essential'
const TOS_KEY = 'swarmie_tos_v1'           // '1' once the run-consent is accepted

const _listeners = new Set()

function _read(key) {
  try { return localStorage.getItem(key) } catch { return null }
}
function _write(key, val) {
  try { localStorage.setItem(key, val) } catch { /* storage blocked */ }
}

/** 'all' | 'essential' | null (not yet chosen). */
export function getConsent() {
  const v = _read(CONSENT_KEY)
  return v === 'all' || v === 'essential' ? v : null
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
  _write(CONSENT_KEY, value)
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
