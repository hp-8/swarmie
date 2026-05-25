/**
 * Roast API client — Swarmie fast pipeline.
 */
import service from './index'

export const roastApi = {
  /**
   * Start a roast job.
   * @param {string} pitch - Pitch text to roast.
   * @param {number} [nAgents=100] - Number of agents to simulate (10..500).
   * @returns {Promise<{job_id: string, status: string}>}
   */
  create(pitch, nAgents = 100) {
    return service.post('/api/roast', { pitch, n_agents: nAgents })
  },

  /**
   * Poll job status. Includes full result when status === 'completed'.
   * @param {string} jobId
   */
  get(jobId) {
    return service.get(`/api/roast/${jobId}`)
  },

  /**
   * Cancel a running job.
   * @param {string} jobId
   */
  cancel(jobId) {
    return service.delete(`/api/roast/${jobId}`)
  },

  /**
   * Build a streaming EventSource URL for a job. The caller is responsible
   * for opening the EventSource and attaching listeners (axios doesn't do SSE).
   * @param {string} jobId
   * @returns {string}
   */
  streamUrl(jobId) {
    const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'
    return `${base}/api/roast/${jobId}/stream`
  },

  /** Send chat message to a specific agent. */
  chat(jobId, agentId, message) {
    return service.post(`/api/roast/${jobId}/agents/${agentId}/chat`, { message })
  },

  /** Fetch existing chat history with an agent. */
  getChat(jobId, agentId) {
    return service.get(`/api/roast/${jobId}/agents/${agentId}/chat`)
  },
}
