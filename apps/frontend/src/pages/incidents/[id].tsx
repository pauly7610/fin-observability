import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { apiRequest } from '../../apiRequest';
import { AssignIncidentForm, EscalateIncidentButton, CommentIncidentForm } from './IncidentActions';
import { AuditTrail } from '@/components/layout/AuditTrail';

interface Incident {
  id: string;
  title: string;
  status: string;
  assigned_to?: string;
  created_at: string;
  description?: string;
}

export default function IncidentDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    apiRequest<Incident>(`/incidents/${id}`)
      .then(setIncident)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <div className="p-8">
      <button onClick={() => router.back()} className="mb-4 text-accent-info">&larr; Back</button>
      {loading ? (
        <div>Loading incident...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : incident ? (
        <div className="bg-background-secondary rounded shadow p-6">
          <h1 className="text-2xl font-bold mb-2">{incident.title}</h1>
          <p className="mb-2 text-sm text-text-secondary">ID: {incident.id}</p>
          <p className="mb-2">Status: <span className="font-semibold">{incident.status}</span></p>
          <p className="mb-2">Assigned To: {incident.assigned_to || '-'}</p>
          <p className="mb-2">Created At: {new Date(incident.created_at).toLocaleString()}</p>
          <p className="mb-2">Description: {incident.description || '-'}</p>
          <div className="mt-6 space-y-4">
            {/* Assign Action */}
            <AssignIncidentForm incidentId={incident.id} onSuccess={() => router.reload()} />
            {/* Escalate Action */}
            <EscalateIncidentButton incidentId={incident.id} onSuccess={() => router.reload()} />
            {/* Comment Action */}
            <CommentIncidentForm incidentId={incident.id} onSuccess={() => router.reload()} />
          </div>
        </div>
      ) : (
        <div>Incident not found.</div>
      )}
    <AuditTrail resource="incidents" resourceId={id as string} />
    </div>
  );
}
