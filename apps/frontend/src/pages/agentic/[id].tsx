import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { apiRequest } from '../../apiRequest';
import { AuditTrail } from '@/components/layout/AuditTrail';

interface AgenticWorkflow {
  id: string;
  name: string;
  status: string;
  last_run: string;
  explainability?: string;
}

export default function AgenticWorkflowDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const [workflow, setWorkflow] = useState<AgenticWorkflow | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    apiRequest<AgenticWorkflow>(`/agentic/workflows/${id}`)
      .then(setWorkflow)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleRun = async () => {
    if (!id) return;
    setActionLoading(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      await apiRequest(`/agentic/workflows/${id}/run`, { method: 'POST' });
      setActionSuccess('Workflow run triggered!');
      // Optionally refetch workflow status
      apiRequest<AgenticWorkflow>(`/agentic/workflows/${id}`).then(setWorkflow);
    } catch (err: any) {
      setActionError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="p-8">
      <button onClick={() => router.back()} className="mb-4 text-accent-info">&larr; Back</button>
      {loading ? (
        <div>Loading workflow...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : workflow ? (
        <div className="bg-background-secondary rounded shadow p-6">
          <h1 className="text-2xl font-bold mb-2">{workflow.name}</h1>
          <p className="mb-2 text-sm text-text-secondary">ID: {workflow.id}</p>
          <p className="mb-2">Status: <span className="font-semibold">{workflow.status}</span></p>
          <p className="mb-2">Last Run: {new Date(workflow.last_run).toLocaleString()}</p>
          <p className="mb-2">Explainability: {workflow.explainability || '-'}</p>
          <div className="mt-6 space-y-4">
            <button onClick={handleRun} disabled={actionLoading} className="bg-accent-primary text-white px-3 py-1 rounded">
              Run Workflow
            </button>
            {actionSuccess && <span className="text-green-500 ml-2">{actionSuccess}</span>}
            {actionError && <span className="text-red-500 ml-2">{actionError}</span>}
          </div>
        </div>
      ) : (
        <div>Workflow not found.</div>
      )}
    <AuditTrail resource="agentic" resourceId={id as string} />
    </div>
  );
}
