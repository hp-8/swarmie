import axios from 'axios'
import { accessToken } from '../lib/account'

// One HTTP client for every backend call. Callers get the response body back,
// not the axios response object.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001',
  // Deck parsing and big panels can take minutes before the first byte.
  timeout: 5 * 60 * 1000,
  headers: { 'Content-Type': 'application/json' },
})

// Signed-in users send their Supabase token; billing uses it to find the account.
api.interceptors.request.use((config) => {
  const token = accessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => {
    const body = response.data
    // Some endpoints answer 200 with { success: false, error } — treat as a failure.
    if (body && body.success === false) {
      return Promise.reject(new Error(body.error || body.message || 'Request failed'))
    }
    return body
  },
  (error) => {
    console.error('[api]', error.code || error.response?.status || '', error.message)
    return Promise.reject(error)
  },
)

export default api
