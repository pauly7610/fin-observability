import React, { useState } from 'react';
import { apiRequest } from '../../apiRequest';
import { Toast } from '@/components/layout/Toast';

export function AssignIncidentForm({ incidentId, onSuccess }: { incidentId: string; onSuccess: () => void }) {
  const [assignee, setAssignee] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      await apiRequest(`/incidents/${incidentId}/assign`, {
        method: 'POST',
        body: JSON.stringify({ assignee }),
      });
      setSuccess(true);
      onSuccess();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  return (
    <form onSubmit={handleAssign} className="flex items-center gap-2">
      <input
        type="text"
        placeholder="Assign to..."
        value={assignee}
        onChange={e => setAssignee(e.target.value)}
        className="px-2 py-1 border rounded"
        required
      />
      <button type="submit" disabled={loading} className="bg-accent-info text-white px-3 py-1 rounded">
        Assign
      </button>
      {success && <span className="text-green-500 ml-2">Assigned!</span>}
      {error && <span className="text-red-500 ml-2">{error}</span>}
    </form>
  );
}

export function EscalateIncidentButton({ incidentId, onSuccess }: { incidentId: string; onSuccess: () => void }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [success, setSuccess] = useState(false);
  const handleEscalate = async () => {
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      await apiRequest(`/incidents/${incidentId}/escalate`, {
        method: 'POST',
      });
      setError(null);
      setToast({ message: 'Incident escalated successfully', type: 'success' });
      onSuccess();
    } catch (err: any) {
      setError(err.message);
      setToast({ message: err.message || 'Failed to escalate incident', type: 'error' });
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="mt-2">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <button onClick={handleEscalate} disabled={loading} className="bg-accent-warning text-white px-3 py-1 rounded">
        Escalate
      </button>
      {error && <span className="text-red-500 ml-2">{error}</span>}
    </div>
  );
}

export function CommentIncidentForm({ incidentId, onSuccess }: { incidentId: string; onSuccess: () => void }) {
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [success, setSuccess] = useState(false);
  const handleComment = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      await apiRequest(`/incidents/${incidentId}/comment`, {
        method: 'POST',
        body: JSON.stringify({ comment }),
      });
      setComment('');
      setError(null);
      setToast({ message: 'Comment added successfully', type: 'success' });
      onSuccess();
    } catch (err: any) {
      setError(err.message);
      setToast({ message: err.message || 'Failed to add comment', type: 'error' });
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="mb-2">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <form onSubmit={handleComment} className="flex items-center space-x-2 mt-2">
        <input
          type="text"
          value={comment}
          onChange={e => setComment(e.target.value)}
          placeholder="Add comment..."
          className="px-2 py-1 border rounded"
        />
        <button type="submit" disabled={loading} className="bg-accent-info text-white px-2 py-1 rounded">
          Comment
        </button>
        {error && <span className="text-red-500 ml-2">{error}</span>}
      </form>
    </div>
  );
}
