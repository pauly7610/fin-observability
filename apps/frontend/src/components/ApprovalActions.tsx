import React, { useState } from 'react';
import { apiRequest } from '../apiRequest';

/**
 * Props for ApprovalActions component.
 * @property approvalId - The ID of the approval request.
 * @property onAction - Optional callback after an action is taken.
 */
interface ApprovalActionsProps {
  approvalId: number;
  onAction?: () => void;
}

/**
 * Renders approve/reject buttons for an approval request. Only users with
 * 'admin', 'compliance', or 'analyst' roles can take actions. Submits
 * decisions to the backend API and provides inline feedback.
 */
export const ApprovalActions: React.FC<ApprovalActionsProps> = ({ approvalId, onAction }) => {
  const [decisionReason, setDecisionReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Determine the user's role. Prefer context/prop if available; otherwise,
  // fallback to localStorage. Only allow actions for privileged roles.
  let userRole = undefined;
  if (typeof window !== 'undefined') {
    userRole = window.localStorage.getItem('userRole');
  }
  const canApprove = ['admin', 'compliance', 'analyst'].includes(userRole || '');

  const handleDecision = async (decision: 'approved' | 'rejected') => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await apiRequest(`/approval/${approvalId}/decision`, {
        method: 'POST',
        body: JSON.stringify({
          decision,
          decision_reason: decisionReason,
        }),
        headers: { 'Content-Type': 'application/json' },
      });
      setSuccess(`Approval ${decision}`);
      setDecisionReason('');
      if (onAction) onAction();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-2 mt-2">
      <textarea
        className="border rounded px-2 py-1 text-sm"
        placeholder="Decision reason (optional)"
        value={decisionReason}
        onChange={e => setDecisionReason(e.target.value)}
        rows={2}
        disabled={!canApprove}
      />
      {canApprove ? (
        <div className="flex gap-2">
          <button
            className="bg-green-600 text-white rounded px-3 py-1 hover:bg-green-700"
            onClick={() => handleDecision('approved')}
            disabled={loading}
          >
            Approve
          </button>
          <button
            className="bg-red-600 text-white rounded px-3 py-1 hover:bg-red-700"
            onClick={() => handleDecision('rejected')}
            disabled={loading}
          >
            Reject
          </button>
        </div>
      ) : (
        <div className="text-xs text-text-secondary">You do not have permission to approve or reject this request.</div>
      )}
      {error && <div className="text-red-500 text-xs">{error}</div>}
      {success && <div className="text-green-500 text-xs">{success}</div>}
    </div>
  );
};
