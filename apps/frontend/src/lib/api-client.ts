import axios from 'axios'
import { z } from 'zod'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor to attach auth headers
apiClient.interceptors.request.use((config) => {
  // Check for JWT token in localStorage
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    } else {
      // Fallback to dev headers
      config.headers['x-user-email'] = 'admin@example.com'
      config.headers['x-user-role'] = 'admin'
    }
  }
  return config
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token')
      }
    }
    return Promise.reject(error)
  }
)

export function validateResponse<T>(response: { data: unknown }, schema: z.ZodType<T>): T {
  const result = schema.safeParse(response.data)
  if (!result.success) {
    console.warn('Response validation warning:', result.error.issues)
    return response.data as T
  }
  return result.data
}

export default apiClient
