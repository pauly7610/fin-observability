import React, { useEffect, useState } from 'react';
import { apiRequest } from '../apiRequest';

interface ComplianceLog {
  id: string;
  timestamp: string;
  type: string;
  status: string;
  description?: string;
  resolved_at?: string;
}

export default function ComplianceLogsPage() {
  const [logs, setLogs] = useState<ComplianceLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    apiRequest<ComplianceLog[]>('/compliance/logs')
      .then(setLogs)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Compliance Logs</h1>
      {loading ? (
        <div>Loading compliance logs...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : (
        <table className="min-w-full bg-background-secondary rounded shadow">
          <thead>
            <tr>
              <th className="px-4 py-2 text-left">ID</th>
              <th className="px-4 py-2 text-left">Type</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2 text-left">Description</th>
              <th className="px-4 py-2 text-left">Timestamp</th>
              <th className="px-4 py-2 text-left">Resolved At</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id} className="border-t border-gray-700">
                <td className="px-4 py-2">
                  <a href={`/compliance/${log.id}`} className="text-accent-info hover:underline">
                    {log.id}
                  </a>
                </td>
                <td className="px-4 py-2">{log.type}</td>
                <td className="px-4 py-2">{log.status}</td>
                <td className="px-4 py-2">{log.description || '-'}</td>
                <td className="px-4 py-2">{new Date(log.timestamp).toLocaleString()}</td>
                <td className="px-4 py-2">{log.resolved_at ? new Date(log.resolved_at).toLocaleString() : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
