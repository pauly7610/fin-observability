import React, { useEffect, useState } from 'react';
import { apiRequest } from '../apiRequest';

interface AgenticWorkflow {
  id: string;
  name: string;
  status: string;
  last_run: string;
  explainability?: string;
}

export default function AgenticWorkflowsPage() {
  const [workflows, setWorkflows] = useState<AgenticWorkflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    apiRequest<AgenticWorkflow[]>('/agentic/workflows')
      .then(setWorkflows)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Agentic Workflows</h1>
      {loading ? (
        <div>Loading workflows...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : (
        <table className="min-w-full bg-background-secondary rounded shadow">
          <thead>
            <tr>
              <th className="px-4 py-2 text-left">Name</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2 text-left">Last Run</th>
              <th className="px-4 py-2 text-left">Explainability</th>
            </tr>
          </thead>
          <tbody>
            {workflows.map((wf) => (
              <tr key={wf.id} className="border-t border-gray-700">
                <td className="px-4 py-2">
                  <a href={`/agentic/${wf.id}`} className="text-accent-info hover:underline">
                    {wf.name}
                  </a>
                </td>
                <td className="px-4 py-2">{wf.status}</td>
                <td className="px-4 py-2">{new Date(wf.last_run).toLocaleString()}</td>
                <td className="px-4 py-2">{wf.explainability || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
