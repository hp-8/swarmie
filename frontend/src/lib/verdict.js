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
  kill: { label: 'kill', cls: 'is-kill' },
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

export function verdictMeta(v) {
  return VERDICT_META[v] || { label: v || '—', cls: 'is-sharpen' }
}

// tokens.css → hex: --live → #5fd99a · --accent-bright → #f8924f · --warn → #ec5f5f
export const VERDICT_HEX = {
  'is-ship': '#5fd99a',
  'is-sharpen': '#f8924f',
  'is-wrong': '#ec5f5f',
  'is-kill': '#ec5f5f',
}
