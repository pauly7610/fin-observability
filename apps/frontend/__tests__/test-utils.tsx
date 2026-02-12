/**
 * Test utilities: QueryClientProvider wrapper and custom render.
 */
import React from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })

interface AllProvidersProps {
  children: React.ReactNode
}

function AllProviders({ children }: AllProvidersProps) {
  const [queryClient] = React.useState(createTestQueryClient)
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

function customRender(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, {
    wrapper: AllProviders,
    ...options,
  })
}

export * from '@testing-library/react'
export { customRender as render }
