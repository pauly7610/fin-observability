import React from 'react'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useMetrics } from '@/hooks/useMetrics'

const mockGet = jest.fn()

jest.mock('@/lib/api-client', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
  },
}))

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

describe('useMetrics', () => {
  beforeEach(() => {
    mockGet.mockReset()
  })

  it('returns initialData shape when loading', () => {
    mockGet.mockImplementation(() => new Promise(() => {}))
    const { result } = renderHook(() => useMetrics(), {
      wrapper: createWrapper(),
    })
    expect(result.current.data).toEqual({
      uptime: 0,
      activeAlerts: 0,
      noiseReduction: 0,
      mttr: 0,
      mttrImprovement: 0,
      complianceScore: 0,
      complianceStatus: 'Unknown',
    })
  })

  it('fetches metrics from apiClient', async () => {
    mockGet.mockResolvedValue({
      data: {
        uptime: 99.9,
        activeAlerts: 5,
        noiseReduction: 94,
        mttr: 12,
        mttrImprovement: 35,
        complianceScore: 85,
        complianceStatus: 'Compliant',
      },
    })
    const { result } = renderHook(() => useMetrics(), {
      wrapper: createWrapper(),
    })
    await waitFor(() => {
      expect(result.current.data?.uptime).toBe(99.9)
    })
    expect(mockGet).toHaveBeenCalledWith('/api/metrics', expect.any(Object))
    expect(result.current.data?.complianceStatus).toBe('Compliant')
  })
})
