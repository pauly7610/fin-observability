'use client'
import { ComplianceStatus } from "@/components/ComplianceStatus"
import { AgentComplianceMonitor } from "@/components/AgentComplianceMonitor"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"

export default function CompliancePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Compliance</h1>
      <Tabs defaultValue="status" className="w-full">
        <TabsList>
          <TabsTrigger value="status">Compliance Logs</TabsTrigger>
          <TabsTrigger value="monitor">Transaction Monitor</TabsTrigger>
        </TabsList>
        <TabsContent value="status">
          <ComplianceStatus />
        </TabsContent>
        <TabsContent value="monitor">
          <AgentComplianceMonitor />
        </TabsContent>
      </Tabs>
    </div>
  )
}
