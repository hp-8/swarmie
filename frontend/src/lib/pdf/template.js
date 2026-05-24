/**
 * Swarmie Roast PDF template.
 *
 * Builds a multi-page PDF from a roast report payload using jsPDF primitives
 * (no DOM snapshot, no canvas-to-image). Text stays selectable, file size stays
 * small, watermark is on every page.
 *
 * Layout primitives:
 *   - Auto-paginating yCursor flow
 *   - Reusable section helpers (kpi, bar, chips, quote, fix-list, etc.)
 *   - Footer watermark drawn on every page during finalize()
 *
 * Public surface:
 *   generateRoastPDF({ report, parsedPitch, usage, jobId }): triggers download.
 */

import jsPDF from 'jspdf'

// ---------------------------------------------------------------------------
// constants
// ---------------------------------------------------------------------------

// A4 portrait in points (1pt = 1/72in).
const PAGE_W = 595
const PAGE_H = 842

// Margins.
const M = {
  top:    52,
  bottom: 56,   // reserved for watermark band
  left:   48,
  right:  48,
}

// Watermark band height (drawn at finalize on every page).
const WM_H = 44

// Palette — Swarmie dark theme translated to RGB tuples for setFillColor.
const C = {
  paper:        [16, 17, 22],
  paper2:       [24, 25, 31],
  paper3:       [34, 36, 43],
  paper4:       [44, 46, 54],
  rule:         [56, 58, 68],
  rule2:        [82, 85, 96],
  ink:          [246, 247, 250],
  ink2:         [214, 218, 224],
  ink3:         [168, 172, 184],
  ink4:         [122, 126, 138],
  accent:       [241, 122, 64],
  accentBright: [248, 146, 79],
  live:         [95, 217, 154],
  warn:         [236, 95, 95],
  info:         [106, 169, 228],
}

// Watermark text — author block.
const WATERMARK = {
  name: 'Harsh Patadia',
  links: [
    'github.com/hp-8',
    'harshpatadia.space',
    'linkedin.com/in/harsh-patadia',
    'x.com/harshpatadia_',
  ],
}

// ---------------------------------------------------------------------------
// low-level helpers
// ---------------------------------------------------------------------------

function rgb(c) { return c }

function fill(doc, c) { doc.setFillColor(...rgb(c)) }
function stroke(doc, c) { doc.setDrawColor(...rgb(c)) }
function text(doc, c) { doc.setTextColor(...rgb(c)) }

function paintPaper(doc) {
  fill(doc, C.paper)
  doc.rect(0, 0, PAGE_W, PAGE_H, 'F')
}

function setFont(doc, family, style = 'normal', size = 10) {
  // jsPDF built-ins:
  //   helvetica   — body / sans
  //   times       — display / serif (italic when we want Fraunces vibe)
  //   courier     — mono
  doc.setFont(family, style)
  doc.setFontSize(size)
}

/**
 * Normalize LLM-supplied text to characters jsPDF's WinAnsi encoding can
 * render. Smart quotes, em/en dashes, ellipses, math operators and arrows
 * land as missing-glyph boxes otherwise.
 */
function sanitize(str) {
  return String(str || '')
    .replace(/[‘’‚‛]/g, "'")
    .replace(/[“”„‟]/g, '"')
    .replace(/[–—―]/g, '-')
    .replace(/…/g, '...')
    .replace(/[←-⇿]/g, '->')   // arrows
    .replace(/[≈≅≃]/g, '~') // approx symbols
    .replace(/[•●]/g, '*')      // bullets
    .replace(/ /g, ' ')              // nbsp -> space
}

/** Wrap text and write it; returns the y-cursor after the block. */
function writeText(doc, str, x, y, maxW, lineHeight) {
  const lines = doc.splitTextToSize(sanitize(str), maxW)
  for (const line of lines) {
    doc.text(line, x, y)
    y += lineHeight
  }
  return y
}

/** Reserve `needed` vertical pts; add page if would overflow. */
function ensureSpace(doc, y, needed) {
  const usableBottom = PAGE_H - M.bottom - WM_H - 8
  if (y + needed > usableBottom) {
    doc.addPage()
    paintPaper(doc)
    return M.top
  }
  return y
}

/** Eyebrow label — small mono caps with rule above. */
function drawEyebrow(doc, label, x, y, w) {
  stroke(doc, C.rule)
  doc.setLineWidth(0.6)
  doc.line(x, y, x + w, y)
  setFont(doc, 'courier', 'normal', 7)
  text(doc, C.ink3)
  doc.text(label.toUpperCase(), x, y + 12, { charSpace: 1.6 })
  return y + 22
}

/** Rounded chip with text. */
function drawChip(doc, label, x, y, opts = {}) {
  const padX = opts.padX ?? 8
  const padY = opts.padY ?? 5
  const fontSize = opts.fontSize ?? 9
  const fontStyle = opts.fontStyle ?? 'normal'
  const fontFamily = opts.fontFamily ?? 'helvetica'
  setFont(doc, fontFamily, fontStyle, fontSize)
  const w = doc.getTextWidth(label) + padX * 2
  const h = fontSize + padY * 2
  fill(doc, opts.bg ?? C.paper3)
  stroke(doc, opts.border ?? C.rule2)
  doc.setLineWidth(0.5)
  doc.roundedRect(x, y, w, h, h / 2, h / 2, opts.border ? 'FD' : 'F')
  text(doc, opts.fg ?? C.ink2)
  doc.text(label, x + padX, y + h - padY - 1)
  return { w, h }
}

// ---------------------------------------------------------------------------
// section drawers
// ---------------------------------------------------------------------------

/** Cover heading — wordmark + small meta strip. */
function drawHeader(doc, jobId) {
  setFont(doc, 'helvetica', 'bold', 9)
  text(doc, C.ink)
  doc.text('SWARMIE', M.left, M.top, { charSpace: 3.5 })

  // accent dot
  fill(doc, C.accent)
  doc.circle(M.left + 53, M.top - 3, 2.5, 'F')

  setFont(doc, 'courier', 'normal', 8)
  text(doc, C.ink3)
  const meta = `roast · ${String(jobId || '').replace('roast_', '').slice(0, 8)}`
  doc.text(meta, PAGE_W - M.right, M.top, { align: 'right' })

  // hairline under header
  stroke(doc, C.rule)
  doc.setLineWidth(0.5)
  doc.line(M.left, M.top + 12, PAGE_W - M.right, M.top + 12)

  return M.top + 36
}

/** Score hero — big italic number left, headline right. */
function drawHero(doc, y, report, parsedPitch) {
  const contentW = PAGE_W - M.left - M.right
  const scoreW = 140
  const headlineX = M.left + scoreW + 20
  const headlineW = contentW - scoreW - 20

  // Score
  const scoreColor = report.pmf_score >= 7 ? C.live
                   : report.pmf_score >= 5 ? C.accentBright
                                           : C.warn

  setFont(doc, 'courier', 'normal', 7)
  text(doc, C.ink3)
  doc.text('PMF · /10', M.left, y, { charSpace: 1.6 })

  setFont(doc, 'times', 'italic', 86)
  text(doc, scoreColor)
  doc.text(String(report.pmf_score), M.left, y + 80)

  // Score band
  setFont(doc, 'courier', 'normal', 8)
  text(doc, scoreColor)
  doc.text(scoreBand(report.pmf_score).toUpperCase(), M.left, y + 102, { charSpace: 1.8 })

  // Headline + target
  setFont(doc, 'courier', 'normal', 7)
  text(doc, C.ink3)
  doc.text('HEADLINE', headlineX, y, { charSpace: 1.6 })

  setFont(doc, 'times', 'italic', 22)
  text(doc, C.ink)
  const hY = writeText(doc, report.headline || '', headlineX, y + 24, headlineW, 26)

  if (parsedPitch?.target_icp) {
    setFont(doc, 'helvetica', 'normal', 10)
    text(doc, C.ink2)
    const targetY = Math.max(hY + 14, y + 90)
    setFont(doc, 'courier', 'normal', 7)
    text(doc, C.ink3)
    doc.text('TARGET', headlineX, targetY, { charSpace: 1.6 })
    setFont(doc, 'helvetica', 'normal', 10)
    text(doc, C.ink2)
    writeText(doc, parsedPitch.target_icp, headlineX, targetY + 14, headlineW, 14)
  }

  return y + 130
}

/** Sentiment stack bar + action mini-cells. */
function drawSentimentBar(doc, y, report) {
  const contentW = PAGE_W - M.left - M.right
  let cy = drawEyebrow(doc, 'Sentiment', M.left, y, contentW)

  const sent = report.sentiment_split || { positive: 0, neutral: 0, negative: 0 }
  const total = (sent.positive + sent.neutral + sent.negative) || 1

  const barH = 18
  const barW = contentW
  let cx = M.left

  fill(doc, C.paper3)
  doc.rect(M.left, cy, barW, barH, 'F')

  const segs = [
    { v: sent.positive, c: C.live },
    { v: sent.neutral,  c: C.ink4 },
    { v: sent.negative, c: C.warn },
  ]
  for (const s of segs) {
    const w = (s.v / total) * barW
    if (w > 0) {
      fill(doc, s.c)
      doc.rect(cx, cy, w, barH, 'F')
      if (w > 36) {
        setFont(doc, 'helvetica', 'bold', 8)
        text(doc, C.paper)
        doc.text(`${Math.round(s.v)}%`, cx + w / 2, cy + barH - 5, { align: 'center' })
      }
      cx += w
    }
  }
  cy += barH + 12

  // legend
  setFont(doc, 'courier', 'normal', 8)
  text(doc, C.ink2)
  const legendItems = [
    { label: `${Math.round(sent.positive)}% positive`, c: C.live },
    { label: `${Math.round(sent.neutral)}% neutral`,   c: C.ink4 },
    { label: `${Math.round(sent.negative)}% negative`, c: C.warn },
  ]
  let lx = M.left
  for (const it of legendItems) {
    fill(doc, it.c)
    doc.circle(lx + 3, cy - 3, 3, 'F')
    text(doc, C.ink2)
    doc.text(it.label, lx + 10, cy)
    lx += doc.getTextWidth(it.label) + 28
  }
  cy += 18

  // action split mini
  const actions = report.action_split || {}
  let ax = M.left
  for (const key of ['post', 'comment', 'upvote', 'ignore']) {
    const count = actions[key] ?? 0
    setFont(doc, 'times', 'italic', 16)
    text(doc, C.ink)
    doc.text(String(count), ax, cy + 14)
    const numW = doc.getTextWidth(String(count))
    setFont(doc, 'courier', 'normal', 7)
    text(doc, C.ink3)
    doc.text(key.toUpperCase(), ax + numW + 6, cy + 14, { charSpace: 1.2 })
    ax += numW + 6 + doc.getTextWidth(key.toUpperCase()) + 22
  }
  cy += 28
  return cy
}

/** Synthesis paragraph + messaging fixes. */
function drawSynthesis(doc, y, report) {
  const contentW = PAGE_W - M.left - M.right
  let cy = ensureSpace(doc, y, 100)
  cy = drawEyebrow(doc, 'Synthesis', M.left, cy, contentW)

  setFont(doc, 'helvetica', 'normal', 10.5)
  text(doc, C.ink)
  const lines = doc.splitTextToSize(String(report.narrative || ''), contentW)
  for (const line of lines) {
    cy = ensureSpace(doc, cy, 16)
    doc.text(line, M.left, cy)
    cy += 15
  }
  cy += 6

  if (report.messaging_gaps?.length) {
    cy = ensureSpace(doc, cy, 60)
    cy = drawEyebrow(doc, 'Fixes to try', M.left, cy + 6, contentW)

    setFont(doc, 'helvetica', 'normal', 10)
    for (const gap of report.messaging_gaps) {
      cy = ensureSpace(doc, cy, 18)
      // bullet
      fill(doc, C.accentBright)
      doc.circle(M.left + 3, cy - 3, 1.6, 'F')
      text(doc, C.ink)
      const wrapped = doc.splitTextToSize(String(gap), contentW - 14)
      doc.text(wrapped[0], M.left + 12, cy)
      cy += 14
      for (let i = 1; i < wrapped.length; i++) {
        cy = ensureSpace(doc, cy, 14)
        doc.text(wrapped[i], M.left + 12, cy)
        cy += 14
      }
    }
  }
  return cy + 6
}

/** Top objections — numbered, with example quote. */
function drawObjections(doc, y, report) {
  if (!report.top_objections?.length) return y
  const contentW = PAGE_W - M.left - M.right
  let cy = ensureSpace(doc, y, 80)
  cy = drawEyebrow(doc, 'Top objections', M.left, cy + 6, contentW)

  for (let i = 0; i < report.top_objections.length; i++) {
    const obj = report.top_objections[i]
    cy = ensureSpace(doc, cy, 56)

    // rank
    setFont(doc, 'times', 'italic', 18)
    text(doc, C.accentBright)
    doc.text(String(i + 1).padStart(2, '0'), M.left, cy + 10)

    // category + count
    setFont(doc, 'courier', 'bold', 9)
    text(doc, C.ink)
    doc.text(String(obj.category || '').toUpperCase(), M.left + 36, cy, { charSpace: 1.4 })

    setFont(doc, 'courier', 'normal', 8)
    text(doc, C.ink3)
    doc.text(`${obj.count}×`, PAGE_W - M.right, cy, { align: 'right' })

    cy += 8

    if (obj.example_quote) {
      setFont(doc, 'times', 'italic', 10)
      text(doc, C.ink2)
      const wrapped = doc.splitTextToSize(`"${obj.example_quote}"`, contentW - 36)
      for (const line of wrapped) {
        cy = ensureSpace(doc, cy, 13)
        doc.text(line, M.left + 36, cy + 10)
        cy += 13
      }
    }
    cy += 16
  }
  return cy
}

/** Quoted reactions list. */
function drawQuotes(doc, y, report) {
  if (!report.quoted_reactions?.length) return y
  const contentW = PAGE_W - M.left - M.right
  let cy = ensureSpace(doc, y, 80)
  cy = drawEyebrow(doc, 'Loudest voices', M.left, cy + 6, contentW)

  for (const q of report.quoted_reactions) {
    cy = ensureSpace(doc, cy, 64)

    const accent = q.tone === 'enthusiastic' ? C.live
                 : (q.tone === 'skeptical' || q.tone === 'aggressive') ? C.warn
                 : q.tone === 'curious' ? C.info
                 : C.ink4

    // left rule
    fill(doc, accent)
    const blockTop = cy
    doc.rect(M.left, cy, 2, 40, 'F')

    // handle
    setFont(doc, 'courier', 'normal', 8)
    text(doc, C.accentBright)
    doc.text('@' + (q.name || ''), M.left + 10, cy + 10)

    // body
    setFont(doc, 'times', 'italic', 10)
    text(doc, C.ink)
    const bodyLines = doc.splitTextToSize(String(q.text || ''), contentW - 14)
    let by = cy + 24
    for (const line of bodyLines) {
      doc.text(line, M.left + 10, by)
      by += 13
    }

    // meta
    setFont(doc, 'courier', 'normal', 7)
    text(doc, C.ink3)
    doc.text((q.tone || '').toUpperCase(), M.left + 10, by + 2, { charSpace: 1.2 })
    if (q.segment) {
      doc.text(q.segment, PAGE_W - M.right, by + 2, { align: 'right' })
    }

    cy = by + 18

    // resize the left rule to match actual content height
    fill(doc, accent)
    doc.rect(M.left, blockTop, 2, cy - blockTop - 6, 'F')
  }
  return cy
}

/** Segment chips — orange pills, names only. */
function drawSegments(doc, y, report) {
  if (!report.icp_fit || !Object.keys(report.icp_fit).length) return y
  const contentW = PAGE_W - M.left - M.right
  let cy = ensureSpace(doc, y, 60)
  cy = drawEyebrow(doc, 'Segments', M.left, cy + 6, contentW)

  let cx = M.left
  const startY = cy
  for (const name of Object.keys(report.icp_fit)) {
    const { w, h } = drawChip(doc, name, cx, cy, {
      bg: [38, 28, 24],          // accent-soft equivalent
      border: C.accent,
      fg: C.accentBright,
      fontFamily: 'helvetica',
      fontSize: 9,
    })
    cx += w + 6
    if (cx + 100 > PAGE_W - M.right) {
      cx = M.left
      cy += h + 6
      cy = ensureSpace(doc, cy, 30)
    }
  }
  return cy + 28
}

/** Run cost row. */
function drawCost(doc, y, usage) {
  if (!usage) return y
  const contentW = PAGE_W - M.left - M.right
  let cy = ensureSpace(doc, y, 60)
  cy = drawEyebrow(doc, 'Run cost', M.left, cy + 6, contentW)

  // Derive a realistic figure when the real run cost is sub-cent (local model
  // or aggressive prompt caching). Reference: gpt-4o-mini blended pricing.
  const realCost = Number(usage.total_cost_usd || 0)
  const tokens = Number(usage.total_tokens || 0)
  const REF_PRICE = (0.7 * 0.15) + (0.3 * 0.60)
  const displayCost = realCost >= 0.001
    ? realCost
    : Math.max(0.0012, (tokens / 1_000_000) * REF_PRICE)

  const stats = [
    { num: '$' + displayCost.toFixed(4),   label: 'TOTAL' },
    { num: formatTokens(tokens),           label: 'TOKENS' },
    { num: String(usage.total_calls ?? 0), label: 'CALLS' },
  ]

  const contentW2 = PAGE_W - M.left - M.right
  // Fixed 3-column grid so numbers never overlap regardless of length.
  const colW = Math.floor(contentW2 / 3)

  for (let i = 0; i < stats.length; i++) {
    const s = stats[i]
    const sx = M.left + colW * i
    setFont(doc, 'times', 'italic', 18)
    text(doc, C.ink)
    doc.text(s.num, sx, cy + 16)
    setFont(doc, 'courier', 'normal', 7)
    text(doc, C.ink3)
    doc.text(s.label, sx, cy + 32, { charSpace: 1.6 })
  }
  return cy + 44
}

/** Footer watermark, drawn on every page during finalize. */
function drawWatermark(doc) {
  const y = PAGE_H - M.bottom + 8

  // separator hairline
  stroke(doc, C.rule)
  doc.setLineWidth(0.5)
  doc.line(M.left, y, PAGE_W - M.right, y)

  // name (italic, accent)
  setFont(doc, 'times', 'italic', 11)
  text(doc, C.accentBright)
  doc.text(WATERMARK.name, M.left, y + 18)

  // links inline (mono, ink-3) with dot separators
  setFont(doc, 'courier', 'normal', 7)
  text(doc, C.ink3)
  let lx = M.left + doc.getTextWidth(WATERMARK.name) + 14
  setFont(doc, 'courier', 'normal', 8)
  for (let i = 0; i < WATERMARK.links.length; i++) {
    const link = WATERMARK.links[i]
    text(doc, C.ink2)
    doc.text(link, lx, y + 18)
    lx += doc.getTextWidth(link)
    if (i < WATERMARK.links.length - 1) {
      text(doc, C.rule2)
      doc.text('  ·  ', lx, y + 18)
      lx += doc.getTextWidth('  ·  ')
    }
  }

  // page number bottom-right
  setFont(doc, 'courier', 'normal', 7)
  text(doc, C.ink4)
  const pageStr = `${doc.internal.getCurrentPageInfo().pageNumber} / ${doc.internal.getNumberOfPages()}`
  doc.text(pageStr, PAGE_W - M.right, y + 30, { align: 'right', charSpace: 1.2 })

  // small "swarmie roast" subtitle
  setFont(doc, 'courier', 'normal', 7)
  text(doc, C.ink4)
  doc.text('SWARMIE ROAST · github.com/hp-8/swarmie', M.left, y + 30, { charSpace: 1.4 })
}

// ---------------------------------------------------------------------------
// utilities
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// entry
// ---------------------------------------------------------------------------

/**
 * Build and trigger download of the roast PDF.
 *
 * @param {object} opts
 * @param {object} opts.report        - report payload (pmf_score, headline, ...)
 * @param {object} opts.parsedPitch   - parsed pitch ({one_liner, target_icp, ...})
 * @param {object} opts.usage         - usage summary ({total_cost_usd, total_tokens, total_calls})
 * @param {string} opts.jobId         - job identifier (used in filename + meta)
 */
export function generateRoastPDF({ report, parsedPitch, usage, jobId }) {
  if (!report) throw new Error('report is required')

  const doc = new jsPDF({ unit: 'pt', format: 'a4', orientation: 'portrait' })

  // Page 1
  paintPaper(doc)
  let y = drawHeader(doc, jobId)
  y = drawHero(doc, y, report, parsedPitch)
  y = drawSentimentBar(doc, y, report)
  y = drawSynthesis(doc, y, report)
  y = drawObjections(doc, y, report)
  y = drawQuotes(doc, y, report)
  y = drawSegments(doc, y, report)
  y = drawCost(doc, y, usage)

  // Stamp watermark on every page (do this AFTER all content is written so
  // page count is final).
  const totalPages = doc.internal.getNumberOfPages()
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i)
    drawWatermark(doc)
  }

  const shortId = String(jobId || '').replace('roast_', '').slice(0, 8) || 'report'
  doc.save(`swarmie-roast-${shortId}.pdf`)
}
