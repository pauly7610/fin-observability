import React, { useEffect, useState } from 'react';
import { apiRequest } from '../apiRequest';

interface ExportJob {
  id: string;
  type: string;
  status: string;
  created_at: string;
  completed_at?: string;
  download_url?: string;
}

export default function ExportsPage() {
  const [exports, setExports] = useState<ExportJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    apiRequest<ExportJob[]>('/exports')
      .then(setExports)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Exports</h1>
        <a href="/exports/create" className="bg-accent-primary text-white px-4 py-2 rounded hover:bg-accent-info transition-colors">+ Create Export</a>
      </div>
      {loading ? (
        <div>Loading exports...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : (
        <table className="min-w-full bg-background-secondary rounded shadow">
          <thead>
            <tr>
              <th className="px-4 py-2 text-left">Type</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2 text-left">Created At</th>
              <th className="px-4 py-2 text-left">Completed At</th>
              <th className="px-4 py-2 text-left">Download</th>
            </tr>
          </thead>
          <tbody>
            {exports.map((job) => (
              <tr key={job.id} className="border-t border-gray-700">
                <td className="px-4 py-2">{job.type}</td>
                <td className="px-4 py-2">{job.status}</td>
                <td className="px-4 py-2">{new Date(job.created_at).toLocaleString()}</td>
                <td className="px-4 py-2">{job.completed_at ? new Date(job.completed_at).toLocaleString() : '-'}</td>
                <td className="px-4 py-2">
                  {job.download_url ? (
                    <a href={job.download_url} className="text-accent-info hover:underline" download>
                      Download
                    </a>
                  ) : (
                    <span>'-'</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
