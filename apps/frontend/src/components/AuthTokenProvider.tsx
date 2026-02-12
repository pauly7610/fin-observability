'use client'

import { useAuth } from '@clerk/nextjs'
import { useEffect } from 'react'
import { setAuthTokenGetter } from '@/lib/api-client'

export function AuthTokenProvider({ children }: { children: React.ReactNode }) {
  const { getToken } = useAuth()

  useEffect(() => {
    setAuthTokenGetter(getToken)
  }, [getToken])

  return <>{children}</>
}
