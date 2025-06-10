import React, { useState } from 'react';
import { apiRequest } from '../../apiRequest';
import { Toast } from '@/components/layout/Toast';

export default function CreateExportPage() {
  const [type, setType] = useState('audit_log');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      await apiRequest('/exports', {
        method: 'POST',
        body: JSON.stringify({ type }),
      });
      setSuccess(true);
      setType('audit_log');
      setToast({ message: 'Export job started!', type: 'success' });
    } catch (err: any) {
      setError(err.message);
      setToast({ message: err.message || 'Failed to create export', type: 'error' });
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="p-8 max-w-lg mx-auto">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <h1 className="text-2xl font-bold mb-4">Create Export</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="font-semibold">Export Type:</label>
          <select value={type} onChange={e => setType(e.target.value)} className="ml-2 px-2 py-1 border rounded">
            <option value="audit_log">Audit Log</option>
            <option value="incidents">Incidents</option>
            <option value="compliance">Compliance</option>
            <option value="users">Users</option>
          </select>
        </div>
        <button type="submit" disabled={loading} className="bg-accent-primary text-white px-3 py-1 rounded">
          Create Export
        </button>
        {success && <span className="text-green-500 ml-2">Export job started!</span>}
        {error && <span className="text-red-500 ml-2">{error}</span>}
      </form>
    </div>
  );
}
