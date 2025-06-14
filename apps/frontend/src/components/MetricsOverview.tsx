import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useMetrics } from "@/hooks/useMetrics"

export function MetricsOverview() {
  const { data, isLoading } = useMetrics()
  if (isLoading) return <div>Loading...</div>

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 my-6">
      <Card>
        <CardHeader>
          <CardTitle>System Uptime</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold">{data.uptime}%</div>
          <div className="text-sm text-muted-foreground">Last 30 days</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Active Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold">{data.activeAlerts}</div>
          <div className="text-sm text-muted-foreground">Noise reduced: {data.noiseReduction}%</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>MTTR</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold">{data.mttr} min</div>
          <div className="text-sm text-muted-foreground">Improved by {data.mttrImprovement}%</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Compliance Score</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold">{data.complianceScore}</div>
          <div className="text-sm text-muted-foreground">{data.complianceStatus}</div>
        </CardContent>
      </Card>
    </div>
  )
}
