/**
 * Verdict display mapping — single source of truth.
 *
 * Shared by Result.vue (verdict chip), lib/shareCard.js (PNG share card)
 * and views/Roasts.vue (famous-roasts gallery). `cls` keys into the
 * `.is-ship / .is-sharpen / .is-wrong / .is-kill` CSS classes, which color
 * via tokens.css custom props.
 *
 * VERDICT_HEX carries the same semantic colors as concrete hex values for
 * canvas surfaces that can't read CSS custom props (same tokens→RGB
 * translation as the palette in lib/pdf/template.js).
 */

export const VERDICT_META = {
  // validate swarm
  ship_it: { label: 'ship it', cls: 'is-ship' },
  sharpen_positioning: { label: 'sharpen', cls: 'is-sharpen' },
  wrong_audience: { label: 'wrong audience', cls: 'is-wrong' },
  kill: { label: 'rethink the core', cls: 'is-kill' },  // key stays 'kill' (API/PMF/eval)
  // investor swarm
  fundable: { label: 'fundable', cls: 'is-ship' },
  sharpen_story: { label: 'sharpen story', cls: 'is-sharpen' },
  wrong_stage: { label: 'wrong stage', cls: 'is-wrong' },
  not_fundable: { label: 'not fundable', cls: 'is-kill' },
  // launch swarm
  go: { label: 'go', cls: 'is-ship' },
  sharpen: { label: 'sharpen', cls: 'is-sharpen' },
  hold: { label: 'hold', cls: 'is-wrong' },
}

// Memo phrasing for a recommendation line (sentence, with full stop).
const REC_PHRASE = {
  ship_it: 'Ship it.',
  sharpen_positioning: 'Sharpen the positioning.',
  wrong_audience: 'Wrong audience.',
  kill: 'Rethink the core.',
  fundable: 'Fundable.',
  sharpen_story: 'Sharpen the story.',
  wrong_stage: 'Wrong stage.',
  not_fundable: 'Not fundable yet.',
  go: 'Go.',
  sharpen: 'Sharpen before launch.',
  hold: 'Hold the launch.',
}
export function recPhrase(v) {
  if (!v) return ''
  if (REC_PHRASE[v]) return REC_PHRASE[v]
  const label = verdictMeta(v).label
  return label.charAt(0).toUpperCase() + label.slice(1) + '.'
}

export function verdictMeta(v) {
  return VERDICT_META[v] || { label: v || '—', cls: 'is-sharpen' }
}

// tokens.css (light) → hex: --live → #2b7a4b · amber #9a5b13 · --warn → #bf2f2a
export const VERDICT_HEX = {
  'is-ship': '#2b7a4b',
  'is-sharpen': '#9a5b13',
  'is-wrong': '#bf2f2a',
  'is-kill': '#bf2f2a',
}
