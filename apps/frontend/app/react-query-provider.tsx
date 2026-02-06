'use client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React, { useState } from 'react'

export function ReactQueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60 * 5, // 5 minutes
        retry: 3,
        refetchOnWindowFocus: false,
      },
    },
  }))
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}
