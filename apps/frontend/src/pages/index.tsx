import React, { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { SystemStatus } from '@/components/layout/SystemStatus';
import { AuditLogPanel } from '@/components/layout/AuditLogPanel';
import { apiRequest } from '../apiRequest';

export default function Dashboard() {
  const [metrics, setMetrics] = useState([]);
  const [metricsLoading, setMetricsLoading] = useState(true);
  const [metricsError, setMetricsError] = useState<string | null>(null);

  const [auditLogs, setAuditLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(true);
  const [logsError, setLogsError] = useState<string | null>(null);

  useEffect(() => {
    setMetricsLoading(true);
    apiRequest('/system_metrics/')
      .then((data) => setMetrics(data))
      .catch((err) => setMetricsError(err.message))
      .finally(() => setMetricsLoading(false));
  }, []);

  useEffect(() => {
    setLogsLoading(true);
    apiRequest('/compliance/logs')
      .then((data) => setAuditLogs(data))
      .catch((err) => setLogsError(err.message))
      .finally(() => setLogsLoading(false));
  }, []);

  // TODO: Replace mockTasks and mockCommands with real data as you build more features

  const mockTasks = [
    {
      id: '1',
      title: 'Investigate CPU spike',
      status: 'ongoing' as const,
      owner: 'agent' as const,
      nextAction: 'Analyzing metrics',
    },
    {
      id: '2',
      title: 'Review compliance report',
      status: 'pending' as const,
      owner: 'human' as const,
      nextAction: 'Waiting for approval',
    },
    {
      id: '3',
      title: 'Update security policies',
      status: 'completed' as const,
      owner: 'agent' as const,
      nextAction: 'Completed',
    },
  ];

  const mockCommands = [
    {
      id: '1',
      title: 'Create new incident',
      description: 'Start a new incident investigation',
      category: 'system' as const,
      action: () => console.log('Create incident'),
    },
    {
      id: '2',
      title: 'Run compliance check',
      description: 'Initiate compliance verification',
      category: 'agent' as const,
      action: () => console.log('Run compliance check'),
    },
  ];

  return (
    <DashboardLayout>
      <div className="flex-1 p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-2">Dashboard</h1>
          <p className="text-text-secondary">
            Welcome to the Financial AI Observability Platform
          </p>
        </div>

        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-2">System Status</h2>
          {metricsLoading ? (
            <div>Loading system metrics...</div>
          ) : metricsError ? (
            <div className="text-red-500">{metricsError}</div>
          ) : (
            <SystemStatus metrics={metrics} lastUpdated={new Date()} />
          )}
        </div>

        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-2">Audit Log</h2>
          {logsLoading ? (
            <div>Loading audit logs...</div>
          ) : logsError ? (
            <div className="text-red-500">{logsError}</div>
          ) : (
            <AuditLogPanel entries={auditLogs} />
          )}
        </div>

        {/* Add more dashboard widgets here */}
      </div>
    </DashboardLayout>
  );
}