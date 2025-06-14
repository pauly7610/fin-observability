import { useSystems } from "@/hooks/useSystems"
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card"

export function SystemHealth() {
  const { data, isLoading } = useSystems()
  if (isLoading) return <div>Loading...</div>

  return (
    <div className="space-y-4">
      {data.systems.map((system: { id: string; name: string; status: string }) => (
        <Card key={system.id}>
          <CardHeader>
            <CardTitle>{system.name}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{system.status}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
