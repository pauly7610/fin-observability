'use client'

import { useCompliance } from '@/hooks/useCompliance'
import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ComplianceLog, ComplianceStats } from '@/types/api'
import { TableSkeleton, CardSkeleton } from '@/components/CardSkeleton'
import { ErrorState } from '@/components/ErrorState'
import { Shield, CheckCircle, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

const severityBadge: Record<string, string> = {
  critical: 'text-red-500 border-red-500/30 bg-red-500/10',
  high: 'text-orange-500 border-orange-500/30 bg-orange-500/10',
  medium: 'text-amber-500 border-amber-500/30 bg-amber-500/10',
  low: 'text-blue-500 border-blue-500/30 bg-blue-500/10',
}

export function ComplianceStatus() {
  const { logs, stats, isLoading, isError, error, resolveLog } = useCompliance()
  const typedLogs: ComplianceLog[] = logs
  const typedStats: ComplianceStats | undefined = stats

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
        <TableSkeleton rows={6} />
      </div>
    )
  }

  if (isError) {
    return <ErrorState message={error?.message} onRetry={() => window.location.reload()} />
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      {typedStats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Total Logs
                </span>
                <Shield className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="text-3xl font-bold tabular-nums">{typedStats.total_logs}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Resolved
                </span>
                <CheckCircle className="h-4 w-4 text-emerald-500" />
              </div>
              <div className="text-3xl font-bold tabular-nums text-emerald-500">
                {typedStats.resolved_logs}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Unresolved
                </span>
                <Clock className="h-4 w-4 text-amber-500" />
              </div>
              <div className="text-3xl font-bold tabular-nums text-amber-500">
                {typedStats.unresolved_logs}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Severity Distribution */}
      {typedStats?.severity_distribution && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Severity Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-6">
              {Object.entries(typedStats.severity_distribution).map(
                ([severity, count]: [string, number]) => (
                  <div key={severity} className="flex items-center gap-2">
                    <Badge variant="outline" className={cn('text-xs', severityBadge[severity] || '')}>
                      {severity}
                    </Badge>
                    <span className="text-sm font-semibold tabular-nums">{count}</span>
                  </div>
                )
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Logs Table */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Compliance Logs
          </CardTitle>
        </CardHeader>
        <CardContent>
          {typedLogs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Shield className="h-10 w-10 text-emerald-500/50 mb-3" />
              <p className="text-sm font-medium text-muted-foreground">No compliance logs</p>
            </div>
          ) : (
            <div className="rounded-lg border border-border overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="w-16">ID</TableHead>
                    <TableHead>Event Type</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Timestamp</TableHead>
                    <TableHead className="w-24" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {typedLogs.map((log: ComplianceLog) => (
                    <TableRow key={log.id}>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        #{log.id}
                      </TableCell>
                      <TableCell className="text-sm font-medium">{log.event_type}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={cn('text-xs', severityBadge[log.severity] || '')}
                        >
                          {log.severity}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={cn(
                            'text-xs gap-1',
                            log.is_resolved
                              ? 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10'
                              : 'text-amber-500 border-amber-500/30 bg-amber-500/10'
                          )}
                        >
                          {log.is_resolved ? (
                            <CheckCircle className="h-3 w-3" />
                          ) : (
                            <Clock className="h-3 w-3" />
                          )}
                          {log.is_resolved ? 'Resolved' : 'Open'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground max-w-[300px] truncate">
                        {log.description}
                      </TableCell>
                      <TableCell className="text-right text-xs text-muted-foreground tabular-nums">
                        {new Date(log.timestamp).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        {!log.is_resolved && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => resolveLog.mutate(log.id)}
                            className="text-emerald-500 border-emerald-500/30 hover:bg-emerald-500/10 h-7 text-xs"
                          >
                            Resolve
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
