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

export async function trackRoastStart(jobId, { pitchLength, model } = {}) {
  if (!supabase) return
  const fingerprint = await getFingerprint()

  const { error } = await supabase
    .from('roast_runs')
    .insert({
      job_id: jobId,
      fingerprint_id: fingerprint,
      status: 'started',
      pitch_length: pitchLength || null,
      model: model || null,
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
