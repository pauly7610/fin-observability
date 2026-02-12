'use client'
import { ComplianceStatus } from "@/components/ComplianceStatus"
import { AgentComplianceMonitor } from "@/components/AgentComplianceMonitor"
import { ModelManagement } from "@/components/ModelManagement"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"

export default function CompliancePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Compliance</h1>
        <p className="text-sm text-muted-foreground">
          Monitor compliance logs, transaction checks, and model management.
        </p>
      </div>
      <Tabs defaultValue="status" className="w-full">
        <TabsList>
          <TabsTrigger value="status">Compliance Logs</TabsTrigger>
          <TabsTrigger value="monitor">Transaction Monitor</TabsTrigger>
          <TabsTrigger value="models">Model Management</TabsTrigger>
        </TabsList>
        <TabsContent value="status">
          <ComplianceStatus />
        </TabsContent>
        <TabsContent value="monitor">
          <AgentComplianceMonitor />
        </TabsContent>
        <TabsContent value="models">
          <ModelManagement />
        </TabsContent>
      </Tabs>
    </div>
  )
}
