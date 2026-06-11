import { describe, it, expect } from 'vitest'
import {
  wrapLines,
  layoutText,
  fitFontSize,
  agentCountLine,
  confidenceLine,
  resolveVerdictDisplay,
  buildDotField,
  CARD_W,
  CARD_H,
  CARD_COLORS,
} from '../lib/shareCard'
import { verdictMeta, VERDICT_HEX } from '../lib/verdict'

// Deterministic stand-in for ctx.measureText: 10px per character.
const measure = (s) => s.length * 10

describe('wrapLines', () => {
  it('wraps on word boundaries within maxWidth', () => {
    expect(wrapLines('aaa bbb ccc', 80, measure)).toEqual(['aaa bbb', 'ccc'])
  })

  it('returns a single line when everything fits', () => {
    expect(wrapLines('aaa bbb', 200, measure)).toEqual(['aaa bbb'])
  })

  it('hard-breaks a single oversized word instead of overflowing', () => {
    const lines = wrapLines('a'.repeat(25), 100, measure)
    expect(lines.length).toBeGreaterThan(1)
    for (const ln of lines) expect(measure(ln)).toBeLessThanOrEqual(100)
  })

  it('handles empty/nullish text', () => {
    expect(wrapLines('', 100, measure)).toEqual([])
    expect(wrapLines(null, 100, measure)).toEqual([])
  })
})

describe('layoutText', () => {
  it('clamps to maxLines with a trailing ellipsis', () => {
    const lines = layoutText('aaa bbb ccc ddd eee', { maxWidth: 80, maxLines: 2, measure })
    expect(lines).toHaveLength(2)
    expect(lines[1].endsWith('…')).toBe(true)
  })

  it('strips trailing punctuation before the ellipsis', () => {
    const lines = layoutText('word, word, word, word, word,', { maxWidth: 70, maxLines: 1, measure })
    expect(lines[0]).not.toMatch(/[,\s]…$/)
    expect(lines[0].endsWith('…')).toBe(true)
  })

  it('survives a 300-char unbroken objection without overflow', () => {
    const lines = layoutText('x'.repeat(300), { maxWidth: 200, maxLines: 3, measure })
    expect(lines).toHaveLength(3)
    for (const ln of lines) expect(measure(ln)).toBeLessThanOrEqual(200)
  })

  it('leaves short text untouched', () => {
    expect(layoutText('short', { maxWidth: 200, maxLines: 3, measure })).toEqual(['short'])
  })
})

describe('fitFontSize', () => {
  const measureAt = (size, text) => text.length * size * 0.6

  it('keeps the base size when the text fits', () => {
    expect(fitFontSize('hi', { maxWidth: 1000, baseSize: 116, minSize: 56, measureAt })).toBe(116)
  })

  it('shrinks until the text fits', () => {
    const size = fitFontSize('wrong audience', { maxWidth: 600, baseSize: 116, minSize: 56, measureAt })
    expect(size).toBeLessThan(116)
    expect(measureAt(size, 'wrong audience')).toBeLessThanOrEqual(600)
  })

  it('never goes below minSize', () => {
    expect(fitFontSize('x'.repeat(200), { maxWidth: 100, baseSize: 116, minSize: 56, measureAt })).toBe(56)
  })
})

describe('display lines', () => {
  it('agentCountLine pluralizes the swarm', () => {
    expect(agentCountLine(150)).toBe('150 synthetic users reacted')
    expect(agentCountLine(0)).toBe('synthetic swarm reacted')
    expect(agentCountLine(undefined)).toBe('synthetic swarm reacted')
  })

  it('confidenceLine renders only when present', () => {
    expect(confidenceLine('medium')).toBe('confidence · medium')
    expect(confidenceLine('')).toBe('')
  })
})

describe('resolveVerdictDisplay', () => {
  it('maps a verdict through the shared verdict meta', () => {
    const d = resolveVerdictDisplay({ verdict: 'kill' })
    expect(d.label).toBe('kill')
    expect(d.color).toBe(VERDICT_HEX['is-kill'])
  })

  it('falls back to pmf_score coloring for legacy reports', () => {
    expect(resolveVerdictDisplay({ pmf_score: 8.2 }).color).toBe(CARD_COLORS.live)
    expect(resolveVerdictDisplay({ pmf_score: 5.5 }).color).toBe(CARD_COLORS.accentBright)
    expect(resolveVerdictDisplay({ pmf_score: 2.1 }).color).toBe(CARD_COLORS.warn)
    expect(resolveVerdictDisplay({ pmf_score: 8.2 }).label).toBe('8.2/10')
  })

  it('renders a placeholder when nothing is known', () => {
    expect(resolveVerdictDisplay({}).label).toBe('—')
  })
})

describe('buildDotField', () => {
  it('is deterministic for a given seed', () => {
    expect(buildDotField(50, 7)).toEqual(buildDotField(50, 7))
  })

  it('differs across seeds', () => {
    expect(buildDotField(50, 7)).not.toEqual(buildDotField(50, 8))
  })

  it('keeps every dot inside the card bounds', () => {
    for (const d of buildDotField(200, 3)) {
      expect(d.x).toBeGreaterThanOrEqual(0)
      expect(d.x).toBeLessThanOrEqual(CARD_W)
      expect(d.y).toBeGreaterThanOrEqual(0)
      expect(d.y).toBeLessThanOrEqual(CARD_H)
    }
  })
})

describe('verdictMeta (shared lib)', () => {
  it('maps all three swarms', () => {
    expect(verdictMeta('ship_it').cls).toBe('is-ship')
    expect(verdictMeta('not_fundable').cls).toBe('is-kill')
    expect(verdictMeta('hold').cls).toBe('is-wrong')
  })

  it('falls back gracefully on unknown verdicts', () => {
    expect(verdictMeta('???')).toEqual({ label: '???', cls: 'is-sharpen' })
    expect(verdictMeta(undefined).label).toBe('—')
  })
})
