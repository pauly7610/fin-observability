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
      }
      // When no token: send no auth headers (backend returns 401 or demo viewer)
    } catch {
      // On error: send no auth headers
    }
  }
  return config
})

const AUTH_ROUTES = ['/sign-in', '/sign-up']

function shouldRedirectToSignIn(): boolean {
  if (typeof window === 'undefined') return false
  const path = window.location.pathname
  return !AUTH_ROUTES.some((r) => path.startsWith(r))
}

// Response interceptor: redirect to sign-in on 401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && shouldRedirectToSignIn()) {
      window.location.assign('/sign-in')
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
