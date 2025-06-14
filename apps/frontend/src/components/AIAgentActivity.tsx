import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card"
import { useAIAgentActivity } from "@/hooks/useAIAgentActivity"

export function AIAgentActivity() {
  const { data, isLoading } = useAIAgentActivity()
  if (isLoading) return <div>Loading...</div>

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <Card>
        <CardHeader>
          <CardTitle>Auto-Remediation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{data.autoRemediation.status}</div>
          <div className="text-sm text-muted-foreground">{data.autoRemediation.resolvedToday} issues resolved today</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Predictive Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{data.predictiveAnalysis.status}</div>
          <div className="text-sm text-muted-foreground">{data.predictiveAnalysis.prevented} incidents prevented</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Compliance Monitoring</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{data.complianceMonitoring.status}</div>
          <div className="text-sm text-muted-foreground">{data.complianceMonitoring.regulatoryChecks} regulatory checks passed</div>
        </CardContent>
      </Card>
    </div>
  )
}
