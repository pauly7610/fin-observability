import React, { useEffect, useState, useRef } from 'react';

// Keyboard shortcut helpers
const OPS_SHORTCUTS = {
  resolve: 'r',
  escalate: 'e',
  assign: 'a',
  open: 'Enter',
  up: 'ArrowUp',
  down: 'ArrowDown',
};

import { apiRequest } from '../apiRequest';
import { IncidentDetailModal } from '@/components/incidents/IncidentDetailModal';

interface Incident {
  id: string;
  incident_id: string;
  type: string;
  title: string;
  desk: string;
  trader: string;
  priority: number;
  severity: string;
  status: string;
  root_cause?: string;
  recommended_action?: string;
  detection_method?: string;
  assigned_to?: string | number;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  last_event_timestamp?: string;
  meta?: Record<string, any>;
  description?: string;
}

interface Filter {
  type: string;
  desk: string;
  trader: string;
  severity: string;
  status: string;
  priority: string;
}

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>({
    type: '', desk: '', trader: '', severity: '', status: '', priority: ''
  });
  const [assignUser, setAssignUser] = useState<{ [id: string]: string }>({});
  const [commentText, setCommentText] = useState<{ [id: string]: string }>({});
  const [detailIncident, setDetailIncident] = useState<Incident | null>(null);
  const [selectedIncidents, setSelectedIncidents] = useState<Set<string>>(new Set());
  const [focusedIdx, setFocusedIdx] = useState(0); // keyboard focus row

  const [inlineEdit, setInlineEdit] = useState<{ [id: string]: Partial<Incident> }>({});

  // Fetch incidents function (now top-level, not inside useEffect)
  const fetchIncidents = () => {
    setLoading(true);
    const params = Object.entries(filter)
      .filter(([_, v]) => v)
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&');
    apiRequest<Incident[]>(`/incidents${params ? '?' + params : ''}`)
      .then(data => { setIncidents(data); })
      .catch(err => { setError(err.message); })
      .finally(() => { setLoading(false); });
  };

  // Real-time updates via WebSocket, fallback to polling
  useEffect(() => {
    let isMounted = true;
    let ws: WebSocket | null = null;
    let pollingInterval: NodeJS.Timeout | null = null;

    // Try WebSocket first
    try {
      const loc = window.location;
      const wsProtocol = loc.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${wsProtocol}//${loc.host}/ws/incidents`;
      ws = new window.WebSocket(wsUrl);
      ws.onopen = () => {
        // On connect, fetch full table for sync
        fetchIncidents();
      };
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setIncidents(prev => {
            // Replace or add the incident in the table
            const idx = prev.findIndex(i => i.incident_id === data.incident_id || i.id === data.id);
            if (idx >= 0) {
              const updated = [...prev];
              updated[idx] = { ...updated[idx], ...data };
              return updated;
            }
            return [data, ...prev];
          });
        } catch (e) {
          // Ignore bad events
        }
      };
      ws.onerror = ws.onclose = () => {
        // Fallback to polling if socket fails
        if (!pollingInterval) {
          pollingInterval = setInterval(fetchIncidents, 8000);
        }
      };
    } catch {
      pollingInterval = setInterval(fetchIncidents, 8000);
    }

    // Cleanup
    return () => {
      isMounted = false;
      if (ws) ws.close();
      if (pollingInterval) clearInterval(pollingInterval);
    };
  }, [filter]);

  // Keyboard shortcuts for ops actions
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) return;
      if (!incidents.length) return;
      if (e.key === OPS_SHORTCUTS.down) {
        setFocusedIdx((idx) => Math.min(idx + 1, incidents.length - 1));
        e.preventDefault();
      } else if (e.key === OPS_SHORTCUTS.up) {
        setFocusedIdx((idx) => Math.max(idx - 1, 0));
        e.preventDefault();
      } else if (e.key === OPS_SHORTCUTS.resolve) {
        const id = incidents[focusedIdx]?.incident_id || incidents[focusedIdx]?.id;
        if (id) handleAction(id, 'resolve');
      } else if (e.key === OPS_SHORTCUTS.escalate) {
        const id = incidents[focusedIdx]?.incident_id || incidents[focusedIdx]?.id;
        if (id) handleAction(id, 'escalate');
      } else if (e.key === OPS_SHORTCUTS.assign) {
        const id = incidents[focusedIdx]?.incident_id || incidents[focusedIdx]?.id;
        if (id) handleAction(id, 'assign', 'me'); // 'me' placeholder, replace with user id if available
      } else if (e.key === OPS_SHORTCUTS.open) {
        const incident = incidents[focusedIdx];
        if (incident) setDetailIncident(incident);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [incidents, focusedIdx]);

  // --- fetchIncidents must be defined before handleAction so it's in scope ---
  // Already defined above in useEffect, so move handleAction below fetchIncidents

  // Action handlers
  const handleAction = async (id: string, action: 'resolve' | 'escalate' | 'assign' | 'comment', value?: string) => {
    try {
      let body: any = {};
      if (action === 'assign') body.assigned_to = value || assignUser[id] || 'me';
      if (action === 'comment') body.comment = commentText[id] || '';
      await apiRequest(`/incidents/${id}/${action}`, {
        method: 'POST',
        body: JSON.stringify(body),
      });
      fetchIncidents();
      if (action === 'assign') setAssignUser(a => ({ ...a, [id]: '' }));
      if (action === 'comment') setCommentText(c => ({ ...c, [id]: '' }));
    } catch (e: any) {
      setError(e.message || 'Action failed');
    }
  };


  const handleInlineEdit = (id: string, field: keyof Incident, value: any) => {
    setInlineEdit(e => ({ ...e, [id]: { ...e[id], [field]: value } }));
  };

  const handleInlineSave = async (id: string) => {
    const edit = inlineEdit[id];
    if (!edit) return;
    if (edit.priority != null) await apiRequest(`/incidents/${id}/assign`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ priority: edit.priority }) });
    if (edit.status) await apiRequest(`/incidents/${id}/assign`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: edit.status }) });
    if (edit.assigned_to) await apiRequest(`/incidents/${id}/assign`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ assigned_to: edit.assigned_to }) });
    setInlineEdit(e => ({ ...e, [id]: {} }));
    setFilter(f => ({ ...f })); // Refresh
  };

  const toggleSelect = (id: string) => {
    setSelectedIncidents(sel => {
      const next = new Set(sel);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    setSelectedIncidents(new Set(incidents.map(i => i.incident_id || i.id)));
  };

  const clearSelection = () => setSelectedIncidents(new Set());

  const handleBulkAction = async (action: 'resolve' | 'escalate' | 'assign', value?: string) => {
    for (const id of Array.from(selectedIncidents)) {
      let body: any = {};
      if (action === 'assign' && value) body.assigned_to = value;
      await apiRequest(`/incidents/${id}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
    }
    clearSelection();
    setFilter(f => ({ ...f })); // Refresh
  };

  const priorities = [ '', '1', '2', '3', '4', '5' ];
  const severities = [ '', 'low', 'medium', 'high', 'critical' ];

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Incidents</h1>
      <div className="mb-4 flex flex-wrap gap-2 items-end">
        <input placeholder="Type" className="input input-sm" value={filter.type} onChange={e => setFilter(f => ({ ...f, type: e.target.value }))} />
        <input placeholder="Desk" className="input input-sm" value={filter.desk} onChange={e => setFilter(f => ({ ...f, desk: e.target.value }))} />
        <input placeholder="Trader" className="input input-sm" value={filter.trader} onChange={e => setFilter(f => ({ ...f, trader: e.target.value }))} />
        <select className="input input-sm" value={filter.severity} onChange={e => setFilter(f => ({ ...f, severity: e.target.value }))}>
          {severities.map(s => <option key={s} value={s}>{s || 'Severity'}</option>)}
        </select>
        <select className="input input-sm" value={filter.status} onChange={e => setFilter(f => ({ ...f, status: e.target.value }))}>
          <option value="">Status</option>
          <option value="open">open</option>
          <option value="investigating">investigating</option>
          <option value="resolved">resolved</option>
          <option value="closed">closed</option>
          <option value="escalated">escalated</option>
        </select>
        <select className="input input-sm" value={filter.priority} onChange={e => setFilter(f => ({ ...f, priority: e.target.value }))}>
          {priorities.map(p => <option key={p} value={p}>{p || 'Priority'}</option>)}
        </select>
        <button className="btn btn-sm" onClick={() => setFilter({ type: '', desk: '', trader: '', severity: '', status: '', priority: '' })}>Clear</button>
      </div>
      {loading ? (
        <div>Loading incidents...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-background-secondary rounded shadow">
            <thead>
              <tr>
                <th className="px-2 py-1"><input type="checkbox" checked={selectedIncidents.size === incidents.length && incidents.length > 0} onChange={e => e.target.checked ? selectAll() : clearSelection()} /></th>
                <th className="px-2 py-1">ID</th>
                <th className="px-2 py-1">Type</th>
                <th className="px-2 py-1">Title</th>
                <th className="px-2 py-1">Desk</th>
                <th className="px-2 py-1">Trader</th>
                <th className="px-2 py-1">Priority</th>
                <th className="px-2 py-1">Severity</th>
                <th className="px-2 py-1">Status</th>
                <th className="px-2 py-1">Root Cause</th>
                <th className="px-2 py-1">Recommended Action</th>
                <th className="px-2 py-1">Detection</th>
                <th className="px-2 py-1">Assigned To</th>
                <th className="px-2 py-1">Created At</th>
                <th className="px-2 py-1">Last Event</th>
                <th className="px-2 py-1">Next Best Action</th>
                <th className="px-2 py-1">Actions</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((incident, i) => {
                const id = incident.incident_id || incident.id;
                // --- Agentic/AI Suggestion logic ---
                let nextAction = '';
                let badgeClass = '';
                if (incident.status === 'open' && incident.priority === 1) {
                  nextAction = 'Escalate';
                  badgeClass = 'bg-red-700 text-white';
                } else if (incident.status === 'open') {
                  nextAction = 'Assign or Investigate';
                  badgeClass = 'bg-yellow-600 text-white';
                } else if (incident.status === 'investigating') {
                  nextAction = 'Comment or Escalate';
                  badgeClass = 'bg-blue-700 text-white';
                } else if (incident.status === 'escalated') {
                  nextAction = 'Notify Mgmt';
                  badgeClass = 'bg-pink-700 text-white';
                } else if (incident.status === 'resolved') {
                  nextAction = 'Close';
                  badgeClass = 'bg-green-700 text-white';
                } else {
                  nextAction = 'Review';
                  badgeClass = 'bg-gray-600 text-white';
                }
                const isFocused = focusedIdx === i;
                return (
                  <tr
                    key={id}
                    className={
                      `${incident.priority === 1 ? "bg-red-900 text-white" : "border-t border-gray-700"} ` +
                      (isFocused ? 'ring-2 ring-accent-info z-10' : '')
                    }
                    tabIndex={0}
                    aria-selected={isFocused}
                  >
                    <td className="px-2 py-1"><input type="checkbox" checked={selectedIncidents.has(id)} onChange={() => toggleSelect(id)} /></td>
                    <td className="px-2 py-1">{id}</td>
                    <td className="px-2 py-1">{incident.type}</td>
                    <td className="px-2 py-1">
                      <button
                        className="text-accent-info hover:underline text-left w-full"
                        style={{ background: 'none', border: 'none', padding: 0, margin: 0, cursor: 'pointer' }}
                        onClick={() => setDetailIncident(incident)}
                      >
                        {incident.title}
                      </button>
                    </td>
                    <td className={`px-2 py-1 font-semibold text-xs rounded ${badgeClass}`}>{nextAction}</td>
                    <td className="px-2 py-1">{incident.desk}</td>
                    <td className="px-2 py-1">{incident.trader}</td>
                    <td className="px-2 py-1 font-bold">
                      <select value={inlineEdit[id]?.priority ?? incident.priority} onChange={e => handleInlineEdit(id, 'priority', Number(e.target.value))} className="input input-xs w-16">
                        {[1,2,3,4,5].map(p => <option key={p} value={p}>{p}</option>)}
                      </select>
                      <button className="btn btn-xs ml-1" onClick={() => handleInlineSave(id)}>Save</button>
                    </td>
                    <td className="px-2 py-1">{incident.severity}</td>
                    <td className="px-2 py-1">
                      <select value={inlineEdit[id]?.status ?? incident.status} onChange={e => handleInlineEdit(id, 'status', e.target.value)} className="input input-xs w-24">
                        {['open','investigating','resolved','closed','escalated'].map(s => <option key={s} value={s}>{s}</option>)}
                      </select>
                      <button className="btn btn-xs ml-1" onClick={() => handleInlineSave(id)}>Save</button>
                    </td>
                    <td className="px-2 py-1">{incident.root_cause}</td>
                    <td className="px-2 py-1">{incident.recommended_action}</td>
                    <td className="px-2 py-1">{incident.detection_method}</td>
                    <td className="px-2 py-1">
                      <input className="input input-xs w-16" value={inlineEdit[id]?.assigned_to ?? incident.assigned_to ?? ''} onChange={e => handleInlineEdit(id, 'assigned_to', e.target.value)} />
                      <button className="btn btn-xs ml-1" onClick={() => handleInlineSave(id)}>Save</button>
                    </td>
                    <td className="px-2 py-1">{new Date(incident.created_at).toLocaleString()}</td>
                    <td className="px-2 py-1">{incident.last_event_timestamp ? new Date(incident.last_event_timestamp).toLocaleString() : '-'}</td>
                    <td className="px-2 py-1 flex flex-col gap-1">
                      <button className="btn btn-xs btn-success" onClick={() => handleAction(id, 'resolve')}>Resolve</button>
                      <button className="btn btn-xs btn-warning" onClick={() => handleAction(id, 'escalate')}>Escalate</button>
                      <div className="flex gap-1 mt-1">
                        <input
                          className="input input-xs"
                          placeholder="User ID"
                          value={assignUser[id] || ''}
                          onChange={e => setAssignUser(a => ({ ...a, [id]: e.target.value }))}
                          style={{ width: 60 }}
                        />
                        <button className="btn btn-xs btn-info" onClick={() => handleAction(id, 'assign')}>Assign</button>
                      </div>
                      <div className="flex gap-1 mt-1">
                        <input
                          className="input input-xs"
                          placeholder="Comment"
                          value={commentText[id] || ''}
                          onChange={e => setCommentText(c => ({ ...c, [id]: e.target.value }))}
                          style={{ width: 100 }}
                        />
                        <button className="btn btn-xs btn-accent" onClick={() => handleAction(id, 'comment')}>Comment</button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {/* Bulk actions bar */}
          {selectedIncidents.size > 0 && (
            <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-gray-800 text-white rounded shadow-lg px-6 py-3 flex gap-4 items-center z-50">
              <span>{selectedIncidents.size} selected</span>
              <button className="btn btn-sm btn-success" onClick={() => handleBulkAction('resolve')}>Bulk Resolve</button>
              <button className="btn btn-sm btn-warning" onClick={() => handleBulkAction('escalate')}>Bulk Escalate</button>
              <input className="input input-xs w-20" placeholder="Assign User" onChange={e => setAssignUser(a => ({ ...a, bulk: e.target.value }))} value={assignUser.bulk || ''} />
              <button className="btn btn-sm btn-info" onClick={() => handleBulkAction('assign', assignUser.bulk)}>Bulk Assign</button>
              <button className="btn btn-sm btn-ghost" onClick={clearSelection}>Clear</button>
            </div>
          )}
        </div>
      )}
      {detailIncident && (
        <IncidentDetailModal incident={detailIncident} onClose={() => setDetailIncident(null)} />
      )}
    </div>
  );
}
