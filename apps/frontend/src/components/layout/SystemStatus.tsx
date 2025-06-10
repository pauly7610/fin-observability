import React from 'react';
import { theme } from '@/styles/theme';

interface SystemMetric {
  name: string;
  value: number;
  unit: string;
  status: 'healthy' | 'warning' | 'critical';
}

interface SystemStatusProps {
  metrics?: SystemMetric[];
  lastUpdated?: Date;
}

export const SystemStatus: React.FC<SystemStatusProps> = ({
  metrics = [],
  lastUpdated = new Date(),
}) => {
  const getStatusColor = (status: SystemMetric['status']) => {
    switch (status) {
      case 'healthy':
        return theme.colors.accent.success;
      case 'warning':
        return theme.colors.accent.warning;
      case 'critical':
        return theme.colors.accent.error;
      default:
        return theme.colors.text.secondary;
    }
  };

  const formatLastUpdated = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(date);
  };

  return (
    <div className="flex items-center space-x-4">
      {metrics.map((metric) => (
        <div
          key={metric.name}
          className="flex items-center space-x-2"
        >
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: getStatusColor(metric.status) }}
          />
          <span className="text-sm">
            {metric.name}: {metric.value}{metric.unit}
          </span>
        </div>
      ))}
      <div className="text-xs text-text-secondary">
        Last updated: {formatLastUpdated(lastUpdated)}
      </div>
    </div>
  );
};

// Styles
const styles = {
  container: {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing[4],
  },
  metric: {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing[2],
  },
  statusIndicator: {
    width: theme.spacing[2],
    height: theme.spacing[2],
    borderRadius: theme.borderRadius.full,
  },
  metricText: {
    fontSize: theme.typography.fontSize.sm,
  },
  lastUpdated: {
    fontSize: theme.typography.fontSize.xs,
    color: theme.colors.text.secondary,
  },
} as const; 