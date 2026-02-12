'use client'

import { MetricsOverview } from '@/components/MetricsOverview'
import { ActivityFeed } from '@/components/ActivityFeed'
import { AIStatusCard } from '@/components/AIStatusCard'
import { DashboardCharts } from '@/components/DashboardCharts'
import { MCPUsageCard } from '@/components/MCPUsageCard'

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Real-time overview of your financial AI observability platform.
        </p>
      </div>
      <MetricsOverview />
      <DashboardCharts />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ActivityFeed />
        <AIStatusCard />
        <MCPUsageCard />
      </div>
    </div>
  )
}