import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../apiRequest';

interface AuditLogEntry {
  id: string;
  timestamp: string;
  action: string;
  details: string;
  user: string;
  category: string;
}

const actionIcons: Record<string, string> = {
  create: '🟢',
  update: '📝',
  delete: '🗑️',
  assign: '👤',
  escalate: '⚠️',
  comment: '💬',
  resolve: '✅',
  login: '🔑',
  default: '📄',
};

const actionColors: Record<string, string> = {
  create: 'text-green-500',
  update: 'text-blue-400',
  delete: 'text-red-500',
  assign: 'text-indigo-400',
  escalate: 'text-yellow-500',
  comment: 'text-cyan-400',
  resolve: 'text-emerald-500',
  login: 'text-purple-400',
  default: 'text-gray-400',
};

function getActionKey(action: string) {
  const lower = action.toLowerCase();
  if (lower.includes('create')) return 'create';
  if (lower.includes('update') || lower.includes('edit')) return 'update';
  if (lower.includes('delete') || lower.includes('remove')) return 'delete';
  if (lower.includes('assign')) return 'assign';
  if (lower.includes('escalate')) return 'escalate';
  if (lower.includes('comment')) return 'comment';
  if (lower.includes('resolve')) return 'resolve';
  if (lower.includes('login')) return 'login';
  return 'default';
}

export function AuditTrail({ resource, resourceId }: { resource: string; resourceId: string }) {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setLoading(true);
    apiRequest<AuditLogEntry[]>(`/audit/${resource}/${resourceId}`)
      .then(setLogs)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [resource, resourceId]);

  const toggleExpand = (id: string) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="mt-8">
      <h2 className="text-lg font-semibold mb-2 flex items-center gap-2">
        <span>🕑</span> Audit Trail
      </h2>
      {loading ? (
        <div>Loading audit trail...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : logs.length === 0 ? (
        <div className="text-text-secondary">No audit entries found.</div>
      ) : (
        <ul className="divide-y divide-gray-700 bg-background-secondary rounded-lg p-2">
          {logs.map((log) => {
            const actionKey = getActionKey(log.action);
            const icon = actionIcons[actionKey] || actionIcons.default;
            const color = actionColors[actionKey] || actionColors.default;
            const isApproval = log.action?.toLowerCase().includes('approve') || log.action?.toLowerCase().includes('reject');
            const decisionReason = log.details && log.details.toLowerCase().includes('decision reason')
              ? log.details.match(/decision reason: ([^\n]+)/i)?.[1]
              : undefined;
            return (
              <li key={log.id} className={`mb-2 ${isApproval ? 'bg-green-50 dark:bg-green-900/20 border-l-4 border-green-400' : ''}`}>
                <div className="flex items-center">
                  <span className={`font-semibold mr-2 ${isApproval ? 'text-accent-success' : ''}`}>{log.action}</span>
                  <span className="text-xs text-text-secondary">{new Date(log.timestamp).toLocaleString()}</span>
                  <button
                    className="ml-2 text-xs text-accent-info underline"
                    onClick={() => toggleExpand(log.id)}
                    aria-expanded={!!expanded[log.id]}
                    aria-controls={`audit-details-${log.id}`}
                  >
                    Details
                  </button>
                </div>
                <div
                  id={`audit-details-${log.id}`}
                  className={`transition-all text-sm mt-1 ${expanded[log.id] ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0 overflow-hidden'} bg-background-primary rounded px-2 py-1 border border-background-tertiary`}
                  style={{ pointerEvents: expanded[log.id] ? 'auto' : 'none' }}
                >
                  {log.details}
                  {isApproval && decisionReason && (
                    <div className="mt-1 text-xs text-accent-info">Decision reason: {decisionReason}</div>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
