import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useCompliance } from '@/hooks/useCompliance'

const mockGet = jest.fn()
const mockPut = jest.fn()

jest.mock('@/lib/api-client', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    put: (...args: unknown[]) => mockPut(...args),
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
  },
  validateResponse: (res: { data: unknown }) => res.data,
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return React.createElement(QueryClientProvider, { client }, children)
}

describe('useCompliance', () => {
  beforeEach(() => {
    mockGet.mockReset()
    mockPut.mockReset()
  })

  it('fetches compliance logs and stats', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url.includes('stats')) {
        return Promise.resolve({ data: { total_logs: 5, resolved_logs: 3, unresolved_logs: 2, severity_distribution: {} } })
      }
      return Promise.resolve({
        data: [
          { id: 1, event_type: 'tx', severity: 'high', is_resolved: false, timestamp: '2025-01-01', description: 'Test' },
        ],
      })
    })
    const { result } = renderHook(() => useCompliance(), { wrapper })
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
    expect(result.current.logs).toHaveLength(1)
    expect(result.current.logs[0].event_type).toBe('tx')
    expect(result.current.stats?.total_logs).toBe(5)
  })

  it('resolveLog mutation invalidates queries', async () => {
    mockGet.mockResolvedValue({ data: [] })
    mockPut.mockResolvedValue({ data: { id: 1, is_resolved: true } })
    const { result } = renderHook(() => useCompliance(), { wrapper })
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
    result.current.resolveLog.mutate(1)
    await waitFor(() => {
      expect(mockPut).toHaveBeenCalledWith('/compliance/logs/1/resolve')
    })
  })
})
