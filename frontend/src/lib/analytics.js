import FingerprintJS from '@fingerprintjs/fingerprintjs'
import { supabase } from './supabase'

let _fpPromise = null
let _fingerprint = null

function getFpPromise() {
  if (!_fpPromise) _fpPromise = FingerprintJS.load()
  return _fpPromise
}

export async function getFingerprint() {
  if (_fingerprint) return _fingerprint
  const fp = await getFpPromise()
  const result = await fp.get()
  _fingerprint = result.visitorId
  return _fingerprint
}

export async function registerDevice() {
  if (!supabase) return null
  const fingerprint = await getFingerprint()

  const { error } = await supabase
    .from('devices')
    .upsert({
      fingerprint_id: fingerprint,
      user_agent: navigator.userAgent,
      platform: navigator.platform || navigator.userAgentData?.platform || '',
      screen_res: `${screen.width}x${screen.height}`,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      last_seen_at: new Date().toISOString(),
    }, { onConflict: 'fingerprint_id' })

  if (error) console.warn('[analytics] device register failed:', error.message)
  return fingerprint
}

export async function trackRoastStart(jobId, { pitchText, pitchLength, nAgents } = {}) {
  if (!supabase) return
  const fingerprint = await getFingerprint()

  const { error } = await supabase
    .from('roast_runs')
    .insert({
      job_id: jobId,
      fingerprint_id: fingerprint,
      status: 'started',
      pitch_length: pitchLength || null,
      pitch_text: pitchText || null,
      n_agents_requested: nAgents || null,
    })

  if (error) console.warn('[analytics] trackRoastStart failed:', error.message)
}

export async function trackRoastComplete(jobId, { agentCount, promptTokens, completionTokens, totalTokens, costUsd, model, error: runError } = {}) {
  if (!supabase) return

  const update = {
    status: runError ? 'failed' : 'completed',
    completed_at: new Date().toISOString(),
  }
  if (agentCount != null) update.agent_count = agentCount
  if (promptTokens != null) update.prompt_tokens = promptTokens
  if (completionTokens != null) update.completion_tokens = completionTokens
  if (totalTokens != null) update.total_tokens = totalTokens
  if (costUsd != null) update.cost_usd = costUsd
  if (model) update.model = model
  if (runError) update.error = String(runError).slice(0, 500)

  const { error } = await supabase
    .from('roast_runs')
    .update(update)
    .eq('job_id', jobId)

  if (error) console.warn('[analytics] trackRoastComplete failed:', error.message)
}

export async function trackParsedPitch(jobId, pitch) {
  if (!supabase || !pitch) return

  const { error } = await supabase
    .from('roast_pitches')
    .upsert({
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
    }, { onConflict: 'job_id' })

  if (error) console.warn('[analytics] trackParsedPitch failed:', error.message)
}

export async function trackReport(jobId, report) {
  if (!supabase || !report) return

  const { error } = await supabase
    .from('roast_reports')
    .upsert({
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
    }, { onConflict: 'job_id' })

  if (error) console.warn('[analytics] trackReport failed:', error.message)
}

export async function trackReactions(jobId, reactions) {
  if (!supabase || !reactions?.length) return

  const rows = reactions.map(r => ({
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
  }))

  // batch in chunks of 100
  for (let i = 0; i < rows.length; i += 100) {
    const chunk = rows.slice(i, i + 100)
    const { error } = await supabase
      .from('roast_reactions')
      .upsert(chunk, { onConflict: 'job_id,agent_id' })

    if (error) {
      console.warn('[analytics] trackReactions failed:', error.message)
      break
    }
  }
}

export async function trackPdfDownload(jobId) {
  if (!supabase) return
  const fingerprint = await getFingerprint()

  const { error } = await supabase
    .from('pdf_downloads')
    .insert({
      job_id: jobId,
      fingerprint_id: fingerprint,
    })

  if (error) console.warn('[analytics] trackPdfDownload failed:', error.message)
}
