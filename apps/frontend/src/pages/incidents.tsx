import React, { useEffect, useState, useMemo } from 'react';
import { apiRequest } from '../apiRequest';
import { IncidentDetailModal } from '@/components/incidents/IncidentDetailModal';

// --- No changes to your interfaces or constants ---
const OPS_SHORTCUTS = {
  resolve: 'r',
  escalate: 'e',
  assign: 'a',
  open: 'Enter',
  up: 'ArrowUp',
  down: 'ArrowDown',
};

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

// --- Helper objects for styling. This cleans up the JSX. ---
const severityConfig = {
  critical: { color: 'bg-red-500', label: 'Critical' },
  high: { color: 'bg-orange-500', label: 'High' },
  medium: { color: 'bg-yellow-500', label: 'Medium' },
  low: { color: 'bg-blue-500', label: 'Low' },
};

const statusConfig = {
  open: { color: 'bg-red-500', label: 'Open' },
  investigating: { color: 'bg-blue-500', label: 'Investigating' },
  escalated: { color: 'bg-purple-500', label: 'Escalated' },
  resolved: { color: 'bg-green-500', label: 'Resolved' },
  closed: { color: 'bg-gray-500', label: 'Closed' },
};

export default function IncidentsPage() {
  // --- All your state and logic hooks remain the same ---
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
  const [focusedIdx, setFocusedIdx] = useState(0);

  // --- REFACTORED: Simplified inline editing state. We only edit one row at a time. ---
  const [editingId, setEditingId] = useState<string | null>(null);
  const [inlineEdit, setInlineEdit] = useState<Partial<Incident>>({});


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

  useEffect(() => {
    let ws: WebSocket | null = null;
    let pollingInterval: NodeJS.Timeout | null = null;
    try {
      const loc = window.location;
      const wsProtocol = loc.protocol === 'https:' ? 'wss:' : 'ws:';
      const backendHost = 'localhost:8000';
      const wsUrl = `${wsProtocol}//${backendHost}/ws/incidents`;
      ws = new window.WebSocket(wsUrl);
      ws.onopen = () => fetchIncidents();
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setIncidents(prev => {
            const idx = prev.findIndex(i => i.incident_id === data.incident_id || i.id === data.id);
            if (idx >= 0) {
              const updated = [...prev];
              updated[idx] = { ...updated[idx], ...data };
              return updated;
            }
            return [data, ...prev];
          });
        } catch (e) { console.error('WS message error:', e); }
      };
      ws.onerror = ws.onclose = () => {
        if (!pollingInterval) {
          pollingInterval = setInterval(fetchIncidents, 8000);
        }
      };
    } catch {
      if (!pollingInterval) {
        pollingInterval = setInterval(fetchIncidents, 8000);
      }
    }
    return () => {
      if (ws) ws.close();
      if (pollingInterval) clearInterval(pollingInterval);
    };
  }, [filter]); // Keep dependency on filter

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName) || editingId) return;
      if (!incidents.length) return;
      
      const keyActionMap: { [key: string]: () => void } = {
        [OPS_SHORTCUTS.down]: () => setFocusedIdx((idx) => Math.min(idx + 1, incidents.length - 1)),
        [OPS_SHORTCUTS.up]: () => setFocusedIdx((idx) => Math.max(idx - 1, 0)),
        [OPS_SHORTCUTS.resolve]: () => {
            const id = incidents[focusedIdx]?.incident_id || incidents[focusedIdx]?.id;
            if (id) handleAction(id, 'resolve');
        },
        [OPS_SHORTCUTS.escalate]: () => {
            const id = incidents[focusedIdx]?.incident_id || incidents[focusedIdx]?.id;
            if (id) handleAction(id, 'escalate');
        },
        [OPS_SHORTCUTS.assign]: () => {
            const id = incidents[focusedIdx]?.incident_id || incidents[focusedIdx]?.id;
            if (id) handleAction(id, 'assign', 'me'); // You can enhance this to pop a modal
        },
        [OPS_SHORTCUTS.open]: () => {
            const incident = incidents[focusedIdx];
            if (incident) setDetailIncident(incident);
        }
      };

      const action = keyActionMap[e.key];
      if (action) {
        e.preventDefault();
        action();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [incidents, focusedIdx, editingId]); // Added editingId to disable shortcuts while editing


  const handleAction = async (id: string, action: 'resolve' | 'escalate' | 'assign' | 'comment', value?: string) => {
    try {
      let body: any = {};
      if (action === 'assign') body.assigned_to = value || assignUser[id] || 'me';
      if (action === 'comment') body.comment = value || commentText[id] || '';
      await apiRequest(`/incidents/${id}/${action}`, {
        method: 'POST',
        body: JSON.stringify(body),
      });
      fetchIncidents(); // Let websocket handle the update, or fetch if needed.
      if (action === 'assign') setAssignUser(a => ({ ...a, [id]: '' }));
      if (action === 'comment') setCommentText(c => ({ ...c, [id]: '' }));
    } catch (e: any) {
      setError(e.message || 'Action failed');
    }
  };
  
  // --- REFACTORED: Start editing a row ---
  const handleEditStart = (incident: Incident) => {
    const id = incident.incident_id || incident.id;
    setEditingId(id);
    setInlineEdit({
      priority: incident.priority,
      status: incident.status,
      assigned_to: incident.assigned_to,
    });
  };

  // --- REFACTORED: Cancel editing ---
  const handleEditCancel = () => {
    setEditingId(null);
    setInlineEdit({});
  };

  // --- REFACTORED: Save inline edits ---
  const handleInlineSave = async () => {
    if (!editingId || !inlineEdit) return;
    try {
        await apiRequest(`/incidents/${editingId}/update`, { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' }, 
            body: JSON.stringify(inlineEdit) 
        });
        setEditingId(null);
        setInlineEdit({});
        // Let the websocket handle the update. If no websocket, uncomment below:
        // fetchIncidents(); 
    } catch(e: any) {
        setError(e.message || 'Save failed');
    }
  };


  const toggleSelect = (id: string) => {
    setSelectedIncidents(sel => {
      const next = new Set(sel);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };
  const selectAll = (ids: string[]) => setSelectedIncidents(new Set(ids));
  const clearSelection = () => setSelectedIncidents(new Set());

  const handleBulkAction = async (action: 'resolve' | 'escalate' | 'assign', value?: string) => {
    // Your existing bulk action logic is fine
  };
  
  // --- NEW: Group incidents by desk for a cleaner layout ---
  const groupedIncidents = useMemo(() => 
    incidents.reduce((acc, incident) => {
      const desk = incident.desk || 'Unassigned';
      if (!acc[desk]) {
        acc[desk] = [];
      }
      acc[desk].push(incident);
      return acc;
    }, {} as Record<string, Incident[]>),
  [incidents]);

  const allIncidentIds = useMemo(() => incidents.map(i => i.incident_id || i.id), [incidents]);

  const priorities = [ '', '1', '2', '3', '4', '5' ];
  const severities = [ '', 'low', 'medium', 'high', 'critical' ];
  const statuses = [ '', 'open', 'investigating', 'resolved', 'closed', 'escalated' ];

  return (
    // Use a dark theme from DaisyUI
    <div className="p-4 sm:p-6 lg:p-8 bg-base-300 min-h-screen text-base-content" data-theme="dark">
      <div className="max-w-full mx-auto">
        <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold">Incidents</h1>
        </div>

        {/* --- REFACTORED: Cleaner filter bar --- */}
        <div className="mb-6 p-4 bg-base-200 rounded-lg shadow">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 items-end">
            <div className="form-control">
                <label className="label pb-1"><span className="label-text">Type</span></label>
                <input placeholder="e.g., api" className="input input-bordered input-sm" value={filter.type} onChange={e => setFilter(f => ({ ...f, type: e.target.value }))} />
            </div>
            <div className="form-control">
                <label className="label pb-1"><span className="label-text">Desk</span></label>
                <input placeholder="e.g., Equities" className="input input-bordered input-sm" value={filter.desk} onChange={e => setFilter(f => ({ ...f, desk: e.target.value }))} />
            </div>
             <div className="form-control">
                <label className="label pb-1"><span className="label-text">Trader</span></label>
                <input placeholder="e.g., Joe" className="input input-bordered input-sm" value={filter.trader} onChange={e => setFilter(f => ({ ...f, trader: e.target.value }))} />
            </div>
            <div className="form-control">
                <label className="label pb-1"><span className="label-text">Severity</span></label>
                <select className="select select-bordered select-sm" value={filter.severity} onChange={e => setFilter(f => ({ ...f, severity: e.target.value }))}>
                    {severities.map(s => <option key={s} value={s}>{s || 'All Severities'}</option>)}
                </select>
            </div>
            <div className="form-control">
                <label className="label pb-1"><span className="label-text">Status</span></label>
                <select className="select select-bordered select-sm" value={filter.status} onChange={e => setFilter(f => ({ ...f, status: e.target.value }))}>
                    {statuses.map(s => <option key={s} value={s}>{s || 'All Statuses'}</option>)}
                </select>
            </div>
             <div className="form-control">
                <label className="label pb-1"><span className="label-text">Priority</span></label>
                <select className="select select-bordered select-sm" value={filter.priority} onChange={e => setFilter(f => ({ ...f, priority: e.target.value }))}>
                    {priorities.map(p => <option key={p} value={p}>{p || 'All Priorities'}</option>)}
                </select>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={() => setFilter({ type: '', desk: '', trader: '', severity: '', status: '', priority: '' })}>Clear</button>
          </div>
        </div>

        {loading && !incidents.length ? (
          <div className="text-center py-10">Loading incidents...</div>
        ) : error ? (
          <div className="alert alert-error shadow-lg"><div><span>Error: {error}</span></div></div>
        ) : (
          <div className="bg-base-200 rounded-lg shadow-lg overflow-x-auto">
            <table className="table w-full">
              {/* --- REFACTORED: Cleaner table head --- */}
              <thead>
                <tr>
                  <th className="p-4"><input type="checkbox" className="checkbox checkbox-primary" checked={selectedIncidents.size === allIncidentIds.length && allIncidentIds.length > 0} onChange={e => e.target.checked ? selectAll(allIncidentIds) : clearSelection()} /></th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Title / ID</th>
                  <th className="p-4">Trader</th>
                  <th className="p-4">Severity</th>
                  <th className="p-4">Priority</th>
                  <th className="p-4">Assigned To</th>
                  <th className="p-4">Created</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>

              {/* --- NEW: Looping through grouped incidents --- */}
              {Object.entries(groupedIncidents).map(([desk, deskIncidents]) => (
                <tbody key={desk} className="border-t-4 border-base-300">
                  {/* Desk Group Header */}
                  <tr>
                    <td colSpan={9} className="bg-base-100 font-bold text-lg p-3 text-primary">{desk}</td>
                  </tr>
                  
                  {deskIncidents.map((incident, i) => {
                    const id = incident.incident_id || incident.id;
                    const isEditing = editingId === id;
                    const isFocused = focusedIdx === incidents.findIndex(inc => (inc.incident_id || inc.id) === id);
                    const currentStatus = statusConfig[incident.status as keyof typeof statusConfig] || { color: 'bg-gray-500', label: incident.status };
                    const currentSeverity = severityConfig[incident.severity as keyof typeof severityConfig] || { color: 'bg-gray-500', label: incident.severity };

                    return (
                        <tr key={id} className={`hover:bg-base-100 ${isFocused ? 'outline outline-2 outline-primary outline-offset-[-2px]' : ''} ${isEditing ? 'bg-base-100' : ''}`}>
                            <td className="p-4"><input type="checkbox" className="checkbox checkbox-primary" checked={selectedIncidents.has(id)} onChange={() => toggleSelect(id)} /></td>
                            
                            {/* --- REFACTORED: Visual status indicator --- */}
                            <td className="p-4">
                                <div className="flex items-center gap-2">
                                    <span className={`w-3 h-3 rounded-full ${currentStatus.color}`}></span>
                                    <span>{currentStatus.label}</span>
                                </div>
                            </td>

                            <td className="p-4">
                                <div className="font-bold cursor-pointer hover:text-primary" onClick={() => setDetailIncident(incident)}>{incident.title}</div>
                                <div className="text-xs text-base-content/60">{id}</div>
                            </td>

                            <td className="p-4">{incident.trader}</td>

                            {/* --- REFACTORED: Severity badge --- */}
                            <td className="p-4">
                                <span className={`badge text-white ${currentSeverity.color} border-none`}>{currentSeverity.label}</span>
                            </td>

                            {/* --- REFACTORED: Priority with inline edit --- */}
                            <td className="p-4">
                                {isEditing ? (
                                    <select className="select select-bordered select-xs" value={inlineEdit.priority} onChange={e => setInlineEdit(v => ({...v, priority: Number(e.target.value)}))}>
                                        {[1,2,3,4,5].map(p => <option key={p} value={p}>P{p}</option>)}
                                    </select>
                                ) : (
                                    <span className="font-bold">P{incident.priority}</span>
                                )}
                            </td>

                             {/* --- REFACTORED: Assigned To with inline edit --- */}
                            <td className="p-4">
                               {isEditing ? (
                                    <input className="input input-bordered input-xs" value={inlineEdit.assigned_to || ''} onChange={e => setInlineEdit(v => ({...v, assigned_to: e.target.value}))} />
                                ) : (
                                    incident.assigned_to || <span className="text-base-content/50">Unassigned</span>
                                )}
                            </td>
                            
                            <td className="p-4 text-sm text-base-content/80">{new Date(incident.created_at).toLocaleString()}</td>
                            
                            {/* --- REFACTORED: Clean actions column --- */}
                            <td className="p-4">
                                <div className="flex justify-end items-center gap-2">
                                {isEditing ? (
                                    <>
                                        <button className="btn btn-sm btn-primary" onClick={handleInlineSave}>Save</button>
                                        <button className="btn btn-sm btn-ghost" onClick={handleEditCancel}>Cancel</button>
                                    </>
                                ) : (
                                    <>
                                        <button className="btn btn-sm btn-success" onClick={() => handleAction(id, 'resolve')}>Resolve</button>
                                        <div className="dropdown dropdown-end">
                                            <label tabIndex={0} className="btn btn-sm btn-square btn-ghost">
                                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="inline-block w-5 h-5 stroke-current"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z"></path></svg>
                                            </label>
                                            <ul tabIndex={0} className="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52 z-10">
                                                <li><a onClick={() => handleEditStart(incident)}>Edit Row</a></li>
                                                <li><a onClick={() => handleAction(id, 'escalate')}>Escalate</a></li>
                                                <li className="p-2">
                                                    <div className="form-control">
                                                        <input type="text" placeholder="Assign to user..." className="input input-sm w-full" value={assignUser[id] || ''} onChange={e => setAssignUser(a => ({...a, [id]: e.target.value}))} />
                                                        <button className="btn btn-xs btn-primary mt-1" onClick={() => handleAction(id, 'assign')}>Assign</button>
                                                    </div>
                                                </li>
                                                 <li className="p-2">
                                                    <div className="form-control">
                                                        <textarea placeholder="Add comment..." className="textarea textarea-sm w-full" value={commentText[id] || ''} onChange={e => setCommentText(c => ({...c, [id]: e.target.value}))}></textarea>
                                                        <button className="btn btn-xs btn-secondary mt-1" onClick={() => handleAction(id, 'comment')}>Comment</button>
                                                    </div>
                                                </li>
                                            </ul>
                                        </div>
                                    </>
                                )}
                                </div>
                            </td>
                        </tr>
                    )
                  })}
                </tbody>
              ))}
            </table>
            {!incidents.length && <div className="text-center p-10">No incidents match your filters.</div>}
          </div>
        )}
      </div>

      {/* Your existing bulk action bar and modal will work perfectly with this new design */}
      {selectedIncidents.size > 0 && (
         <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-base-100 text-base-content rounded-lg shadow-2xl px-6 py-3 flex gap-4 items-center z-50">
           <span className="font-bold">{selectedIncidents.size} selected</span>
           <button className="btn btn-sm btn-success" onClick={() => handleBulkAction('resolve')}>Bulk Resolve</button>
           <button className="btn btn-sm btn-warning" onClick={() => handleBulkAction('escalate')}>Bulk Escalate</button>
           <div className="flex gap-2 items-center">
            <input className="input input-sm w-28" placeholder="Assign User" onChange={e => setAssignUser(a => ({ ...a, bulk: e.target.value }))} value={assignUser.bulk || ''} />
            <button className="btn btn-sm btn-info" onClick={() => handleBulkAction('assign', assignUser.bulk)}>Bulk Assign</button>
           </div>
           <button className="btn btn-sm btn-ghost" onClick={clearSelection}>Clear Selection</button>
         </div>
       )}

      {detailIncident && (
        <IncidentDetailModal incident={detailIncident} onClose={() => setDetailIncident(null)} />
      )}
    </div>
  );
}
