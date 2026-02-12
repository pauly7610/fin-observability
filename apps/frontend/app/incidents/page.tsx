'use client'

import { useAlerts } from '@/hooks/useAlerts'
import { IncidentTable } from '@/components/IncidentTable'
import { TableSkeleton } from '@/components/CardSkeleton'
import { ErrorState } from '@/components/ErrorState'
import { AlertTriangle } from 'lucide-react'

export default function IncidentsPage() {
  const { data, isLoading, isError, error, bulkResolve } = useAlerts()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <AlertTriangle className="h-6 w-6 text-amber-500" />
            Incidents
          </h1>
          <p className="text-sm text-muted-foreground">
            Monitor, triage, and resolve incidents across your financial systems.
          </p>
        </div>
        {data?.alerts && !isError && (
          <div className="text-sm text-muted-foreground tabular-nums">
            {data.alerts.length} total
          </div>
        )}
      </div>

      {isError ? (
        <ErrorState message={error?.message} onRetry={() => window.location.reload()} />
      ) : isLoading ? (
        <TableSkeleton rows={8} />
      ) : (
        <IncidentTable
          incidents={data?.alerts || []}
          onBulkResolve={(ids) => bulkResolve.mutate(ids)}
        />
      )}
    </div>
  )
}
