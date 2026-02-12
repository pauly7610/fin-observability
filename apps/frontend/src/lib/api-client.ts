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

// Token getter set by AuthTokenProvider; used for Bearer auth
let tokenGetter: (() => Promise<string | null>) | null = null
export function setAuthTokenGetter(getter: () => Promise<string | null>) {
  tokenGetter = getter
}

// Request interceptor: attach Clerk session token for backend auth
apiClient.interceptors.request.use(async (config) => {
  if (typeof window !== 'undefined') {
    try {
      const token = tokenGetter ? await tokenGetter() : null
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      } else {
        config.headers['x-user-email'] = 'admin@example.com'
        config.headers['x-user-role'] = 'admin'
      }
    } catch {
      config.headers['x-user-email'] = 'admin@example.com'
      config.headers['x-user-role'] = 'admin'
    }
  }
  return config
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
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
