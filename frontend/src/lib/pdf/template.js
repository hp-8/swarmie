/**
 * Swarmie decision-memo PDF.
 *
 * Mirrors the V2 result page (components/swarm/DecisionMemo.vue) on A4 with
 * jsPDF primitives: white paper, ink text, serif verdict, red used only as a
 * highlight behind risk flags. Text stays selectable and the file small.
 *
 * Flow: header → subject + panel facts → verdict → action panel (this week,
 * branches, rewording) → what's working → hidden risks → objections →
 * evidence (sentiment, why people scrolled past, segments) → voices →
 * summary, plus deck diagnosis / launch brief when present. Run cost sits
 * in the header facts.
 * A footer with the disclosure and page number goes on every page.
 *
 * Public surface: generateRoastPDF({ report, parsedPitch, usage, jobId }).
 */

import { recPhrase, verdictMeta } from '../verdict'

// jsPDF is imported dynamically in generateRoastPDF so it is only fetched
// when someone clicks "Download PDF".

// A4 portrait in points.
const PAGE_W = 595
const PAGE_H = 842
const M = { top: 50, bottom: 54, left: 50, right: 50 }
const CW = PAGE_W - M.left - M.right

// tokens.css (light) as RGB.
const C = {
  paper: [255, 255, 255],
  paper2: [246, 247, 249],
  paper3: [236, 238, 242],
  rule: [227, 230, 234],
  rule2: [203, 208, 214],
  ink: [29, 33, 39],
  ink2: [61, 67, 76],
  ink3: [95, 103, 115],
  ink4: [122, 129, 140],
  live: [43, 122, 75],
  warn: [191, 47, 42],
  warnHl: [247, 212, 206],
  logo: { core: [255, 107, 53], a: [45, 110, 247], b: [21, 193, 163], c: [255, 201, 79], d: [255, 93, 162] },
}

const SERIF = 'times'
const SANS = 'helvetica'

// ---------------------------------------------------------------------------
// primitives
// ---------------------------------------------------------------------------

const fill = (doc, c) => doc.setFillColor(...c)
const stroke = (doc, c) => doc.setDrawColor(...c)
const ink = (doc, c) => doc.setTextColor(...c)
const font = (doc, family, style, size) => { doc.setFont(family, style); doc.setFontSize(size) }

/** jsPDF's built-in fonts are WinAnsi: map typographic characters it can't draw. */
export function sanitize(str) {
  return String(str ?? '')
    .replace(/[‘’‚‛]/g, "'")
    .replace(/[“”„‟]/g, '"')
    .replace(/[–—―]/g, '-')
    .replace(/…/g, '...')
    .replace(/[←-⇿]/g, '->')
    .replace(/[≈≅≃]/g, '~')
    .replace(/[•●]/g, '*')
    .replace(/00A0/g, ' ')
}

const lines = (doc, str, w) => doc.splitTextToSize(sanitize(str), w)
const cap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : '')

/** Flowing page cursor: adds a page when a block would cross the footer. */
function makeFlow(doc) {
  const flow = {
    y: M.top,
    need(h) {
      if (flow.y + h > PAGE_H - M.bottom) {
        doc.addPage()
        flow.y = M.top
      }
    },
  }
  return flow
}

/** Write wrapped text at x; returns the y after the last line. */
function para(doc, flow, str, { x = M.left, w = CW, size = 10, lh = 1.45, family = SANS, style = 'normal', color = C.ink2 } = {}) {
  if (!str) return flow.y
  font(doc, family, style, size)
  ink(doc, color)
  for (const ln of lines(doc, str, w)) {
    flow.need(size * lh)
    doc.text(ln, x, flow.y + size)
    flow.y += size * lh
  }
  return flow.y
}

function heading(doc, flow, label, gapAbove = 16) {
  flow.need(gapAbove + 34)
  flow.y += gapAbove
  stroke(doc, C.rule)
  doc.setLineWidth(0.6)
  doc.line(M.left, flow.y, M.left + CW, flow.y)
  flow.y += 14
  font(doc, SANS, 'bold', 11.5)
  ink(doc, C.ink)
  doc.text(sanitize(label), M.left, flow.y + 9)
  flow.y += 20
}

/** Small label on a red highlight, like the memo's "Risk" flag. Returns its width. */
function flag(doc, label, x, baseline) {
  font(doc, SANS, 'bold', 7)
  const w = doc.getTextWidth(label) + 8
  fill(doc, C.warnHl)
  doc.roundedRect(x, baseline - 7.5, w, 10.5, 1.5, 1.5, 'F')
  ink(doc, C.ink)
  doc.text(label, x + 4, baseline)
  return w
}

function bullets(doc, flow, items, marker = C.ink3, { x = M.left, w = CW, size = 9.5 } = {}) {
  for (const it of items || []) {
    font(doc, SANS, 'normal', size)
    const ls = lines(doc, it, w - 12)
    flow.need(ls.length * size * 1.45 + 4)
    fill(doc, marker)
    doc.circle(x + 2.5, flow.y + size * 0.62, 1.5, 'F')
    ink(doc, C.ink2)
    ls.forEach((ln, i) => doc.text(ln, x + 12, flow.y + size + i * size * 1.45))
    flow.y += ls.length * size * 1.45 + 4
  }
}

function hbar(doc, x, y, w, pct, color) {
  fill(doc, C.paper3)
  doc.roundedRect(x, y, w, 4, 2, 2, 'F')
  const fw = Math.max(0, Math.min(1, (Number(pct) || 0) / 100)) * w
  if (fw > 0) { fill(doc, color); doc.roundedRect(x, y, fw, 4, 2, 2, 'F') }
}

// ---------------------------------------------------------------------------
// sections
// ---------------------------------------------------------------------------

function drawLogo(doc, x, y, s) {
  const p = (v) => (v * s) / 120
  stroke(doc, [120, 120, 118])
  doc.setLineWidth(p(3))
  for (const [ex, ey] of [[28, 42], [92, 42], [28, 82], [92, 82]]) doc.line(x + p(60), y + p(60), x + p(ex), y + p(ey))
  const L = C.logo
  for (const [cx, cy, r, col] of [[60, 60, 22, L.core], [28, 42, 9, L.a], [92, 42, 9, L.b], [28, 82, 9, L.c], [92, 82, 9, L.d]]) {
    fill(doc, col)
    doc.circle(x + p(cx), y + p(cy), p(r), 'F')
  }
}

function drawHeader(doc, flow, { report, parsedPitch, jobId, reviewers, usage }) {
  drawLogo(doc, M.left, flow.y - 4, 20)
  font(doc, SANS, 'bold', 13)
  ink(doc, C.ink)
  doc.text('Swarmie', M.left + 26, flow.y + 11)
  font(doc, SANS, 'normal', 8.5)
  ink(doc, C.ink3)
  const shortId = String(jobId || '').replace('roast_', '').slice(0, 8)
  doc.text(`Decision memo${shortId ? ` · ${shortId}` : ''}`, M.left + CW, flow.y + 11, { align: 'right' })
  flow.y += 24
  stroke(doc, C.ink)
  doc.setLineWidth(1)
  doc.line(M.left, flow.y, M.left + CW, flow.y)
  flow.y += 16

  const subject = parsedPitch?.one_liner || parsedPitch?.target_icp
  if (subject) para(doc, flow, subject, { size: 10.5, style: 'bold', color: C.ink })

  const a = report.action_split || {}
  const spoke = (a.comment || 0) + (a.post || 0)
  const conf = { low: 'Low', med: 'Medium', high: 'High' }[report.confidence] || 'Low'
  const cost = usage ? ` · Run cost ${costLabel(usage)}` : ''
  const facts = `${reviewers} reviewers · ${spoke} spoke · ${Math.round(report.silent_share_pct || 0)}% scrolled past · Confidence ${conf}${cost}`
  flow.y += 2
  para(doc, flow, facts, { size: 8.5, color: C.ink3 })
}

function drawVerdict(doc, flow, report) {
  const title = recPhrase(report.verdict) || report.headline || 'Decision memo'
  const bad = ['is-kill', 'is-wrong'].includes(verdictMeta(report.verdict).cls)
  flow.y += 18
  font(doc, SERIF, 'bold', 30)
  const ls = lines(doc, title, CW)
  for (const ln of ls) {
    flow.need(34)
    if (bad) {
      fill(doc, C.warnHl)
      doc.rect(M.left - 1, flow.y + 16, doc.getTextWidth(ln) + 2, 13, 'F')
    }
    ink(doc, C.ink)
    doc.text(ln, M.left, flow.y + 27)
    flow.y += 33
  }
  if (report.verdict_reason) {
    flow.y += 4
    para(doc, flow, report.verdict_reason, { family: SERIF, size: 13, lh: 1.4, color: C.ink2, w: CW * 0.9 })
  }
  if (report.confidence_reason) {
    flow.y += 2
    para(doc, flow, report.confidence_reason, { size: 8.5, color: C.ink3 })
  }
}

/** Grey action panel: this week, then the branches and the rewording list. */
function drawActionPanel(doc, flow, report) {
  const p = report.path_forward || {}
  const thisWeek = report.next_action || p.this_week
  const branches = [['If it holds', p.if_confirmed], ['If not', p.if_not]].filter(([, t]) => t)
  const fixes = report.messaging_gaps || []
  if (!thisWeek && !branches.length && !fixes.length) return

  const pad = 16
  const iw = CW - pad * 2
  const colW = (iw - 18) / 2
  // Measure first so the panel can be drawn behind its text in one piece.
  font(doc, SANS, 'bold', 12)
  const tw = thisWeek ? lines(doc, thisWeek, iw) : []
  font(doc, SANS, 'normal', 9.5)
  const bl = branches.map(([, t]) => lines(doc, t, branches.length > 1 ? colW : iw))
  const branchH = bl.length ? 12 + Math.max(...bl.map((l) => l.length)) * 13.5 : 0
  const fixL = fixes.map((f) => lines(doc, f, iw - 12))
  const fixH = fixes.length ? 12 + fixL.reduce((h, l) => h + l.length * 13.5 + 3, 0) : 0
  const h = pad + (tw.length ? 12 + tw.length * 16 : 0) + (branchH ? 14 + branchH : 0) + (fixH ? 14 + fixH : 0) + pad - 4

  flow.y += 16
  flow.need(h)
  const top = flow.y
  fill(doc, C.paper2)
  doc.rect(M.left, top, CW, h, 'F')
  let y = top + pad
  const label = (t, x, yy) => { font(doc, SANS, 'bold', 8); ink(doc, C.ink3); doc.text(t, x, yy) }

  if (tw.length) {
    label('This week', M.left + pad, y + 7)
    y += 12
    font(doc, SANS, 'bold', 12); ink(doc, C.ink)
    tw.forEach((ln, i) => doc.text(ln, M.left + pad, y + 12 + i * 16))
    y += tw.length * 16
  }
  if (bl.length) {
    y += 14
    stroke(doc, C.rule2); doc.setLineWidth(0.5); doc.line(M.left + pad, y - 7, M.left + CW - pad, y - 7)
    branches.forEach(([lab], i) => {
      const x = M.left + pad + (branches.length > 1 ? i * (colW + 18) : 0)
      label(lab, x, y + 7)
      font(doc, SANS, 'normal', 9.5); ink(doc, C.ink2)
      bl[i].forEach((ln, j) => doc.text(ln, x, y + 12 + 9.5 + j * 13.5))
    })
    y += branchH
  }
  if (fixL.length) {
    y += 14
    stroke(doc, C.rule2); doc.setLineWidth(0.5); doc.line(M.left + pad, y - 7, M.left + CW - pad, y - 7)
    label('Reword the pitch', M.left + pad, y + 7)
    y += 12
    font(doc, SANS, 'normal', 9.5)
    for (const ls of fixL) {
      fill(doc, C.ink3); doc.circle(M.left + pad + 2.5, y + 6, 1.4, 'F')
      ink(doc, C.ink2)
      ls.forEach((ln, j) => doc.text(ln, M.left + pad + 12, y + 9.5 + j * 13.5))
      y += ls.length * 13.5 + 3
    }
  }
  flow.y = top + h
}

function drawWorking(doc, flow, report) {
  if (!report.what_working?.length) return
  heading(doc, flow, "What's working")
  bullets(doc, flow, report.what_working, C.live)
}

function drawRisks(doc, flow, report) {
  const risks = report.hidden_risks || []
  if (!risks.length) return
  heading(doc, flow, 'Hidden risks')
  risks.forEach((r, i) => {
    font(doc, SANS, 'bold', 10.5)
    const fw = doc.getTextWidth(`RISK ${i + 1}`) + 8 + 6
    const title = lines(doc, r.risk, CW - fw)
    flow.need(title.length * 14 + 40)
    flag(doc, `RISK ${i + 1}`, M.left, flow.y + 10)
    font(doc, SANS, 'bold', 10.5); ink(doc, C.ink)
    title.forEach((ln, j) => doc.text(ln, M.left + fw, flow.y + 10 + j * 14))
    flow.y += title.length * 14 + 3
    labelled(doc, flow, 'Easy to miss:', r.why_non_obvious, M.left + fw)
    labelled(doc, flow, 'Test it:', r.cheap_test, M.left + fw)
    flow.y += 8
  })
}

/** "Label: text" with a bold label, wrapped under the text column. */
function labelled(doc, flow, label, value, x, w = M.left + CW - x) {
  if (!value) return
  font(doc, SANS, 'bold', 9)
  const lw = doc.getTextWidth(label + ' ')
  font(doc, SANS, 'normal', 9)
  const first = lines(doc, value, w - lw)
  const rest = first.length > 1 ? lines(doc, first.slice(1).join(' '), w) : []
  flow.need(13 * (1 + rest.length))
  font(doc, SANS, 'bold', 9); ink(doc, C.ink)
  doc.text(label, x, flow.y + 9)
  font(doc, SANS, 'normal', 9); ink(doc, C.ink2)
  doc.text(first[0] || '', x + lw, flow.y + 9)
  flow.y += 13
  for (const ln of rest) { doc.text(ln, x, flow.y + 9); flow.y += 13 }
}

function drawObjections(doc, flow, report, copy) {
  const objs = report.top_objections || []
  if (!objs.length) return
  heading(doc, flow, copy.objections)
  objs.forEach((o, i) => {
    flow.need(60)
    const x = M.left + 22
    font(doc, SANS, 'bold', 10); ink(doc, C.ink3)
    doc.text(String(i + 1), M.left, flow.y + 10)
    ink(doc, C.ink)
    doc.text(sanitize(cap(o.category)), x, flow.y + 10)
    font(doc, SANS, 'normal', 8.5); ink(doc, C.ink3)
    doc.text(`${o.count ?? ''}x`, M.left + CW, flow.y + 10, { align: 'right' })
    flow.y += 16
    if (o.example_quote) {
      para(doc, flow, `"${o.example_quote}"`, { x, w: CW - 22, family: SERIF, style: 'italic', size: 10.5, lh: 1.35, color: C.ink2 })
      flow.y += 3
    }
    labelled(doc, flow, `${cap(copy.askTag)}:`, o.real_test, x)
    if (o.kill_criteria) {
      font(doc, SANS, 'normal', 9)
      const tagW = (() => { font(doc, SANS, 'bold', 7); return doc.getTextWidth(cap(copy.killTag).toUpperCase()) + 8 + 6 })()
      font(doc, SANS, 'normal', 9)
      const ls = lines(doc, o.kill_criteria, CW - 22 - tagW)
      flow.need(ls.length * 13)
      flag(doc, cap(copy.killTag).toUpperCase(), x, flow.y + 9)
      font(doc, SANS, 'normal', 9); ink(doc, C.ink2)
      ls.forEach((ln, j) => doc.text(ln, x + tagW, flow.y + 9 + j * 13))
      flow.y += ls.length * 13
    }
    labelled(doc, flow, 'Fix:', o.suggested_fix, x)
    flow.y += 10
  })
}

function drawEvidence(doc, flow, report, copy) {
  const s = report.sentiment_split || {}
  const reasons = report.ignore_reasons || []
  const segs = Object.entries(report.icp_fit || {}).map(([name, v]) => ({ name, count: Number(v?.count) || 0 }))
  const segTotal = segs.reduce((a, b) => a + b.count, 0)
  heading(doc, flow, 'Evidence')
  const colW = (CW - 24) / 2
  const xL = M.left
  const xR = M.left + colW + 24
  const startY = flow.y

  // Left: sentiment of those who spoke
  const a = report.action_split || {}
  const spoke = (a.comment || 0) + (a.post || 0)
  flow.need(90)
  font(doc, SANS, 'bold', 9); ink(doc, C.ink)
  doc.text(`How the ${spoke} who spoke felt`, xL, flow.y + 9)
  let yL = flow.y + 20
  let x = xL
  for (const [k, col] of [['positive', C.live], ['neutral', C.rule2], ['negative', C.warn]]) {
    const w = (Number(s[k]) || 0) / 100 * colW
    if (w > 0) { fill(doc, col); doc.rect(x, yL, Math.max(0, w - 1), 5, 'F'); x += w }
  }
  yL += 16
  for (const [k, col] of [['positive', C.live], ['neutral', C.rule2], ['negative', C.warn]]) {
    fill(doc, col); doc.circle(xL + 3, yL - 3, 2.4, 'F')
    font(doc, SANS, 'normal', 9); ink(doc, C.ink2)
    doc.text(cap(k), xL + 10, yL)
    font(doc, SANS, 'bold', 9); ink(doc, C.ink)
    doc.text(`${s[k] ?? 0}%`, xL + colW, yL, { align: 'right' })
    yL += 14
  }

  // Right: why people scrolled past
  let yR = flow.y
  if (reasons.length) {
    font(doc, SANS, 'bold', 9); ink(doc, C.ink)
    doc.text(sanitize(cap(copy.silence(Math.round(report.silent_share_pct || 0)))), xR, yR + 9)
    yR += 26
    for (const r of reasons) {
      font(doc, SANS, 'normal', 9); ink(doc, C.ink2)
      doc.text(sanitize(r.label), xR, yR)
      font(doc, SANS, 'bold', 9); ink(doc, C.ink)
      doc.text(`${r.share_pct}%`, xR + colW, yR, { align: 'right' })
      hbar(doc, xR, yR + 4, colW, r.share_pct, C.ink2)
      yR += 14
      const note = r.implication || r.example
      if (note) {
        font(doc, SANS, 'normal', 8); ink(doc, C.ink3)
        for (const ln of lines(doc, note, colW)) { doc.text(ln, xR, yR + 2); yR += 11 }
      }
      yR += 6
    }
  }
  flow.y = Math.max(yL, yR, startY) + 6

  if (segs.length) {
    const rows = Math.ceil(segs.length / 2)
    flow.need(26 + rows * 24)
    font(doc, SANS, 'bold', 9); ink(doc, C.ink)
    doc.text(sanitize(cap(copy.segments)), xL, flow.y + 9)
    flow.y += 26
    segs.forEach((sg, i) => {
      const cx = i % 2 ? xR : xL
      const cy = flow.y + Math.floor(i / 2) * 24
      font(doc, SANS, 'normal', 9); ink(doc, C.ink2)
      doc.text(sanitize(cap(sg.name)), cx, cy)
      font(doc, SANS, 'bold', 9); ink(doc, C.ink)
      doc.text(String(sg.count), cx + colW, cy, { align: 'right' })
      hbar(doc, cx, cy + 5, colW, segTotal ? (sg.count / segTotal) * 100 : 0, C.ink4)
    })
    flow.y += rows * 24
  }
}

function drawVoices(doc, flow, report, copy) {
  const shown = new Set((report.top_objections || []).map((o) => (o.example_quote || '').trim().toLowerCase()))
  const voices = (report.quoted_reactions || []).filter((q) => q.text && !shown.has(q.text.trim().toLowerCase()))
  if (!voices.length) return
  heading(doc, flow, copy.voices)
  for (const q of voices) {
    font(doc, SERIF, 'normal', 11)
    flow.need(lines(doc, q.text, CW).length * 15 + 22)
    para(doc, flow, `"${q.text}"`, { family: SERIF, size: 11, lh: 1.35, color: C.ink })
    const meta = [q.name && `@${q.name}`, q.tone && cap(q.tone), q.segment].filter(Boolean).join(' · ')
    para(doc, flow, meta, { size: 8, color: C.ink3 })
    flow.y += 8
  }
}

function drawSummary(doc, flow, report) {
  if (!report.narrative) return
  // Keep the summary in one piece: start it on a new page rather than split it.
  font(doc, SERIF, 'normal', 10.5)
  flow.need(16 + 34 + lines(doc, report.narrative, CW).length * 10.5 * 1.5)
  heading(doc, flow, "The panel's summary")
  para(doc, flow, report.narrative, { family: SERIF, size: 10.5, lh: 1.5, color: C.ink2 })
}

function drawDeckDiagnosis(doc, flow, report) {
  const d = report.deck_diagnosis
  if (!d) return
  heading(doc, flow, `Deck diagnosis · fundability readiness ${Math.round(d.readiness_pct || 0)}%`)
  para(doc, flow, `Stage ${d.stage || '-'} · score ${d.overall_score || 0}/130`, { size: 8.5, color: C.ink3 })
  if (d.next_move) { flow.y += 6; labelled(doc, flow, 'Next move:', d.next_move, M.left) }
  for (const s of d.slides || []) {
    flow.need(28)
    flow.y += 6
    font(doc, SANS, 'bold', 9); ink(doc, C.ink)
    doc.text(sanitize(`${cap(s.slide_type)} · page ${s.page}`), M.left, flow.y + 9)
    doc.text(`${s.score}/10`, M.left + CW, flow.y + 9, { align: 'right' })
    flow.y += 13
    if (s.top_issue) para(doc, flow, s.top_issue, { size: 9, x: M.left + 12, w: CW - 12 })
  }
  for (const f of d.red_flags || []) {
    flow.need(28)
    flow.y += 6
    const serious = f.severity === 'CRITICAL' || f.severity === 'HIGH'
    const w = serious ? flag(doc, String(f.severity), M.left, flow.y + 9) + 6 : 0
    font(doc, SANS, 'bold', 9); ink(doc, C.ink)
    doc.text(sanitize(`${serious ? '' : `${f.severity} · `}${cap(f.slide_type)} p.${f.page}`), M.left + w, flow.y + 9)
    flow.y += 13
    para(doc, flow, f.text, { size: 9, x: M.left + 12, w: CW - 12 })
  }
  if (d.strong_zones?.length) { heading(doc, flow, 'Strong zones', 12); bullets(doc, flow, d.strong_zones, C.live) }
  if (d.weak_zones?.length) { heading(doc, flow, 'Weak zones', 12); bullets(doc, flow, d.weak_zones, C.warn) }
  if (d.investor_simulation) { heading(doc, flow, 'Investor in the room', 12); para(doc, flow, d.investor_simulation, { family: SERIF, size: 10.5 }) }
}

function drawLaunchBrief(doc, flow, report) {
  const b = report.launch_brief
  if (!b) return
  for (const [label, items, col] of [
    ['Likely questions', b.questions, C.ink3],
    ['Confusion points', b.confusion, C.warn],
    ['Risks', b.risks, C.warn],
    ['Discussion themes', b.themes, C.ink3],
  ]) {
    if (items?.length) { heading(doc, flow, label); bullets(doc, flow, items, col) }
  }
  if (b.playbook?.length) {
    heading(doc, flow, 'Response playbook')
    for (const p of b.playbook) {
      labelled(doc, flow, 'If:', p.trigger, M.left)
      labelled(doc, flow, 'Reply:', p.response, M.left + 12)
      flow.y += 6
    }
  }
  if (b.next_actions?.length) { heading(doc, flow, 'Next actions'); bullets(doc, flow, b.next_actions, C.live) }
}

function costLabel(usage) {
  const c = Number(usage?.total_cost_usd || 0)
  return c >= 0.001 ? `$${c.toFixed(4)}` : 'under $0.001'
}

function drawFooter(doc, page, total) {
  const y = PAGE_H - M.bottom + 16
  stroke(doc, C.rule)
  doc.setLineWidth(0.5)
  doc.line(M.left, y, M.left + CW, y)
  font(doc, SANS, 'normal', 7.5)
  ink(doc, C.ink3)
  doc.text('AI reviewers, not real users. Directional only.  ·  swarmie.harshpatadia.com', M.left, y + 13)
  doc.text(`${page} / ${total}`, M.left + CW, y + 13, { align: 'right' })
}

// ---------------------------------------------------------------------------
// entry
// ---------------------------------------------------------------------------

const COPY = {
  validate: { objections: 'Top objections', voices: 'Loudest voices', segments: 'Segments', askTag: 'test it', killTag: 'drop it if', silence: (p) => `why ${p}% scrolled past` },
  investor: { objections: 'Questions & objections', voices: 'In the room', segments: 'Investor types', askTag: 'get proof', killTag: 'stalls if', silence: (p) => `why ${p}% passed` },
  launch: { objections: 'Objections & questions', voices: 'In the thread', segments: 'Communities', askTag: 'test this', killTag: 'risk if', silence: (p) => `why ${p}% scrolled past` },
}

/**
 * Build and download the decision-memo PDF.
 * @param {{ report: object, parsedPitch?: object, usage?: object, jobId?: string, swarmType?: string, reactionCount?: number }} opts
 */
export async function generateRoastPDF({ report, parsedPitch, usage, jobId, swarmType = 'validate', reactionCount = 0 }) {
  if (!report) throw new Error('report is required')
  const { default: jsPDF } = await import('jspdf')
  const doc = new jsPDF({ unit: 'pt', format: 'a4', orientation: 'portrait' })
  doc.setProperties({ title: 'Swarmie decision memo', creator: 'Swarmie' })

  const copy = COPY[swarmType] || COPY.validate
  const a = report.action_split || {}
  const reviewers = reactionCount || Object.values(a).reduce((x, y) => x + (Number(y) || 0), 0)

  const flow = makeFlow(doc)
  drawHeader(doc, flow, { report, parsedPitch, jobId, reviewers, usage })
  drawVerdict(doc, flow, report)
  drawActionPanel(doc, flow, report)
  drawWorking(doc, flow, report)
  drawRisks(doc, flow, report)
  drawDeckDiagnosis(doc, flow, report)
  drawLaunchBrief(doc, flow, report)
  drawObjections(doc, flow, report, copy)
  drawEvidence(doc, flow, report, copy)
  drawVoices(doc, flow, report, copy)
  drawSummary(doc, flow, report)

  const total = doc.internal.getNumberOfPages()
  for (let i = 1; i <= total; i++) { doc.setPage(i); drawFooter(doc, i, total) }

  const shortId = String(jobId || '').replace('roast_', '').slice(0, 8) || 'memo'
  doc.save(`swarmie-memo-${shortId}.pdf`)
}
