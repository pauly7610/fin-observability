import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { MetricsOverview } from "@/components/MetricsOverview"
import { AIAgentActivity } from "@/components/AIAgentActivity"
import { AlertsPanel } from "@/components/AlertsPanel"
import { ComplianceStatus } from "@/components/ComplianceStatus"
import { SystemHealth } from "@/components/SystemHealth"
import { AgentComplianceMonitor } from "@/components/AgentComplianceMonitor"
import { useMockScenarios } from '@/hooks/useMockScenarios';
import { useMockAuditTrail } from '@/hooks/useMockAuditTrail';
import React from 'react';

export default function DashboardPage() {
  const { data: scenarios, isLoading: loadingScenarios } = useMockScenarios();
  const { data: auditTrail, isLoading: loadingAudit } = useMockAuditTrail();

  return (
    <Tabs defaultValue="overview" className="w-full">
      <TabsList>
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="alerts">Alerts</TabsTrigger>
        <TabsTrigger value="compliance">Compliance</TabsTrigger>
        <TabsTrigger value="compliance-monitor">Compliance Monitor</TabsTrigger>
        <TabsTrigger value="systems">Systems</TabsTrigger>
      </TabsList>
      <TabsContent value="overview">
        <MetricsOverview />
        <AIAgentActivity />
      </TabsContent>
      <TabsContent value="alerts">
        <AlertsPanel />
      </TabsContent>
      <TabsContent value="compliance">
        <ComplianceStatus />
      </TabsContent>
      <TabsContent value="systems">
        <SystemHealth />
      </TabsContent>
      <TabsContent value="compliance-monitor">
        <AgentComplianceMonitor />
      </TabsContent>
    </Tabs>
  )
}
