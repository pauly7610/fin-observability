import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ConnectPage from '../app/(dashboard)/connect/page'

const mockGet = jest.fn()
const mockPost = jest.fn()

jest.mock('@/lib/api-client', () => ({
  __esModule: true,
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
  },
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

function setupConnectMocks() {
  mockGet
    .mockResolvedValueOnce({
      data: {
        tools: [
          { name: 'check_transaction_compliance', description: 'Score a transaction', parameters: {} },
        ],
        tool_count: 1,
      },
    })
    .mockResolvedValueOnce({
      data: { total_calls: 0, tools: {}, avg_latency_ms: 0, errors: 0, recent: [] },
    })
    .mockResolvedValueOnce({
      data: { enabled: false, brokers: '', topics: [], stuck_order_threshold_minutes: 5 },
    })
}

describe('Connect Page', () => {
  beforeEach(() => {
    mockGet.mockReset()
    mockPost.mockReset()
  })

  it('renders Connect Your AI Agent title', async () => {
    setupConnectMocks()
    render(<ConnectPage />, { wrapper })
    await waitFor(() => {
      expect(screen.getByText('Connect Your AI Agent')).toBeInTheDocument()
    })
  })

  it('renders Quick Connect and Tool Catalog sections', async () => {
    mockGet
      .mockResolvedValueOnce({ data: { tools: [], tool_count: 0 } })
      .mockResolvedValueOnce({ data: { total_calls: 0, tools: {}, avg_latency_ms: 0, errors: 0 } })
      .mockResolvedValueOnce({ data: { enabled: false } })
    render(<ConnectPage />, { wrapper })
    await waitFor(() => {
      expect(screen.getByText('Quick Connect')).toBeInTheDocument()
    })
    expect(screen.getByText('Tool Catalog')).toBeInTheDocument()
  })

  it('renders Try It Live section', async () => {
    setupConnectMocks()
    render(<ConnectPage />, { wrapper })
    await waitFor(() => {
      expect(screen.getByText('Try It Live')).toBeInTheDocument()
    })
    expect(screen.getByText('Run Compliance Check')).toBeInTheDocument()
  })
})
