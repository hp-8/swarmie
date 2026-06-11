/**
 * Share-card PNG renderer — 1200×630 (OG ratio), drawn entirely client-side
 * on a plain <canvas>. No html2canvas, no backend, no new deps.
 *
 * Structure mirrors lib/pdf/template.js: the text-layout helpers are pure
 * functions (unit-testable without a real canvas — they take a `measure`
 * callback), and all 2D-context calls live in one thin draw function.
 *
 * Public surface:
 *   buildShareCardBlob(data) → Promise<{ canvas, blob }>   (browser only)
 *   downloadBlob(blob, filename)                            (browser only)
 *   drawShareCard(canvas, data) — accepts anything with getContext('2d')
 *
 * `data`: { verdict, pmf_score, confidence, agentCount,
 *           objectionCategory, objectionText, url }
 */

import { verdictMeta, VERDICT_HEX } from './verdict'

export const CARD_W = 1200
export const CARD_H = 630

// tokens.css → hex (same translation as the lib/pdf/template.js palette).
export const CARD_COLORS = {
  paper: '#101116',
  rule: '#383a44',
  ink: '#f6f7fa',
  ink2: '#d6dae0',
  ink3: '#a8acb8',
  ink4: '#7a7e8a',
  accent: '#f17a40',
  accentBright: '#f8924f',
  live: '#5fd99a',
  warn: '#ec5f5f',
  info: '#6aa9e4',
}

const ELLIPSIS = '…'
const PAD = 64
const MAX_TEXT_W = CARD_W - PAD * 2

const FONT_DISPLAY = 'Fraunces, Georgia, "Times New Roman", serif'
const FONT_MONO = '"JetBrains Mono", ui-monospace, SFMono-Regular, monospace'

// ---------------------------------------------------------------------------
// pure text-layout helpers (no canvas — `measure(str) → px` is injected)
// ---------------------------------------------------------------------------

/**
 * Greedy word-wrap. Words wider than maxWidth are hard-broken by character,
 * so a single unbroken 300-char token can't blow the layout.
 */
export function wrapLines(text, maxWidth, measure) {
  const words = String(text ?? '').trim().split(/\s+/).filter(Boolean)
  const lines = []
  let line = ''

  const flush = () => {
    if (line) lines.push(line)
    line = ''
  }

  for (const word of words) {
    if (measure(word) <= maxWidth) {
      const tryLine = line ? `${line} ${word}` : word
      if (measure(tryLine) <= maxWidth) line = tryLine
      else { flush(); line = word }
      continue
    }
    // oversized single word → hard-break by character
    flush()
    let rest = word
    while (rest.length > 0) {
      let take = 1
      while (take < rest.length && measure(rest.slice(0, take + 1)) <= maxWidth) take++
      lines.push(rest.slice(0, take))
      rest = rest.slice(take)
    }
    // pull the trailing fragment back so following words can join it
    line = lines.pop()
  }
  flush()
  return lines
}

/**
 * Wrap, then clamp to maxLines with a clean ellipsis on the final line.
 * Trailing space/punctuation stubs are stripped before the ellipsis so the
 * cut never reads "…,…".
 */
export function layoutText(text, { maxWidth, maxLines, measure }) {
  const lines = wrapLines(text, maxWidth, measure)
  if (lines.length <= maxLines) return lines
  const kept = lines.slice(0, maxLines)
  let last = kept[maxLines - 1]
  while (last.length > 1 && measure(last + ELLIPSIS) > maxWidth) last = last.slice(0, -1)
  kept[maxLines - 1] = last.replace(/[\s.,;:]+$/, '') + ELLIPSIS
  return kept
}

/**
 * Largest font size in [minSize, baseSize] at which `text` fits maxWidth.
 * `measureAt(size, text) → px`.
 */
export function fitFontSize(text, { maxWidth, baseSize, minSize, measureAt }) {
  let size = baseSize
  while (size > minSize && measureAt(size, text) > maxWidth) size -= 2
  return Math.max(size, minSize)
}

export function agentCountLine(n) {
  const v = Number(n) || 0
  return v > 0 ? `${v} synthetic users reacted` : 'synthetic swarm reacted'
}

export function confidenceLine(confidence) {
  return confidence ? `confidence · ${String(confidence)}` : ''
}

/**
 * Verdict → display label + concrete color. Falls back to the legacy
 * pmf_score for pre-verdict reports.
 */
export function resolveVerdictDisplay({ verdict, pmf_score } = {}) {
  if (verdict) {
    const meta = verdictMeta(verdict)
    return { label: meta.label, color: VERDICT_HEX[meta.cls] || CARD_COLORS.accentBright }
  }
  if (typeof pmf_score === 'number') {
    const color = pmf_score >= 7 ? CARD_COLORS.live
      : pmf_score >= 5 ? CARD_COLORS.accentBright
      : CARD_COLORS.warn
    return { label: `${pmf_score.toFixed(1)}/10`, color }
  }
  return { label: '—', color: CARD_COLORS.accentBright }
}

// mulberry32 — tiny seeded PRNG so the dot swarm is deterministic.
function mulberry32(seed) {
  let a = seed >>> 0
  return function () {
    a |= 0
    a = (a + 0x6D2B79F5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/**
 * Scattered dot-swarm motif — biased toward the top-right so it reads as a
 * swarm gathering, in brand colors (mostly ink, ~30% coral, a few phosphor).
 */
export function buildDotField(count = 110, seed = 7) {
  const rand = mulberry32(seed)
  const dots = []
  for (let i = 0; i < count; i++) {
    const x = CARD_W * (1 - Math.pow(rand(), 1.6))
    const y = CARD_H * Math.pow(rand(), 1.25)
    const roll = rand()
    dots.push({
      x,
      y,
      r: 1 + rand() * 2.6,
      color: roll < 0.30 ? CARD_COLORS.accent : roll < 0.38 ? CARD_COLORS.live : CARD_COLORS.ink3,
      alpha: 0.05 + rand() * 0.30,
      glow: roll < 0.06,
    })
  }
  return dots
}

// ---------------------------------------------------------------------------
// canvas drawing (thin layer over the helpers above)
// ---------------------------------------------------------------------------

/** Manual letter-spacing — ctx.letterSpacing isn't universally supported. */
function drawTracked(ctx, str, x, y, tracking) {
  let cx = x
  for (const ch of str) {
    ctx.fillText(ch, cx, y)
    cx += ctx.measureText(ch).width + tracking
  }
}

/**
 * Draw the full card onto `canvas` (resized to 1200×630).
 * Layout: wordmark + agent count → verdict block → top objection → URL bar.
 */
export function drawShareCard(canvas, data = {}) {
  canvas.width = CARD_W
  canvas.height = CARD_H
  const ctx = canvas.getContext('2d')
  const C = CARD_COLORS
  const verdict = resolveVerdictDisplay(data)
  const measure = (s) => ctx.measureText(s).width

  // --- paper ---
  ctx.fillStyle = C.paper
  ctx.fillRect(0, 0, CARD_W, CARD_H)

  // --- atmosphere: coral dawn top-right + faint cool counter-glow low-left ---
  let g = ctx.createRadialGradient(CARD_W * 0.86, -40, 0, CARD_W * 0.86, -40, 560)
  g.addColorStop(0, 'rgba(241, 122, 64, 0.14)')
  g.addColorStop(1, 'rgba(241, 122, 64, 0)')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, CARD_W, CARD_H)

  g = ctx.createRadialGradient(CARD_W * 0.10, CARD_H * 1.05, 0, CARD_W * 0.10, CARD_H * 1.05, 520)
  g.addColorStop(0, 'rgba(106, 169, 228, 0.07)')
  g.addColorStop(1, 'rgba(106, 169, 228, 0)')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, CARD_W, CARD_H)

  // --- dot swarm motif ---
  for (const d of buildDotField()) {
    ctx.globalAlpha = d.alpha
    ctx.fillStyle = d.color
    ctx.shadowColor = d.glow ? C.accent : 'transparent'
    ctx.shadowBlur = d.glow ? 14 : 0
    ctx.beginPath()
    ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 1
  ctx.shadowBlur = 0

  // vignette — edges fall away so the verdict holds the eye
  g = ctx.createRadialGradient(CARD_W / 2, CARD_H * 0.42, CARD_H * 0.30, CARD_W / 2, CARD_H * 0.42, CARD_W * 0.72)
  g.addColorStop(0, 'rgba(16, 17, 22, 0)')
  g.addColorStop(1, 'rgba(16, 17, 22, 0.55)')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, CARD_W, CARD_H)

  // --- top bar: wordmark left · agent count right ---
  ctx.shadowColor = C.accent
  ctx.shadowBlur = 16
  ctx.fillStyle = C.accent
  ctx.beginPath()
  ctx.arc(PAD + 7, 74, 7, 0, Math.PI * 2)
  ctx.fill()
  ctx.shadowBlur = 0

  ctx.fillStyle = C.ink
  ctx.font = `700 21px ${FONT_MONO}`
  drawTracked(ctx, 'SWARMIE', PAD + 28, 81, 5)

  ctx.fillStyle = C.ink3
  ctx.font = `500 16px ${FONT_MONO}`
  ctx.textAlign = 'right'
  ctx.fillText(agentCountLine(data.agentCount), CARD_W - PAD, 81)
  ctx.textAlign = 'left'

  // --- verdict block ---
  ctx.fillStyle = C.ink4
  ctx.font = `600 15px ${FONT_MONO}`
  drawTracked(ctx, 'THE SWARM’S VERDICT', PAD, 192, 4)

  const verdictLabel = verdict.label.toUpperCase()
  const verdictSize = fitFontSize(verdictLabel, {
    maxWidth: MAX_TEXT_W,
    baseSize: 116,
    minSize: 56,
    measureAt: (size, text) => {
      ctx.font = `italic 600 ${size}px ${FONT_DISPLAY}`
      return measure(text)
    },
  })
  ctx.font = `italic 600 ${verdictSize}px ${FONT_DISPLAY}`
  ctx.fillStyle = verdict.color
  ctx.shadowColor = verdict.color
  ctx.shadowBlur = 70
  ctx.fillText(verdictLabel, PAD, 304)
  ctx.shadowBlur = 28
  ctx.fillText(verdictLabel, PAD, 304)
  ctx.shadowBlur = 0

  const confLine = confidenceLine(data.confidence)
  if (confLine) {
    ctx.fillStyle = C.ink3
    ctx.font = `500 15px ${FONT_MONO}`
    drawTracked(ctx, confLine.toUpperCase(), PAD, 350, 3)
  }

  // --- top objection (wrapped + clamped, survives 300-char quotes) ---
  const objectionText = String(data.objectionText || '').trim()
  if (objectionText) {
    ctx.fillStyle = C.ink4
    ctx.font = `600 13px ${FONT_MONO}`
    const tag = data.objectionCategory
      ? `TOP OBJECTION · ${String(data.objectionCategory).toUpperCase()}`
      : 'TOP OBJECTION'
    drawTracked(ctx, tag, PAD, 414, 3)

    ctx.font = `italic 500 29px ${FONT_DISPLAY}`
    ctx.fillStyle = C.ink2
    const lines = layoutText(`“${objectionText}”`, {
      maxWidth: MAX_TEXT_W,
      maxLines: 3,
      measure,
    })
    lines.forEach((ln, i) => ctx.fillText(ln, PAD, 454 + i * 40))
  }

  // --- bottom bar: rule · URL · honest tag ---
  ctx.strokeStyle = C.rule
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(PAD, 560)
  ctx.lineTo(CARD_W - PAD, 560)
  ctx.stroke()

  ctx.fillStyle = C.accentBright
  ctx.font = `600 18px ${FONT_MONO}`
  ctx.fillText(data.url || 'swarmie.vercel.app', PAD, 596)

  ctx.fillStyle = C.ink4
  ctx.font = `500 14px ${FONT_MONO}`
  ctx.textAlign = 'right'
  ctx.fillText('synthetic users · disclosed', CARD_W - PAD, 596)
  ctx.textAlign = 'left'

  return canvas
}

// ---------------------------------------------------------------------------
// browser-only entry points
// ---------------------------------------------------------------------------

/** Render the card to a fresh canvas and return it with its PNG blob. */
export async function buildShareCardBlob(data) {
  // Best effort: make sure the display/mono webfonts are usable on canvas.
  if (typeof document !== 'undefined' && document.fonts) {
    try {
      await Promise.all([
        document.fonts.load('italic 600 116px Fraunces'),
        document.fonts.load('500 16px "JetBrains Mono"'),
        document.fonts.ready,
      ])
    } catch { /* fall back to system serif/mono */ }
  }
  const canvas = document.createElement('canvas')
  drawShareCard(canvas, data)
  const blob = await new Promise((resolve, reject) => {
    canvas.toBlob(
      (b) => (b ? resolve(b) : reject(new Error('canvas.toBlob returned null'))),
      'image/png',
    )
  })
  return { canvas, blob }
}

/** canvas.toBlob → object URL → <a download> click. */
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
