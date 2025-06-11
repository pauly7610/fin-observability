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
    <div className="p-4 sm:p-8">
      <div className="mb-4">
        <h1 className="text-2xl font-bold">Exports</h1>
        <p className="text-sm text-gray-400 mt-1 mb-2">
          Export incident and trading data for <span className="font-semibold">compliance</span>, <span className="font-semibold">audit</span>, or regulatory review. Exports are cryptographically signed and include SIEM metadata.
        </p>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <a href="/exports/create" className="bg-accent-primary text-white px-4 py-2 rounded hover:bg-accent-info transition-colors w-full sm:w-auto text-center">+ Create Export</a>
        </div>
      </div>
      {loading ? (
        <div>Loading exports...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-background-secondary rounded shadow text-sm">
            <thead>
              <tr>
                <th className="px-2 py-2 text-left whitespace-nowrap">Type</th>
                <th className="px-2 py-2 text-left whitespace-nowrap">Status</th>
                <th className="px-2 py-2 text-left whitespace-nowrap">Created At</th>
                <th className="px-2 py-2 text-left whitespace-nowrap">Completed At</th>
                <th className="px-2 py-2 text-left whitespace-nowrap">Download</th>
              </tr>
            </thead>
            <tbody>
              {exports.map((job) => (
                <tr key={job.id} className="border-t border-gray-700">
                  <td className="px-2 py-2 whitespace-nowrap">{job.type}</td>
                  <td className="px-2 py-2 whitespace-nowrap">{job.status}</td>
                  <td className="px-2 py-2 whitespace-nowrap">{new Date(job.created_at).toLocaleString()}</td>
                  <td className="px-2 py-2 whitespace-nowrap">{job.completed_at ? new Date(job.completed_at).toLocaleString() : '-'}</td>
                  <td className="px-2 py-2 whitespace-nowrap">
                    {job.download_url ? (
                      <a href={job.download_url} className="text-accent-info hover:underline" download>
                        Download
                      </a>
                    ) : (
                      <span>-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

