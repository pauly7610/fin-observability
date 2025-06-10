import React, { useEffect, useState } from 'react';
import { apiRequest } from '../apiRequest';
import { ApprovalActions } from '../components/ApprovalActions';

/**
 * ApprovalRequest describes the shape of an approval request object as
 * returned by the backend API.
 */
interface ApprovalRequest {
  id: number;
  resource_type: string;
  resource_id: string;
  requested_by: number;
  status: string;
  reason: string;
  decision_by?: number;
  decision_reason?: string;
  created_at: string;
  decided_at?: string;
  meta?: Record<string, any>;
}

/**
 * ApprovalsPage renders the approvals dashboard, listing all approval
 * requests with filtering by status. Allows privileged users to take
 * actions inline. Refreshes automatically after actions.
 */
export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [status, setStatus] = useState<string>('pending');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    apiRequest<ApprovalRequest[]>(`/approval/?status=${status}`)
      .then(setApprovals)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [status]);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Approval Requests</h1>
      <div className="mb-4">
        <label className="mr-2">Filter by status:</label>
        <select value={status} onChange={e => setStatus(e.target.value)} className="border rounded px-2 py-1">
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="escalated">Escalated</option>
          <option value="">All</option>
        </select>
      </div>
      {loading ? (
        <div>Loading approvals...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : (
        <table className="min-w-full bg-background-secondary rounded shadow">
          <thead>
            <tr>
              <th className="px-4 py-2 text-left">ID</th>
              <th className="px-4 py-2 text-left">Resource</th>
              <th className="px-4 py-2 text-left">Requested By</th>
              <th className="px-4 py-2 text-left">Reason</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2 text-left">Created</th>
              <th className="px-4 py-2 text-left">Decision</th>
            </tr>
          </thead>
          <tbody>
            {approvals.map(a => (
              <tr key={a.id} className="border-t border-gray-700 align-top">
                <td className="px-4 py-2">{a.id}</td>
                <td className="px-4 py-2">{a.resource_type} <span className="text-xs text-text-secondary">({a.resource_id})</span></td>
                <td className="px-4 py-2">{a.requested_by}</td>
                <td className="px-4 py-2">{a.reason}</td>
                <td className="px-4 py-2 font-semibold capitalize">{a.status}</td>
                <td className="px-4 py-2">{new Date(a.created_at).toLocaleString()}</td>
                <td className="px-4 py-2">
                  {a.status === 'pending' ? (
                    <ApprovalActions approvalId={a.id} onAction={() => {
                      // Refresh approvals after action
                      apiRequest<ApprovalRequest[]>(`/approval/?status=${status}`).then(setApprovals);
                    }} />
                  ) : (
                    a.decision_reason || '-'
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
