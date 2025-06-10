import React, { useState } from 'react';
import { apiRequest } from '../../apiRequest';
import { Toast } from '@/components/layout/Toast';

export function ResolveComplianceLogButton({ logId, onSuccess }: { logId: string; onSuccess: () => void }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [success, setSuccess] = useState(false);
  const handleResolve = async () => {
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      await apiRequest(`/compliance/logs/${logId}/resolve`, { method: 'POST' });
      setError(null);
      setToast({ message: 'Compliance log resolved successfully', type: 'success' });
      setSuccess(true);
      onSuccess();
    } catch (err: any) {
      setError(err.message);
      setToast({ message: err.message || 'Failed to resolve compliance log', type: 'error' });
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="mb-2">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <button onClick={handleResolve} disabled={loading} className="bg-accent-success text-white px-3 py-1 rounded mt-2">
        Resolve
        {success && <span className="text-green-500 ml-2">Resolved!</span>}
        {error && <span className="text-red-500 ml-2">{error}</span>}
      </button>
    </div>
  );
}
