import React from 'react'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DashboardPage from '../app/(dashboard)/page'

jest.mock('@/components/MetricsOverview', () => ({
  MetricsOverview: () => <div data-testid="metrics-overview">MetricsOverview</div>,
}))
jest.mock('@/components/ActivityFeed', () => ({
  ActivityFeed: () => <div data-testid="activity-feed">ActivityFeed</div>,
}))
jest.mock('@/components/AIStatusCard', () => ({
  AIStatusCard: () => <div data-testid="ai-status">AIStatusCard</div>,
}))
jest.mock('@/components/DashboardCharts', () => ({
  DashboardCharts: () => <div data-testid="dashboard-charts">DashboardCharts</div>,
}))
jest.mock('@/components/MCPUsageCard', () => ({
  MCPUsageCard: () => <div data-testid="mcp-usage">MCPUsageCard</div>,
}))

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

describe('Dashboard Page', () => {
  it('renders dashboard title and description', () => {
    render(<DashboardPage />, { wrapper })
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText(/Real-time overview/)).toBeInTheDocument()
  })

  it('renders MetricsOverview, ActivityFeed, MCPUsageCard', () => {
    render(<DashboardPage />, { wrapper })
    expect(screen.getByTestId('metrics-overview')).toBeInTheDocument()
    expect(screen.getByTestId('activity-feed')).toBeInTheDocument()
    expect(screen.getByTestId('mcp-usage')).toBeInTheDocument()
    expect(screen.getByTestId('ai-status')).toBeInTheDocument()
    expect(screen.getByTestId('dashboard-charts')).toBeInTheDocument()
  })
})
