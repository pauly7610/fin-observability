import React from 'react';
import { theme } from '@/styles/theme';

interface AuditLogEntry {
  id: string;
  timestamp: Date;
  action: string;
  details: string;
  user: string;
  category: 'system' | 'agent' | 'user';
}

interface AuditLogPanelProps {
  entries?: AuditLogEntry[];
  onEntryClick?: (entry: AuditLogEntry) => void;
}

export const AuditLogPanel: React.FC<AuditLogPanelProps> = ({
  entries = [],
  onEntryClick,
}) => {
  const formatTimestamp = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(date);
  };

  const getCategoryColor = (category: AuditLogEntry['category']) => {
    switch (category) {
      case 'system':
        return theme.colors.accent.info;
      case 'agent':
        return theme.colors.accent.warning;
      case 'user':
        return theme.colors.accent.success;
      default:
        return theme.colors.text.secondary;
    }
  };

  return (
    <div className="w-80 bg-background-secondary p-4 border-l border-gray-800">
      <h2 className="text-lg font-semibold mb-4">Audit Log</h2>
      <div className="space-y-2">
        {entries.map((entry) => (
          <div
            key={entry.id}
            className="p-3 rounded-md bg-background-primary cursor-pointer hover:bg-opacity-80 transition-colors"
            onClick={() => onEntryClick?.(entry)}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium">{entry.action}</span>
              <span
                className="text-xs px-2 py-1 rounded-full"
                style={{ backgroundColor: getCategoryColor(entry.category) }}
              >
                {entry.category}
              </span>
            </div>
            <p className="text-sm text-text-secondary mb-1">{entry.details}</p>
            <div className="flex items-center justify-between text-xs text-text-secondary">
              <span>{entry.user}</span>
              <span>{formatTimestamp(entry.timestamp)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Styles
const styles = {
  container: {
    width: '20rem',
    backgroundColor: theme.colors.background.secondary,
    padding: theme.spacing[4],
    borderLeft: `1px solid ${theme.colors.background.primary}`,
  },
  title: {
    fontSize: theme.typography.fontSize.lg,
    fontWeight: 600,
    marginBottom: theme.spacing[4],
  },
  entryList: {
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing[2],
  },
  entry: {
    padding: theme.spacing[3],
    borderRadius: theme.borderRadius.md,
    backgroundColor: theme.colors.background.primary,
    cursor: 'pointer',
    transition: 'background-color 0.2s',
    '&:hover': {
      backgroundColor: 'rgba(35, 37, 38, 0.8)',
    },
  },
  entryHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: theme.spacing[1],
  },
  entryAction: {
    fontSize: theme.typography.fontSize.sm,
    fontWeight: 500,
  },
  entryCategory: {
    fontSize: theme.typography.fontSize.xs,
    padding: `${theme.spacing[1]} ${theme.spacing[2]}`,
    borderRadius: theme.borderRadius.full,
  },
  entryDetails: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
    marginBottom: theme.spacing[1],
  },
  entryFooter: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    fontSize: theme.typography.fontSize.xs,
    color: theme.colors.text.secondary,
  },
} as const; 