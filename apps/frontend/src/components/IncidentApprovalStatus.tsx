import React, { useEffect, useState } from 'react';
import { apiRequest } from '../apiRequest';
import { ApprovalActions } from './ApprovalActions';

interface IncidentApprovalStatusProps {
  incidentId: string;
}

interface ApprovalRequest {
  id: number;
  status: string;
  reason: string;
  decision_reason?: string;
  created_at: string;
  decided_at?: string;
}

export const IncidentApprovalStatus: React.FC<IncidentApprovalStatusProps> = ({ incidentId }) => {
  const [approval, setApproval] = useState<ApprovalRequest | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    apiRequest<ApprovalRequest[]>(`/approval/?resource_type=incident_export&resource_id=${incidentId}`)
      .then((approvals) => setApproval(approvals && approvals.length > 0 ? approvals[0] : null))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [incidentId]);

  if (loading) return <div className="text-xs text-text-secondary">Loading approval status...</div>;
  if (error) return <div className="text-xs text-red-500">{error}</div>;
  if (!approval) return <div className="text-xs text-text-secondary">No approval required or found.</div>;

  return (
    <div className="mt-4 p-3 bg-background-primary rounded shadow">
      <div className="font-semibold text-sm mb-1">Export Approval Status:</div>
      <div className="flex items-center gap-2">
        <span className="capitalize font-bold text-accent-info">{approval.status}</span>
        <span className="text-xs text-text-secondary">Created: {new Date(approval.created_at).toLocaleString()}</span>
        {approval.decided_at && <span className="text-xs text-text-secondary">Decided: {new Date(approval.decided_at).toLocaleString()}</span>}
      </div>
      <div className="text-xs text-text-secondary mt-1">Reason: {approval.reason}</div>
      {approval.status === 'pending' && (
        <ApprovalActions approvalId={approval.id} onAction={() => {
          // Refresh approval after action
          apiRequest<ApprovalRequest[]>(`/approval/?resource_type=incident_export&resource_id=${incidentId}`).then((approvals) => setApproval(approvals && approvals.length > 0 ? approvals[0] : null));
        }} />
      )}
      {approval.status !== 'pending' && approval.decision_reason && (
        <div className="text-xs mt-2">Decision reason: {approval.decision_reason}</div>
      )}
    </div>
  );
};
