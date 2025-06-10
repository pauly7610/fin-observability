import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { apiRequest } from '../../apiRequest';
import { ResolveComplianceLogButton } from './ComplianceActions';
import { AuditTrail } from '@/components/layout/AuditTrail';
import { ComplianceApprovalStatus } from '../../components/ComplianceApprovalStatus';

interface ComplianceLog {
  id: string;
  timestamp: string;
  type: string;
  status: string;
  description?: string;
  resolved_at?: string;
}

export default function ComplianceLogDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const [log, setLog] = useState<ComplianceLog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    apiRequest<ComplianceLog>(`/compliance/logs/${id}`)
      .then(setLog)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <div className="p-8">
      <button onClick={() => router.back()} className="mb-4 text-accent-info">&larr; Back</button>
      {loading ? (
        <div>Loading compliance log...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : log ? (
        <div className="bg-background-secondary rounded shadow p-6">
          <h1 className="text-2xl font-bold mb-2">Compliance Log {log.id}</h1>
          <p className="mb-2">Type: <span className="font-semibold">{log.type}</span></p>
          <p className="mb-2">Status: <span className="font-semibold">{log.status}</span></p>
          <p className="mb-2">Description: {log.description || '-'}</p>
          <p className="mb-2">Timestamp: {new Date(log.timestamp).toLocaleString()}</p>
          <p className="mb-2">Resolved At: {log.resolved_at ? new Date(log.resolved_at).toLocaleString() : '-'}</p>
          <div className="mt-6 space-y-4">
            <ResolveComplianceLogButton logId={log.id} onSuccess={() => router.reload()} />
            {/* Approval Status */}
            <div className="mt-6">
              <ComplianceApprovalStatus logId={log.id} />
            </div>
          </div>
        </div>
      ) : (
        <div>Compliance log not found.</div>
      )}
    <AuditTrail resource="compliance" resourceId={id as string} />
    </div>
  );
}
