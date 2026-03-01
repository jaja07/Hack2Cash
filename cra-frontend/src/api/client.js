/**
 * api/client.js
 * Centralised axios instance + typed API calls.
 */
import axios from 'axios'
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api/`,
  timeout: 120_000,
})

// ── Auth token injector ────────────────────────────────────────────────
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('cra_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── API helpers ────────────────────────────────────────────────────────
// Connexion (Standard OAuth2 attendu par le backend)
export const login = (email, password) => {
  const formData = new URLSearchParams();
  formData.append('username', email); // FastAPI utilise 'username' par défaut
  formData.append('password', password);

  return api.post('users/token', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  }).then((r) => r.data);
}

// Création de compte
export const register = (userData) =>
  api.post('users/', userData).then((r) => r.data);




export const getReport = (jobId) =>
  api.get(`reports/${jobId}`).then((r) => r.data)

export const sendChat = (jobId, message) =>
  api.post('chat', { job_id: jobId, message }).then((r) => r.data)

export const healthCheck = () =>
  api.get('health').then((r) => r.data)

// Lancer l'analyse (Route: /api/agents/analyze)
export const startAnalysis = (payload) =>
  api.post('agents/analyze', payload).then((r) => r.data)

// Suivre l'avancement (Route: /api/agents/jobs/{id})
export const getJobStatus = (jobId) =>
  api.get(`agents/jobs/${jobId}`).then((r) => r.data)

// Analyser un fichier directement (Optionnel, si vous utilisez cette route)
export const uploadAndAnalyze = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('agents/analyze/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}

// Uploader pour l'analyse à travers le websocket
export const uploadForWebsocket = (conversationId, file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`ws/${conversationId}/upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}

export default api
