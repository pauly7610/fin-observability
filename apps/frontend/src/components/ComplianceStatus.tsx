import { useCompliance } from "@/hooks/useCompliance"
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card"

export function ComplianceStatus() {
  const { data, isLoading } = useCompliance()
  if (isLoading) return <div>Loading...</div>

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Compliance Score</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold">{data.score}</div>
          <div className="text-sm text-muted-foreground">{data.status}</div>
        </CardContent>
      </Card>
      {/* Add more compliance cards as needed */}
    </div>
  )
}
