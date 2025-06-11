import { useRouter } from 'next/router';
import { useEffect } from 'react';

export default function IndexRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/incidents');
  }, [router]);
  return null;
}
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