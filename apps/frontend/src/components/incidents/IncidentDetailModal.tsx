import React from 'react';
import { IncidentTimeline } from './IncidentTimeline';

interface IncidentDetailModalProps {
  incident: any;
  onClose: () => void;
}

export const IncidentDetailModal: React.FC<IncidentDetailModalProps> = ({ incident, onClose }) => {
  if (!incident) return null;
  // --- Agentic/AI Suggestion logic ---
  let aiSuggestion = '';
  let nextAction = '';
  if (incident.status === 'open' && incident.priority === 1) {
    nextAction = 'Escalate immediately or assign to senior ops.';
  } else if (incident.status === 'open') {
    nextAction = 'Assign to desk ops or begin investigation.';
  } else if (incident.status === 'investigating') {
    nextAction = 'Add comment or escalate if unresolved.';
  } else if (incident.status === 'escalated') {
    nextAction = 'Notify compliance or management.';
  } else if (incident.status === 'resolved') {
    nextAction = 'Close incident if all checks pass.';
  } else {
    nextAction = 'Review and update as needed.';
  }
  aiSuggestion = `Root cause: ${incident.root_cause || 'Unknown'}\nRecommended action: ${incident.recommended_action || 'Review incident details.'}`;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center">
      <div className="bg-background-primary rounded-lg shadow-lg p-6 w-full max-w-lg relative">
        <button onClick={onClose} className="absolute top-2 right-2 btn btn-xs btn-error">✕</button>
        <h2 className="text-xl font-bold mb-2">Incident Detail</h2>
        {/* AI Suggestion Section */}
        <div className="mb-4 p-3 bg-blue-900/80 rounded text-blue-100">
          <div className="font-semibold mb-1">AI Suggestion</div>
          <div className="mb-1 whitespace-pre-line">{aiSuggestion}</div>
          <div className="italic text-accent-info">Next best ops action: {nextAction}</div>
        </div>
        {/* Incident Timeline Section */}
        <IncidentTimeline incident={incident} />
        <table className="w-full text-sm">
          <tbody>
            {Object.entries(incident).map(([key, value]) => (
              <tr key={key} className="border-b border-gray-700">
                <td className="font-semibold pr-2 py-1 align-top">{key}</td>
                <td className="py-1">{typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
