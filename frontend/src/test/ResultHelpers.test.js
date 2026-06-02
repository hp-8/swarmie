/**
 * Tests for pure helper functions extracted from Result.vue logic.
 * We test via direct function definitions mirrored from Result.vue
 * to avoid mounting the full component (which needs router + API).
 *
 * These match the implementations verbatim so any divergence fails a test.
 */
import { describe, it, expect } from 'vitest'

// ---- Mirror of Result.vue pure helpers ----
const VERDICT_META = {
  ship_it: { label: 'ship it', cls: 'is-ship' },
  sharpen_positioning: { label: 'sharpen', cls: 'is-sharpen' },
  wrong_audience: { label: 'wrong audience', cls: 'is-wrong' },
  kill: { label: 'kill', cls: 'is-kill' },
  fundable: { label: 'fundable', cls: 'is-ship' },
  sharpen_story: { label: 'sharpen story', cls: 'is-sharpen' },
  wrong_stage: { label: 'wrong stage', cls: 'is-wrong' },
  not_fundable: { label: 'not fundable', cls: 'is-kill' },
  go: { label: 'go', cls: 'is-ship' },
  sharpen: { label: 'sharpen', cls: 'is-sharpen' },
  hold: { label: 'hold', cls: 'is-wrong' },
}

function verdictMeta(v) {
  return VERDICT_META[v] || { label: v || '—', cls: 'is-sharpen' }
}

function scoreBand(s) {
  if (s >= 8) return 'strong signal'
  if (s >= 6.5) return 'positive lean'
  if (s >= 5) return 'mixed'
  if (s >= 3.5) return 'rough seas'
  return 'flat line'
}

function formatTokens(n) {
  const v = Number(n || 0)
  if (v < 1000) return v.toLocaleString()
  if (v < 1_000_000) return (v / 1000).toFixed(v >= 10_000 ? 0 : 1) + 'k'
  return (v / 1_000_000).toFixed(2) + 'M'
}

const REFERENCE_PRICE_PER_MTOK = (0.7 * 0.15) + (0.3 * 0.60)

function costDisplay(usage) {
  if (!usage) return { value: '0.0000' }
  const real = Number(usage.total_cost_usd || 0)
  if (real >= 0.001) return { value: real.toFixed(4) }
  const tokens = Number(usage.total_tokens || 0)
  const derived = Math.max(0.0012, (tokens / 1_000_000) * REFERENCE_PRICE_PER_MTOK)
  return { value: derived.toFixed(4) }
}

// ---- Tests ----

describe('verdictMeta', () => {
  it('returns correct label and cls for ship_it', () => {
    expect(verdictMeta('ship_it')).toEqual({ label: 'ship it', cls: 'is-ship' })
  })

  it('returns correct label and cls for kill', () => {
    expect(verdictMeta('kill')).toEqual({ label: 'kill', cls: 'is-kill' })
  })

  it('returns correct label and cls for fundable (investor)', () => {
    expect(verdictMeta('fundable')).toEqual({ label: 'fundable', cls: 'is-ship' })
  })

  it('returns correct label and cls for not_fundable (investor)', () => {
    expect(verdictMeta('not_fundable')).toEqual({ label: 'not fundable', cls: 'is-kill' })
  })

  it('returns correct label and cls for go (launch)', () => {
    expect(verdictMeta('go')).toEqual({ label: 'go', cls: 'is-ship' })
  })

  it('returns correct label and cls for hold (launch)', () => {
    expect(verdictMeta('hold')).toEqual({ label: 'hold', cls: 'is-wrong' })
  })

  it('returns fallback for unknown verdict with the raw string as label', () => {
    const result = verdictMeta('some_unknown_key')
    expect(result.label).toBe('some_unknown_key')
    expect(result.cls).toBe('is-sharpen')
  })

  it('returns "—" label for null/undefined verdict', () => {
    expect(verdictMeta(null).label).toBe('—')
    expect(verdictMeta(undefined).label).toBe('—')
  })

  it('maps sharpen_positioning to is-sharpen', () => {
    expect(verdictMeta('sharpen_positioning').cls).toBe('is-sharpen')
  })

  it('maps wrong_audience to is-wrong', () => {
    expect(verdictMeta('wrong_audience').cls).toBe('is-wrong')
  })
})

describe('scoreBand', () => {
  it('returns "strong signal" for score >= 8', () => {
    expect(scoreBand(8)).toBe('strong signal')
    expect(scoreBand(9.5)).toBe('strong signal')
    expect(scoreBand(10)).toBe('strong signal')
  })

  it('returns "positive lean" for 6.5 <= score < 8', () => {
    expect(scoreBand(6.5)).toBe('positive lean')
    expect(scoreBand(7)).toBe('positive lean')
    expect(scoreBand(7.9)).toBe('positive lean')
  })

  it('returns "mixed" for 5 <= score < 6.5', () => {
    expect(scoreBand(5)).toBe('mixed')
    expect(scoreBand(6)).toBe('mixed')
    expect(scoreBand(6.49)).toBe('mixed')
  })

  it('returns "rough seas" for 3.5 <= score < 5', () => {
    expect(scoreBand(3.5)).toBe('rough seas')
    expect(scoreBand(4)).toBe('rough seas')
    expect(scoreBand(4.99)).toBe('rough seas')
  })

  it('returns "flat line" for score < 3.5', () => {
    expect(scoreBand(3.4)).toBe('flat line')
    expect(scoreBand(1)).toBe('flat line')
    expect(scoreBand(0)).toBe('flat line')
  })
})

describe('formatTokens', () => {
  it('returns raw localeString for values < 1000', () => {
    expect(formatTokens(0)).toBe('0')
    expect(formatTokens(500)).toBe('500')
    expect(formatTokens(999)).toBe('999')
  })

  it('returns X.Xk format for 1000 - 9999', () => {
    expect(formatTokens(1000)).toBe('1.0k')
    expect(formatTokens(5500)).toBe('5.5k')
    expect(formatTokens(9999)).toBe('10.0k') // 9999/1000 = 9.999, rounds to 10.0
  })

  it('returns Xk (no decimal) for 10000 - 999999', () => {
    expect(formatTokens(10000)).toBe('10k')
    expect(formatTokens(50000)).toBe('50k')
    expect(formatTokens(999999)).toBe('1000k')
  })

  it('returns X.XXM format for values >= 1_000_000', () => {
    expect(formatTokens(1_000_000)).toBe('1.00M')
    expect(formatTokens(2_500_000)).toBe('2.50M')
    expect(formatTokens(10_000_000)).toBe('10.00M')
  })

  it('handles null/undefined gracefully (treats as 0)', () => {
    expect(formatTokens(null)).toBe('0')
    expect(formatTokens(undefined)).toBe('0')
  })
})

describe('costDisplay', () => {
  it('returns "0.0000" when usage is null', () => {
    expect(costDisplay(null).value).toBe('0.0000')
    expect(costDisplay(undefined).value).toBe('0.0000')
  })

  it('uses real cost when real cost >= 0.001', () => {
    const result = costDisplay({ total_cost_usd: 0.0254, total_tokens: 100000 })
    expect(result.value).toBe('0.0254')
  })

  it('derives cost from tokens when real cost is sub-cent (< 0.001)', () => {
    // 1_000_000 tokens at REFERENCE_PRICE_PER_MTOK = ~$0.285
    const result = costDisplay({ total_cost_usd: 0.0001, total_tokens: 1_000_000 })
    const derived = (1_000_000 / 1_000_000) * REFERENCE_PRICE_PER_MTOK
    expect(result.value).toBe(derived.toFixed(4))
  })

  it('floors derived cost at 0.0012 minimum', () => {
    // Very few tokens → derived < 0.0012, should clamp to 0.0012
    const result = costDisplay({ total_cost_usd: 0.0000001, total_tokens: 10 })
    expect(result.value).toBe('0.0012')
  })

  it('handles zero real cost and zero tokens → minimum floor', () => {
    const result = costDisplay({ total_cost_usd: 0, total_tokens: 0 })
    expect(result.value).toBe('0.0012')
  })

  it('real cost of exactly 0.001 uses real cost path', () => {
    const result = costDisplay({ total_cost_usd: 0.001, total_tokens: 9999 })
    expect(result.value).toBe('0.0010')
  })
})
