import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { apiRequest } from '../../apiRequest';
import { Toast } from '@/components/layout/Toast';
import { AuditTrail } from '@/components/layout/AuditTrail';
import { UserApprovalStatus } from '../../components/UserApprovalStatus';

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  status: string;
}

export default function UserDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [role, setRole] = useState('');
  const [status, setStatus] = useState('');
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    apiRequest<User>(`/users/${id}`)
      .then((u) => {
        setUser(u);
        setRole(u.role);
        setStatus(u.status);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setSaving(true);
    setToast(null);
    try {
      await apiRequest(`/users/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ role, status }),
      });
      setToast({ message: 'User updated successfully', type: 'success' });
    } catch (err: any) {
      setError(err.message);
      setToast({ message: err.message || 'Failed to update user', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      <h1 className="text-2xl font-bold mb-4">User Detail</h1>
      {/* Approval Status */}
      <div className="mb-6">
        <UserApprovalStatus userId={id as string} />
      </div>
      <button onClick={() => router.back()} className="mb-4 text-accent-info">&larr; Back</button>
      {loading ? (
        <div>Loading user...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : user ? (
        <div className="bg-background-secondary rounded shadow p-6">
          <h1 className="text-2xl font-bold mb-2">{user.username}</h1>
          <p className="mb-2 text-sm text-text-secondary">ID: {user.id}</p>
          <p className="mb-2">Email: {user.email}</p>
          <form onSubmit={handleSave} className="space-y-4 mt-4">
            <div>
              <label className="font-semibold">Role:</label>
              <select value={role} onChange={(e) => setRole(e.target.value)} className="ml-2 px-2 py-1 border rounded">
                <option value="admin">Admin</option>
                <option value="user">User</option>
                <option value="auditor">Auditor</option>
              </select>
            </div>
            <div>
              <label className="font-semibold">Status:</label>
              <select value={status} onChange={e => setStatus(e.target.value)} className="ml-2 px-2 py-1 border rounded">
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            <button type="submit" disabled={saving} className="bg-accent-primary text-white px-3 py-1 rounded">
              Save
            </button>
          </form>
        </div>
      ) : (
        <div>User not found.</div>
      )}
    <AuditTrail resource="users" resourceId={id as string} />
    </div>
  );
}
