'use client'

import { Card, CardContent } from '@/components/ui/card'
import { useMetrics } from '@/hooks/useMetrics'
import { CardSkeleton } from '@/components/CardSkeleton'
import { ArrowUpRight, ArrowDownRight, AlertTriangle, Clock, Shield, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatCardProps {
  title: string
  value: string | number
  subtitle: string
  icon: React.ReactNode
  trend?: { value: number; label: string; positive: boolean }
  accent?: string
}

function StatCard({ title, value, subtitle, icon, trend, accent = 'text-primary' }: StatCardProps) {
  return (
    <Card className="relative overflow-hidden">
      <CardContent className="p-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            {title}
          </span>
          <div className={cn('p-2 rounded-lg bg-muted', accent)}>
            {icon}
          </div>
        </div>
        <div className="space-y-1">
          <div className={cn('text-3xl font-bold tabular-nums tracking-tight', accent)}>
            {value}
          </div>
          <div className="flex items-center gap-2">
            {trend && (
              <span
                className={cn(
                  'inline-flex items-center gap-0.5 text-xs font-semibold rounded-full px-1.5 py-0.5',
                  trend.positive
                    ? 'text-emerald-500 bg-emerald-500/10'
                    : 'text-red-500 bg-red-500/10'
                )}
              >
                {trend.positive ? (
                  <ArrowUpRight className="h-3 w-3" />
                ) : (
                  <ArrowDownRight className="h-3 w-3" />
                )}
                {trend.value}%
              </span>
            )}
            <span className="text-xs text-muted-foreground">{subtitle}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function MetricsOverview() {
  const { data, isLoading } = useMetrics()

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="System Uptime"
        value={`${data?.uptime ?? 0}%`}
        subtitle="Last 30 days"
        icon={<Activity className="h-4 w-4" />}
        trend={{ value: 0.1, label: 'vs last month', positive: true }}
        accent="text-emerald-500"
      />
      <StatCard
        title="Active Alerts"
        value={data?.activeAlerts ?? 0}
        subtitle={`${data?.noiseReduction ?? 0}% noise reduced`}
        icon={<AlertTriangle className="h-4 w-4" />}
        accent={data?.activeAlerts > 0 ? 'text-amber-500' : 'text-emerald-500'}
      />
      <StatCard
        title="MTTR"
        value={`${data?.mttr ?? 0}m`}
        subtitle="Mean time to resolve"
        icon={<Clock className="h-4 w-4" />}
        trend={{ value: data?.mttrImprovement ?? 0, label: 'improvement', positive: true }}
        accent="text-blue-500"
      />
      <StatCard
        title="Compliance"
        value={data?.complianceScore ?? 0}
        subtitle={data?.complianceStatus ?? 'Unknown'}
        icon={<Shield className="h-4 w-4" />}
        accent={
          (data?.complianceScore ?? 0) >= 90
            ? 'text-emerald-500'
            : (data?.complianceScore ?? 0) >= 70
            ? 'text-amber-500'
            : 'text-red-500'
        }
      />
    </div>
  )
}
