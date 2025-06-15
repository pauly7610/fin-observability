'use client'
import { useCompliance } from "@/hooks/useCompliance"
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card"
import { ComplianceLog, ComplianceStats } from "@/types/api"

export function ComplianceStatus() {
  const { logs, stats, isLoading, isError, error, resolveLog } = useCompliance()
  const typedLogs: ComplianceLog[] = logs
  const typedStats: ComplianceStats | undefined = stats
  if (isLoading) return <div>Loading...</div>
  if (isError) return <div>Error loading data: {error?.message}</div>

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Compliance Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          {typedStats ? (
            <>
              <div><b>Total Logs:</b> {typedStats.total_logs}</div>
              <div><b>Resolved Logs:</b> {typedStats.resolved_logs}</div>
              <div><b>Unresolved Logs:</b> {typedStats.unresolved_logs}</div>
              <div><b>Severity Distribution:</b></div>
              <ul className="ml-4">
                {typedStats.severity_distribution && Object.entries(typedStats.severity_distribution).map(([severity, count]: [string, number]) => (
                  <li key={severity}>{severity}: {count}</li>
                ))}
              </ul>
            </>
          ) : (
            <div>No stats available.</div>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Compliance Logs</CardTitle>
        </CardHeader>
        <CardContent>
          {typedLogs.length === 0 ? (
            <div>No compliance logs available.</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Event Type</th>
                  <th>Severity</th>
                  <th>Resolved</th>
                  <th>Timestamp</th>
                  <th>Description</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {typedLogs.map((log: ComplianceLog) => (
                  <tr key={log.id}>
                    <td>{log.id}</td>
                    <td>{log.event_type}</td>
                    <td>{log.severity}</td>
                    <td>{log.is_resolved ? 'Yes' : 'No'}</td>
                    <td>{log.timestamp}</td>
                    <td>{log.description}</td>
                    <td>
                      {!log.is_resolved && (
                        <button className="px-2 py-1 bg-green-500 text-white rounded" onClick={() => resolveLog.mutate(log.id)}>
                          Resolve
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
