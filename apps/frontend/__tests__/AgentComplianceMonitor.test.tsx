import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AgentComplianceMonitor } from '@/components/AgentComplianceMonitor'

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

describe('AgentComplianceMonitor', () => {
  beforeEach(() => {
    mockGet.mockReset()
    mockPost.mockReset()
  })

  it('renders header and badges', async () => {
    mockGet.mockResolvedValue({ data: {} })
    render(<AgentComplianceMonitor />)
    await waitFor(() => {
      expect(screen.getByText('AI Agent: Financial Compliance Monitor')).toBeInTheDocument()
    })
    expect(screen.getByText('FINRA 4511')).toBeInTheDocument()
    expect(screen.getByText('SEC 17a-4')).toBeInTheDocument()
    expect(screen.getByText('Batch Testing')).toBeInTheDocument()
    expect(screen.getByText('Test Transaction')).toBeInTheDocument()
  })

  it('renders metric cards when metrics are loaded', async () => {
    mockGet.mockResolvedValue({
      data: {
        total_transactions: 1000,
        approval_rate: 85,
        block_rate: 5,
        avg_confidence: 92,
        storage: 'sqlite',
      },
    })
    render(<AgentComplianceMonitor />)
    await waitFor(() => {
      expect(screen.getByText('1000')).toBeInTheDocument()
    })
    expect(screen.getByText('85%')).toBeInTheDocument()
    expect(screen.getByText('5%')).toBeInTheDocument()
    expect(screen.getByText('92%')).toBeInTheDocument()
  })

  it('shows Run Compliance Check button', async () => {
    mockGet.mockResolvedValue({ data: {} })
    render(<AgentComplianceMonitor />)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Run Compliance Check/i })).toBeInTheDocument()
    })
  })

  it('displays compliance result when check succeeds', async () => {
    mockGet.mockResolvedValue({ data: {} })
    mockPost.mockResolvedValue({
      data: {
        action: 'approve',
        confidence: 95,
        reasoning: 'Transaction within limits',
        alternatives: [],
        audit_trail: { regulation: 'FINRA 4511', timestamp: new Date().toISOString(), agent: 'ml-v2' },
      },
    })
    render(<AgentComplianceMonitor />)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Run Compliance Check/i })).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: /Run Compliance Check/i }))
    await waitFor(() => {
      expect(screen.getByText('APPROVE')).toBeInTheDocument()
    })
    expect(screen.getByText(/95/)).toBeInTheDocument()
    expect(screen.getByText('Agent Reasoning')).toBeInTheDocument()
  })
})
