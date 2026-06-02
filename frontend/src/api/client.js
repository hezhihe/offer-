import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 90000
})

export function normalizeToken(rawToken) {
  if (!rawToken) return ''
  return String(rawToken)
    .trim()
    .replace(/^["']|["']$/g, '')
    .replace(/^Bearer\s+/i, '')
    .replace(/\s+/g, '')
}

client.interceptors.request.use(config => {
  const token = normalizeToken(localStorage.getItem('user_token'))
  if (token) {
    localStorage.setItem('user_token', token)
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('user_token')
      window.location.href = '#/auth'
    }
    return Promise.reject(error)
  }
)

export default client
