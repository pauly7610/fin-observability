import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useAlerts } from '@/hooks/useAlerts'

const mockGet = jest.fn()
const mockPost = jest.fn()

jest.mock('@/lib/api-client', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
  },
  validateResponse: (res: { data: unknown }) => res.data,
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return React.createElement(QueryClientProvider, { client }, children)
}

describe('useAlerts', () => {
  beforeEach(() => {
    mockGet.mockReset()
    mockPost.mockReset()
  })

  it('fetches incidents and returns alerts', async () => {
    mockGet.mockResolvedValue({
      data: {
        incidents: [
          {
            id: '1',
            incident_id: 'INC-001',
            title: 'Stuck Order',
            description: 'Test',
            status: 'open',
            severity: 'high',
            priority: 1,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            assigned_to: null,
          },
        ],
      },
    })
    const { result } = renderHook(() => useAlerts(), { wrapper })
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
    expect(result.current.data?.alerts).toHaveLength(1)
    expect(result.current.data?.alerts[0].title).toBe('Stuck Order')
  })

  it('bulkResolve mutation calls API', async () => {
    mockGet.mockResolvedValue({ data: { incidents: [] } })
    mockPost.mockResolvedValue({ data: { results: [] } })
    const { result } = renderHook(() => useAlerts(), { wrapper })
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })
    result.current.bulkResolve.mutate(['INC-001'])
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/incidents/bulk/resolve', {
        incident_ids: ['INC-001'],
      })
    })
  })
})
