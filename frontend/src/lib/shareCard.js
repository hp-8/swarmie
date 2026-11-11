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
 * `data`: { verdict, pmf_score, confidence, agentCount, riskTitle, riskWhy,
 *           objectionCategory, objectionText, url }
 * Shows the memo's top hidden risk; falls back to the top objection for
 * reports without hidden risks (pre-V2).
 */

import { recPhrase, verdictMeta, VERDICT_HEX } from './verdict'

export const CARD_W = 1200
export const CARD_H = 630

// tokens.css (V2 light memo) → hex for canvas, which can't read CSS vars.
export const CARD_COLORS = {
  paper: '#ffffff',
  paper2: '#f6f7f9',
  rule: '#e3e6ea',
  ink: '#1d2127',
  ink2: '#3d434c',
  ink3: '#5f6773',
  accentBright: '#9a5b13', // sharpen / middling
  live: '#2b7a4b',
  warn: '#bf2f2a',
}

const ELLIPSIS = '…'
const PAD = 64
const MAX_TEXT_W = CARD_W - PAD * 2

const FONT_DISPLAY = '"Source Serif 4", Georgia, "Times New Roman", serif'
const FONT_SANS = '"Public Sans", system-ui, -apple-system, "Segoe UI", sans-serif'
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
  return v > 0 ? `${v} reviewer${v === 1 ? '' : 's'}` : 'synthetic panel'
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
 * Layout: wordmark + memo meta → verdict sentence → top risk (or objection) → URL bar.
 */
export function drawShareCard(canvas, data = {}) {
  canvas.width = CARD_W
  canvas.height = CARD_H
  const ctx = canvas.getContext('2d')
  const C = CARD_COLORS
  const verdict = resolveVerdictDisplay(data)
  const measure = (s) => ctx.measureText(s).width

  ctx.fillStyle = C.paper
  ctx.fillRect(0, 0, CARD_W, CARD_H)

  // --- header: logo + wordmark · memo meta ---
  drawLogo(ctx, PAD, 52, 36)
  ctx.fillStyle = C.ink
  ctx.font = `700 26px ${FONT_SANS}`
  ctx.fillText('Swarmie', PAD + 50, 79)

  ctx.fillStyle = C.ink3
  ctx.font = `500 14px ${FONT_MONO}`
  const meta = `DECISION MEMO · ${agentCountLine(data.agentCount).toUpperCase()}`
  drawTrackedRight(ctx, meta, CARD_W - PAD, 78, 2)

  hRule(ctx, 116)

  // --- verdict: colored marker + memo sentence ---
  ctx.fillStyle = verdict.color
  ctx.beginPath()
  ctx.arc(PAD + 6, 166, 6, 0, Math.PI * 2)
  ctx.fill()
  ctx.font = `600 13px ${FONT_MONO}`
  drawTracked(ctx, 'VERDICT', PAD + 22, 171, 3)
  const confLine = confidenceLine(data.confidence)
  if (confLine) {
    ctx.fillStyle = C.ink3
    ctx.font = `500 13px ${FONT_MONO}`
    drawTracked(ctx, `· ${confLine.toUpperCase()}`, PAD + 104, 171, 2)
  }

  const phrase = data.verdict ? recPhrase(data.verdict) : verdict.label
  const phraseSize = fitFontSize(phrase, {
    maxWidth: MAX_TEXT_W,
    baseSize: 68,
    minSize: 40,
    measureAt: (size, text) => {
      ctx.font = `600 ${size}px ${FONT_DISPLAY}`
      return measure(text)
    },
  })
  ctx.font = `600 ${phraseSize}px ${FONT_DISPLAY}`
  ctx.fillStyle = C.ink
  ctx.fillText(phrase, PAD, 248)

  // --- finding panel: top hidden risk, else top objection ---
  const risk = String(data.riskTitle || '').trim()
  const quote = String(data.objectionText || '').trim()
  if (risk || quote) {
    const top = 296
    const x = PAD + 32
    const w = MAX_TEXT_W - 64
    // Lay text out first so the panel can hug it: [font, color, lines, lineHeight]
    const blocks = []
    let flag
    if (risk) {
      flag = 'RISK'
      ctx.font = `700 30px ${FONT_SANS}`
      const title = layoutText(risk, { maxWidth: w, maxLines: 2, measure })
      blocks.push([ctx.font, C.ink, title, 38])
      const why = String(data.riskWhy || '').trim()
      if (why) {
        ctx.font = `400 20px ${FONT_SANS}`
        const maxLines = title.length > 1 ? 1 : 2
        blocks.push([ctx.font, C.ink2, layoutText(`Easy to miss because ${lowerFirst(why)}`, { maxWidth: w, maxLines, measure }), 28])
      }
    } else {
      flag = data.objectionCategory
        ? `OBJECTION · ${String(data.objectionCategory).toUpperCase()}`
        : 'OBJECTION'
      ctx.font = `italic 500 28px ${FONT_DISPLAY}`
      blocks.push([ctx.font, C.ink2, layoutText(`“${quote}”`, { maxWidth: w, maxLines: 3, measure }), 38])
    }

    // Baselines: first title line 98px under the panel top, each next line
    // one line-height down, +10px between blocks.
    const rows = []
    let y = top + 98
    blocks.forEach(([font, color, lines, lh], i) => {
      if (i) y += 10 + lh
      lines.forEach((ln, j) => rows.push([font, color, ln, y + j * lh]))
      y += (lines.length - 1) * lh
    })
    const bottom = Math.min(y + 32, 536) // keep clear of the footer rule at 556
    ctx.fillStyle = C.paper2
    roundRect(ctx, PAD, top, MAX_TEXT_W, bottom - top, 12)
    ctx.fill()

    drawFlag(ctx, flag, x, top + 34)
    for (const [font, color, ln, by] of rows) {
      ctx.font = font
      ctx.fillStyle = color
      ctx.fillText(ln, x, by)
    }
  }

  // --- footer: rule · URL · disclosure ---
  hRule(ctx, 556)
  ctx.fillStyle = C.ink
  ctx.font = `500 18px ${FONT_MONO}`
  ctx.fillText(data.url || 'swarmie.harshpatadia.com', PAD, 594)
  ctx.fillStyle = C.ink3
  ctx.font = `400 16px ${FONT_SANS}`
  ctx.textAlign = 'right'
  ctx.fillText('AI reviewers, not real users', CARD_W - PAD, 594)
  ctx.textAlign = 'left'

  return canvas
}

function lowerFirst(s) {
  return s ? s.charAt(0).toLowerCase() + s.slice(1) : s
}

function hRule(ctx, y) {
  ctx.strokeStyle = CARD_COLORS.rule
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(PAD, y + 0.5)
  ctx.lineTo(CARD_W - PAD, y + 0.5)
  ctx.stroke()
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.arcTo(x + w, y, x + w, y + h, r)
  ctx.arcTo(x + w, y + h, x, y + h, r)
  ctx.arcTo(x, y + h, x, y, r)
  ctx.arcTo(x, y, x + w, y, r)
  ctx.closePath()
}

function trackedWidth(ctx, str, tracking) {
  let w = 0
  for (const ch of str) w += ctx.measureText(ch).width + tracking
  return w - tracking
}

// Outlined mono tag, like the memo's "Risk" flag.
function drawFlag(ctx, label, x, y) {
  ctx.font = `600 13px ${FONT_MONO}`
  const w = trackedWidth(ctx, label, 2)
  ctx.strokeStyle = CARD_COLORS.warn
  ctx.lineWidth = 1.5
  roundRect(ctx, x, y - 18, w + 18, 28, 5)
  ctx.stroke()
  ctx.fillStyle = CARD_COLORS.warn
  drawTracked(ctx, label, x + 9, y + 1, 2)
}

function drawTrackedRight(ctx, str, right, y, tracking) {
  drawTracked(ctx, str, right - trackedWidth(ctx, str, tracking), y, tracking)
}

// The favicon mark: four colored nodes wired to a coral core.
function drawLogo(ctx, x, y, size) {
  const p = (v) => (v * size) / 120
  ctx.strokeStyle = 'rgba(25, 24, 20, 0.6)'
  ctx.lineWidth = p(3)
  for (const [ex, ey] of [[28, 42], [92, 42], [28, 82], [92, 82]]) {
    ctx.beginPath()
    ctx.moveTo(x + p(60), y + p(60))
    ctx.lineTo(x + p(ex), y + p(ey))
    ctx.stroke()
  }
  const dots = [[60, 60, 22, '#ff6b35'], [28, 42, 9, '#2d6ef7'], [92, 42, 9, '#15c1a3'], [28, 82, 9, '#ffc94f'], [92, 82, 9, '#ff5da2']]
  for (const [cx, cy, r, fill] of dots) {
    ctx.fillStyle = fill
    ctx.beginPath()
    ctx.arc(x + p(cx), y + p(cy), p(r), 0, Math.PI * 2)
    ctx.fill()
  }
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
        document.fonts.load('600 68px "Source Serif 4"'),
        document.fonts.load('italic 500 28px "Source Serif 4"'),
        document.fonts.load('700 30px "Public Sans"'),
        document.fonts.load('400 20px "Public Sans"'),
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
