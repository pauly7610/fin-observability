import React from 'react'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MetricsOverview } from '@/components/MetricsOverview'

jest.mock('@/hooks/useMetrics', () => ({
  useMetrics: jest.fn(),
}))

const mockUseMetrics = require('@/hooks/useMetrics').useMetrics as jest.Mock

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('MetricsOverview', () => {
  it('renders loading skeletons when loading', () => {
    mockUseMetrics.mockReturnValue({ data: null, isLoading: true })
    const { container } = render(<MetricsOverview />, { wrapper })
    expect(container.querySelector('.grid')).toBeInTheDocument()
    expect(container.querySelector('[class*="animate-pulse"]')).toBeInTheDocument()
  })

  it('renders metric cards when data is loaded', () => {
    mockUseMetrics.mockReturnValue({
      data: {
        uptime: 99.9,
        activeAlerts: 2,
        noiseReduction: 94,
        mttr: 12,
        mttrImprovement: 35,
        complianceScore: 85,
        complianceStatus: 'Compliant',
      },
      isLoading: false,
    })
    render(<MetricsOverview />, { wrapper })
    expect(screen.getByText('99.9%')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('12m')).toBeInTheDocument()
    expect(screen.getByText('85')).toBeInTheDocument()
    expect(screen.getByText('System Uptime')).toBeInTheDocument()
    expect(screen.getByText('Active Alerts')).toBeInTheDocument()
    expect(screen.getByText('MTTR')).toBeInTheDocument()
    expect(screen.getByText('Compliance')).toBeInTheDocument()
  })

  it('renders fallback values when data is null', () => {
    mockUseMetrics.mockReturnValue({ data: null, isLoading: false })
    render(<MetricsOverview />, { wrapper })
    expect(screen.getByText('System Uptime')).toBeInTheDocument()
    expect(screen.getAllByText('0').length).toBeGreaterThan(0)
  })
})
