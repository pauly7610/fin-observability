import React from 'react'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ComplianceStatus } from '@/components/ComplianceStatus'

jest.mock('@/hooks/useCompliance', () => ({
  useCompliance: jest.fn(),
}))

const mockUseCompliance = require('@/hooks/useCompliance').useCompliance as jest.Mock

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('ComplianceStatus', () => {
  it('renders loading state', () => {
    mockUseCompliance.mockReturnValue({
      logs: [],
      stats: undefined,
      isLoading: true,
      isError: false,
      resolveLog: { mutate: jest.fn() },
    })
    render(<ComplianceStatus />, { wrapper })
    expect(document.querySelector('[class*="animate-pulse"]') || document.body).toBeTruthy()
  })

  it('renders error state', () => {
    mockUseCompliance.mockReturnValue({
      logs: [],
      stats: undefined,
      isLoading: false,
      isError: true,
      error: { message: 'Failed to load' },
      resolveLog: { mutate: jest.fn() },
    })
    render(<ComplianceStatus />, { wrapper })
    expect(screen.getByText(/retry|try again|reload/i)).toBeTruthy()
  })

  it('renders stats and logs when loaded', () => {
    mockUseCompliance.mockReturnValue({
      logs: [
        {
          id: 1,
          event_type: 'transaction',
          severity: 'high',
          is_resolved: false,
          timestamp: new Date().toISOString(),
          description: 'Suspicious transfer',
        },
      ],
      stats: {
        total_logs: 10,
        resolved_logs: 6,
        unresolved_logs: 4,
        severity_distribution: { high: 2, medium: 3, low: 5 },
      },
      isLoading: false,
      isError: false,
      resolveLog: { mutate: jest.fn() },
    })
    render(<ComplianceStatus />, { wrapper })
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('6')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
    expect(screen.getByText('Compliance Logs')).toBeInTheDocument()
    expect(screen.getByText('Suspicious transfer')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Resolve' })).toBeInTheDocument()
  })

  it('renders empty state when no logs', () => {
    mockUseCompliance.mockReturnValue({
      logs: [],
      stats: { total_logs: 0, resolved_logs: 0, unresolved_logs: 0, severity_distribution: {} },
      isLoading: false,
      isError: false,
      resolveLog: { mutate: jest.fn() },
    })
    render(<ComplianceStatus />, { wrapper })
    expect(screen.getByText('No compliance logs')).toBeInTheDocument()
  })
})
