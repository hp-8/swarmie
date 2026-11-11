import FingerprintJS from '@fingerprintjs/fingerprintjs'
import service from '../api/index'
import { hasAnalyticsConsent } from './consent'

let _fpPromise = null
let _fingerprint = null

// Events go to our backend, which writes them with the server key. Browser
// keys have no access to analytics tables. Failures never reach the user.
async function send(op, payload) {
  try {
    await service.post(`/api/analytics/${op}`, payload)
  } catch (e) {
    console.warn(`[analytics] ${op} failed:`, e.message)
  }
}

function getFpPromise() {
  if (!_fpPromise) _fpPromise = FingerprintJS.load()
  return _fpPromise
}

export async function getFingerprint() {
  // Device fingerprinting is non-essential — never run it without consent.
  if (!hasAnalyticsConsent()) return null
  if (_fingerprint) return _fingerprint
  const fp = await getFpPromise()
  const result = await fp.get()
  _fingerprint = result.visitorId
  return _fingerprint
}

export async function registerDevice() {
  if (!hasAnalyticsConsent()) return null
  const fingerprint = await getFingerprint()
  await send('device', {
    fingerprint_id: fingerprint,
    user_agent: navigator.userAgent,
    platform: navigator.platform || navigator.userAgentData?.platform || '',
    screen_res: `${screen.width}x${screen.height}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    last_seen_at: new Date().toISOString(),
  })
  return fingerprint
}

export async function trackRoastStart(jobId, { pitchText, pitchLength, nAgents, swarmType, source } = {}) {
  if (!hasAnalyticsConsent()) return
  // Must land before the insert below: roast_runs.fingerprint_id has an FK to
  // devices, and registerDevice() at app-boot is fire-and-forget so it can
  // still be in flight (or have silently failed) when a run starts.
  const fingerprint = await registerDevice()
  await send('run_start', {
    job_id: jobId,
    fingerprint_id: fingerprint,
    status: 'started',
    pitch_length: pitchLength || null,
    pitch_text: pitchText || null,
    n_agents_requested: nAgents || null,
    swarm_type: swarmType || 'validate',
    source: source || null,
  })
}

export async function trackParsedPitch(jobId, pitch) {
  if (!hasAnalyticsConsent() || !pitch) return
  await send('pitch', {
    job_id: jobId,
    one_liner: pitch.one_liner || null,
    problem: pitch.problem || null,
    solution: pitch.solution || null,
    target_icp: pitch.target_icp || null,
    pricing: pitch.pricing || null,
    icp_segments: pitch.icp_segments || [],
    competitors: pitch.competitors || [],
    channels: pitch.channels || [],
    founder_ask: pitch.founder_ask || null,
  })
}

export async function trackReport(jobId, report) {
  if (!hasAnalyticsConsent() || !report) return
  await send('report', {
    job_id: jobId,
    pmf_score: report.pmf_score ?? null,
    headline: report.headline || null,
    narrative: report.narrative || null,
    sentiment_positive: report.sentiment_split?.positive ?? null,
    sentiment_neutral: report.sentiment_split?.neutral ?? null,
    sentiment_negative: report.sentiment_split?.negative ?? null,
    action_post: report.action_split?.post ?? 0,
    action_comment: report.action_split?.comment ?? 0,
    action_upvote: report.action_split?.upvote ?? 0,
    action_ignore: report.action_split?.ignore ?? 0,
    top_objections: report.top_objections || [],
    messaging_gaps: report.messaging_gaps || [],
    icp_fit: report.icp_fit || {},
    quoted_reactions: report.quoted_reactions || [],
  })
}

export async function trackReactions(jobId, reactions) {
  if (!hasAnalyticsConsent() || !reactions?.length) return
  await send('reactions', reactions.map(r => ({
    job_id: jobId,
    agent_id: r.agent_id,
    archetype_id: r.archetype_id || null,
    segment: r.segment || null,
    name: r.name || null,
    tone: r.tone || null,
    action: r.action || null,
    reaction_text: r.text || null,
    sentiment: r.sentiment ?? null,
    objections: r.objections || [],
  })))
}

export async function trackPdfDownload(jobId) {
  if (!hasAnalyticsConsent()) return
  const fingerprint = await registerDevice()
  await send('pdf_download', { job_id: jobId, fingerprint_id: fingerprint })
}

// vote: +1 | -1. Upsert so re-vote overwrites.
export async function trackObjectionFeedback(jobId, objectionCategory, vote) {
  if (!hasAnalyticsConsent()) return
  const fingerprint = await getFingerprint()
  await send('objection_feedback', {
    job_id: jobId,
    fingerprint_id: fingerprint,
    objection_category: objectionCategory,
    vote,
  })
}

// { helpful: bool, comment?: string, email?: string, trigger: 'button'|'popup' }
export async function trackProductFeedback(jobId, { helpful, comment, email, trigger }) {
  if (!hasAnalyticsConsent()) return
  const fingerprint = await getFingerprint()
  await send('product_feedback', {
    job_id: jobId,
    fingerprint_id: fingerprint,
    helpful: helpful ?? null,
    comment: comment || null,
    email: email || null,
    trigger: trigger || null,
  })
}
