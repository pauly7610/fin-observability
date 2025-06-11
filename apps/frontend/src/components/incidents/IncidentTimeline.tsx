import React from 'react';

interface IncidentTimelineProps {
  incident: any;
}

/**
 * IncidentTimeline renders a chronological feed of all ops actions and comments for an incident.
 * It expects incident.meta.comments (array) and can be extended for audit log integration.
 */
export const IncidentTimeline: React.FC<IncidentTimelineProps> = ({ incident }) => {
  // Comments are stored in incident.meta.comments as an array
  const comments = incident?.meta?.comments || [];

  // Timeline events: comments, status changes, assignments, etc. (for now, just comments)
  // In future, fetch audit log entries and merge with comments.
  const timelineEvents = [
    ...comments.map((c: any) => ({
      type: 'comment',
      user: c.user,
      text: c.comment,
      timestamp: c.timestamp,
    })),
    // Add more event types here (status changes, assignments, etc.)
  ].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  if (!timelineEvents.length) {
    return (
      <div className="p-3 text-gray-400 italic text-sm">No activity yet for this incident.</div>
    );
  }

  return (
    <div className="mt-4 border-t border-gray-700 pt-3">
      <div className="font-semibold mb-2 text-base text-blue-200">Incident Timeline</div>
      <ul className="space-y-2">
        {timelineEvents.map((event, idx) => (
          <li key={idx} className="flex items-start gap-2">
            <div className="w-2 h-2 mt-2 rounded-full bg-blue-400 flex-shrink-0" />
            <div>
              <div className="text-xs text-gray-400">
                {event.type === 'comment' ? 'Comment' : event.type} by <span className="font-mono">{event.user ?? 'unknown'}</span> at {new Date(event.timestamp).toLocaleString()}
              </div>
              <div className="text-sm text-blue-100 whitespace-pre-line">{event.text}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default IncidentTimeline;
