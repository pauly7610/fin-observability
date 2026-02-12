import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MCPUsageCard } from '@/components/MCPUsageCard'

const mockGet = jest.fn()

jest.mock('@/lib/api-client', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
  },
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('MCPUsageCard', () => {
  beforeEach(() => {
    mockGet.mockReset()
  })

  it('renders loading state', () => {
    mockGet.mockImplementation(() => new Promise(() => {}))
    render(<MCPUsageCard />, { wrapper })
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders MCP stats when loaded', async () => {
    mockGet.mockResolvedValue({
      data: {
        total_calls: 42,
        tools: { check_transaction_compliance: 30, analyze_portfolio: 12 },
        avg_latency_ms: 150,
        errors: 0,
      },
    })
    render(<MCPUsageCard />, { wrapper })
    await waitFor(() => {
      expect(screen.getByText('42')).toBeInTheDocument()
    })
    expect(screen.getByText('150')).toBeInTheDocument()
    expect(screen.getByText('0')).toBeInTheDocument()
    expect(screen.getByText('MCP Connections')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('renders empty state when no calls', async () => {
    mockGet.mockResolvedValue({
      data: { total_calls: 0, tools: {}, avg_latency_ms: 0, errors: 0 },
    })
    render(<MCPUsageCard />, { wrapper })
    await waitFor(() => {
      expect(screen.getByText(/Connect an AI agent/)).toBeInTheDocument()
    })
    expect(screen.getByText('No calls yet')).toBeInTheDocument()
  })
})
