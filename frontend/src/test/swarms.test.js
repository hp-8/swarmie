import { describe, it, expect } from 'vitest'
import { SWARMS } from '../lib/swarms.js'

describe('SWARMS catalogue', () => {
  it('has exactly 3 entries', () => {
    expect(SWARMS).toHaveLength(3)
  })

  it('each entry has required shape keys', () => {
    const requiredKeys = ['key', 'label', 'title', 'sub', 'placeholder', 'template', 'checks']
    for (const swarm of SWARMS) {
      for (const k of requiredKeys) {
        expect(swarm, `${swarm.key} missing "${k}"`).toHaveProperty(k)
      }
    }
  })

  it('validate swarm: checks has 5 entries', () => {
    const validate = SWARMS.find(s => s.key === 'validate')
    expect(validate.checks).toHaveLength(5)
  })

  it('investor swarm: checks has 5 entries', () => {
    const investor = SWARMS.find(s => s.key === 'investor')
    expect(investor.checks).toHaveLength(5)
  })

  it('launch swarm: checks has 5 entries', () => {
    const launch = SWARMS.find(s => s.key === 'launch')
    expect(launch.checks).toHaveLength(5)
  })

  it('each check has pattern (RegExp) and key and label', () => {
    for (const swarm of SWARMS) {
      for (const check of swarm.checks) {
        expect(check).toHaveProperty('key')
        expect(check).toHaveProperty('label')
        expect(check).toHaveProperty('pattern')
        expect(check.pattern).toBeInstanceOf(RegExp)
      }
    }
  })

  describe('validate swarm pattern spot-checks', () => {
    const validate = SWARMS.find(s => s.key === 'validate')
    const byKey = (k) => validate.checks.find(c => c.key === k)

    it('problem pattern matches "problem: we need X"', () => {
      expect(byKey('problem').pattern.test('problem: we need X')).toBe(true)
    })

    it('problem pattern does NOT match empty "problem:"', () => {
      expect(byKey('problem').pattern.test('problem:  ')).toBe(false)
    })

    it('pricing pattern matches "$49/seat"', () => {
      expect(byKey('pricing').pattern.test('$49/seat')).toBe(true)
    })

    it('pricing pattern matches "pricing: per-seat"', () => {
      expect(byKey('pricing').pattern.test('pricing: per-seat model')).toBe(true)
    })

    it('competitor pattern matches "vs. Salesforce"', () => {
      expect(byKey('competitor').pattern.test('vs. Salesforce')).toBe(true)
    })

    it('competitor pattern matches "alternative to HubSpot"', () => {
      expect(byKey('competitor').pattern.test('alternative to HubSpot')).toBe(true)
    })

    it('audience pattern matches "who: B2B AEs"', () => {
      expect(byKey('audience').pattern.test('who: B2B AEs with > 50 cold replies')).toBe(true)
    })
  })

  describe('investor swarm pattern spot-checks', () => {
    const investor = SWARMS.find(s => s.key === 'investor')
    const byKey = (k) => investor.checks.find(c => c.key === k)

    it('traction pattern matches "mrr: $40k"', () => {
      expect(byKey('traction').pattern.test('mrr: $40k')).toBe(true)
    })

    it('traction pattern matches "revenue: $200k ARR"', () => {
      expect(byKey('traction').pattern.test('revenue: $200k ARR')).toBe(true)
    })

    it('raise pattern matches "raising: $2M seed"', () => {
      expect(byKey('raise').pattern.test('raising: $2M seed')).toBe(true)
    })

    it('raise pattern matches "pre-seed round"', () => {
      expect(byKey('raise').pattern.test('pre-seed round: $500k')).toBe(true)
    })

    it('market pattern matches "tam: $5B"', () => {
      expect(byKey('market').pattern.test('tam: $5B market')).toBe(true)
    })
  })

  describe('launch swarm pattern spot-checks', () => {
    const launch = SWARMS.find(s => s.key === 'launch')
    const byKey = (k) => launch.checks.find(c => c.key === k)

    it('channel pattern matches "product hunt"', () => {
      expect(byKey('channel').pattern.test('product hunt launch')).toBe(true)
    })

    it('channel pattern matches "channel: hacker news"', () => {
      expect(byKey('channel').pattern.test('channel: hacker news')).toBe(true)
    })

    it('differentiation pattern matches "different: no-code"', () => {
      expect(byKey('differentiation').pattern.test('different: no-code setup')).toBe(true)
    })

    it('timing pattern matches "timing: AI wave"', () => {
      expect(byKey('timing').pattern.test('timing: AI wave is peaking')).toBe(true)
    })
  })

  it('all swarms have agentNoun string', () => {
    for (const s of SWARMS) {
      expect(typeof s.agentNoun).toBe('string')
      expect(s.agentNoun.length).toBeGreaterThan(0)
    }
  })

  it('all swarms have enabled: true', () => {
    for (const s of SWARMS) {
      expect(s.enabled).toBe(true)
    }
  })
})
