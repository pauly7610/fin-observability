import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AgentComplianceMonitor } from '@/components/AgentComplianceMonitor'

const originalFetch = global.fetch

beforeEach(() => {
  global.fetch = jest.fn()
})

afterEach(() => {
  global.fetch = originalFetch
})

describe('AgentComplianceMonitor', () => {
  it('renders header and badges', async () => {
    ;(global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) })
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
    ;(global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('metrics')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            total_transactions: 1000,
            approval_rate: 85,
            block_rate: 5,
            avg_confidence: 92,
            storage: 'sqlite',
          }),
        })
      }
      return Promise.resolve({ ok: false })
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
    ;(global.fetch as jest.Mock).mockResolvedValue({ ok: true, json: async () => ({}) })
    render(<AgentComplianceMonitor />)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Run Compliance Check/i })).toBeInTheDocument()
    })
  })

  it('displays compliance result when check succeeds', async () => {
    ;(global.fetch as jest.Mock).mockImplementation((url: string, opts?: { method?: string }) => {
      if (url.includes('monitor') && opts?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            action: 'approve',
            confidence: 95,
            reasoning: 'Transaction within limits',
            alternatives: [],
            audit_trail: { regulation: 'FINRA 4511', timestamp: new Date().toISOString(), agent: 'ml-v2' },
          }),
        })
      }
      if (url.includes('metrics')) {
        return Promise.resolve({ ok: true, json: async () => ({}) })
      }
      return Promise.resolve({ ok: false })
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
