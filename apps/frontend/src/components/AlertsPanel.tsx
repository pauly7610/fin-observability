import { useAlerts } from "@/hooks/useAlerts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function AlertsPanel() {
  const { data, isLoading } = useAlerts()
  if (isLoading) return <div>Loading...</div>

  return (
    <div className="space-y-4">
      {data.alerts.map((alert: { id: string; title: string; description: string; timestamp: string }) => (
        <Card key={alert.id}>
          <CardHeader>
            <CardTitle>{alert.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <div>{alert.description}</div>
            <div className="text-xs text-muted-foreground">{alert.timestamp}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
