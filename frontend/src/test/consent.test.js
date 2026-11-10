import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { getConsent, requiresOptIn } from '../lib/consent'

const tz = (zone) => vi.spyOn(Intl, 'DateTimeFormat').mockReturnValue({ resolvedOptions: () => ({ timeZone: zone }) })

describe('geo consent', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => vi.restoreAllMocks())

  it('EU timezone requires opt-in, no implied consent', () => {
    tz('Europe/Berlin')
    expect(requiresOptIn()).toBe(true)
    expect(getConsent()).toBe(null)
  })
  it('non-EU defaults to analytics on', () => {
    tz('Asia/Kolkata')
    expect(getConsent()).toBe('all')
  })
  it('stored opt-out wins everywhere', () => {
    tz('America/New_York')
    localStorage.setItem('swarmie_consent_v1', 'essential')
    expect(getConsent()).toBe('essential')
  })
})
