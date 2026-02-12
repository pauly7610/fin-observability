import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useMetrics } from '@/hooks/useMetrics'

const originalFetch = global.fetch

beforeEach(() => {
  global.fetch = jest.fn()
})

afterEach(() => {
  global.fetch = originalFetch
})

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return React.createElement(QueryClientProvider, { client }, children)
}

describe('useMetrics', () => {
  it('fetches metrics from /api/metrics', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        uptime: 99.9,
        activeAlerts: 3,
        noiseReduction: 94,
        mttr: 12,
        mttrImprovement: 35,
        complianceScore: 88,
        complianceStatus: 'Compliant',
      }),
    })
    const { result } = renderHook(() => useMetrics(), { wrapper })
    await waitFor(() => {
      expect(result.current.data?.uptime).toBe(99.9)
    })
    expect(result.current.data?.activeAlerts).toBe(3)
    expect(result.current.data?.complianceScore).toBe(88)
    expect(global.fetch).toHaveBeenCalledWith('/api/metrics', expect.objectContaining({ signal: expect.any(AbortSignal) }))
  })

  it('has initial data fallback', () => {
    ;(global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}))
    const { result } = renderHook(() => useMetrics(), { wrapper })
    expect(result.current.data).toBeDefined()
    expect(result.current.data?.uptime).toBe(0)
  })
})
