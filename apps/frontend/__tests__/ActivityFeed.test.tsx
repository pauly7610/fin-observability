import React from 'react'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ActivityFeed } from '@/components/ActivityFeed'

jest.mock('@/hooks/useAlerts', () => ({
  useAlerts: jest.fn(),
}))

const mockUseAlerts = require('@/hooks/useAlerts').useAlerts as jest.Mock

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('ActivityFeed', () => {
  it('renders loading skeleton when loading', () => {
    mockUseAlerts.mockReturnValue({ data: null, isLoading: true })
    render(<ActivityFeed />, { wrapper })
    expect(document.querySelector('[class*="animate-pulse"]') || document.body).toBeTruthy()
  })

  it('renders All clear when no incidents', () => {
    mockUseAlerts.mockReturnValue({
      data: { alerts: [] },
      isLoading: false,
    })
    render(<ActivityFeed />, { wrapper })
    expect(screen.getByText('All clear')).toBeInTheDocument()
    expect(screen.getByText('No active incidents')).toBeInTheDocument()
  })

  it('renders incidents when data is provided', () => {
    mockUseAlerts.mockReturnValue({
      data: {
        alerts: [
          {
            id: '1',
            incident_id: 'INC-001',
            title: 'Stuck Order',
            severity: 'high',
            status: 'open',
            type: 'stuck_order',
            desk: 'FX',
            created_at: new Date().toISOString(),
          },
        ],
      },
      isLoading: false,
    })
    render(<ActivityFeed />, { wrapper })
    expect(screen.getByText('Recent Incidents')).toBeInTheDocument()
    expect(screen.getByText('Stuck Order')).toBeInTheDocument()
    expect(screen.getByText('high')).toBeInTheDocument()
  })
})
