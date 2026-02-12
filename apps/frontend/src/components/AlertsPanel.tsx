'use client'
import { useAlerts } from "@/hooks/useAlerts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function AlertsPanel() {
  const { data, isLoading, isError, error } = useAlerts()
  if (isLoading) return <div>Loading...</div>
  if (!data) return <div>No data available</div>
  if (isError) return <div>Error loading data: {error?.message}</div>

  return (
    <div className="space-y-4">
      {data.alerts.map((alert) => (
        <Card key={alert.id}>
          <CardHeader>
            <CardTitle>{alert.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <div>{alert.description}</div>
            <div className="text-xs text-muted-foreground">{alert.created_at}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
