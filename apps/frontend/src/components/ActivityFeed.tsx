'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useAlerts } from '@/hooks/useAlerts'
import { TableSkeleton } from '@/components/CardSkeleton'
import { AlertTriangle, CheckCircle, Clock, Shield, Bot } from 'lucide-react'
import { cn } from '@/lib/utils'

const severityConfig: Record<string, { color: string; dot: string }> = {
  critical: { color: 'text-red-500', dot: 'bg-red-500' },
  high: { color: 'text-orange-500', dot: 'bg-orange-500' },
  medium: { color: 'text-amber-500', dot: 'bg-amber-500' },
  low: { color: 'text-blue-500', dot: 'bg-blue-500' },
}

const statusConfig: Record<string, { icon: React.ReactNode; color: string }> = {
  open: { icon: <AlertTriangle className="h-3.5 w-3.5" />, color: 'text-red-500' },
  investigating: { icon: <Clock className="h-3.5 w-3.5" />, color: 'text-amber-500' },
  resolved: { icon: <CheckCircle className="h-3.5 w-3.5" />, color: 'text-emerald-500' },
  closed: { icon: <CheckCircle className="h-3.5 w-3.5" />, color: 'text-muted-foreground' },
}

function timeAgo(dateStr: string): string {
  const now = new Date()
  const date = new Date(dateStr)
  const diffMs = now.getTime() - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return 'just now'
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.floor(diffHr / 24)
  return `${diffDay}d ago`
}

export function ActivityFeed() {
  const { data, isLoading } = useAlerts()

  if (isLoading) return <TableSkeleton rows={6} />

  const alerts = (data?.alerts || []).slice(0, 8)

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          Recent Incidents
        </CardTitle>
      </CardHeader>
      <CardContent>
        {alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Shield className="h-10 w-10 text-emerald-500/50 mb-3" />
            <p className="text-sm font-medium text-muted-foreground">All clear</p>
            <p className="text-xs text-muted-foreground/70">No active incidents</p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert: any) => {
              const severity = severityConfig[alert.severity] || severityConfig.low
              const status = statusConfig[alert.status] || statusConfig.open
              return (
                <div
                  key={alert.id || alert.incident_id}
                  className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer group"
                >
                  <div className={cn('mt-0.5', status.color)}>
                    {status.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-sm font-medium truncate">
                        {alert.title}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className={cn('text-[10px] px-1.5 py-0 h-4', severity.color)}
                      >
                        {alert.severity}
                      </Badge>
                      {alert.type && (
                        <span className="text-[10px] text-muted-foreground">
                          {alert.type}
                        </span>
                      )}
                      {alert.desk && (
                        <span className="text-[10px] text-muted-foreground">
                          {alert.desk}
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="text-[10px] text-muted-foreground whitespace-nowrap mt-0.5">
                    {timeAgo(alert.created_at)}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
