import React, { useEffect, useState } from 'react';
import { apiRequest } from '../apiRequest';

interface Incident {
  id: string;
  title: string;
  status: string;
  assigned_to?: string;
  created_at: string;
  description?: string;
}

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    apiRequest<Incident[]>('/incidents/')
      .then(setIncidents)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Incidents</h1>
      {loading ? (
        <div>Loading incidents...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : (
        <table className="min-w-full bg-background-secondary rounded shadow">
          <thead>
            <tr>
              <th className="px-4 py-2 text-left">ID</th>
              <th className="px-4 py-2 text-left">Title</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2 text-left">Assigned To</th>
              <th className="px-4 py-2 text-left">Created At</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((incident) => (
              <tr key={incident.id} className="border-t border-gray-700">
                <td className="px-4 py-2">{incident.id}</td>
                <td className="px-4 py-2">
                  <a href={`/incidents/${incident.id}`} className="text-accent-info hover:underline">
                    {incident.title}
                  </a>
                </td>
                <td className="px-4 py-2">{incident.status}</td>
                <td className="px-4 py-2">{incident.assigned_to || '-'}</td>
                <td className="px-4 py-2">{new Date(incident.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
