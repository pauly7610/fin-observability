import React, { useEffect, useState } from 'react';
import { theme } from '@/styles/theme';
import { apiRequest } from '../../apiRequest';

interface Task {
  id: string;
  title: string;
  status: 'ongoing' | 'pending' | 'completed';
  owner: 'agent' | 'human';
  nextAction: string;
}

interface ApprovalRequest {
  id: number;
  resource_type: string;
  resource_id: string;
  requested_by: number;
  status: string;
  reason: string;
  created_at: string;
}

interface TaskSidebarProps {
  tasks?: Task[];
}

export const TaskSidebar: React.FC<TaskSidebarProps> = ({ tasks = [] }) => {
  const groupedTasks = tasks.reduce(
    (acc, task) => {
      acc[task.status].push(task);
      return acc;
    },
    { ongoing: [], pending: [], completed: [] } as Record<string, Task[]>
  );

  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    apiRequest<ApprovalRequest[]>('/approval/?status=pending')
      .then(setApprovals)
      .catch(() => setApprovals([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="w-80 bg-background-secondary p-4 border-l border-gray-800">
      <h2 className="text-lg font-semibold mb-4">Workflow</h2>

      {/* Approvals Section */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-text-secondary mb-2">Approvals</h3>
        <div className="space-y-2">
          {loading ? (
            <div className="text-xs text-text-secondary">Loading approvals...</div>
          ) : approvals.length === 0 ? (
            <div className="text-xs text-text-secondary">No pending approvals</div>
          ) : (
            approvals.map((a) => (
              <div key={a.id} className="bg-background-primary rounded p-2 shadow flex flex-col">
                <span className="text-xs text-accent-warning font-semibold">{a.resource_type} #{a.resource_id}</span>
                <span className="text-xs text-text-secondary">{a.reason}</span>
                <span className="text-xs text-text-secondary">Requested by: {a.requested_by}</span>
                <span className="text-xs text-text-secondary">Created: {new Date(a.created_at).toLocaleString()}</span>
                <a href={`/approvals`} className="text-xs text-accent-info mt-1 underline">Review</a>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Ongoing Tasks */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-text-secondary mb-2">Ongoing Tasks</h3>
        <div className="space-y-2">
          {groupedTasks.ongoing.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      </div>

      {/* Pending Approval */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-text-secondary mb-2">Pending Approval</h3>
        <div className="space-y-2">
          {groupedTasks.pending.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      </div>

      {/* Completed Tasks */}
      <div>
        <h3 className="text-sm font-medium text-text-secondary mb-2">Completed</h3>
        <div className="space-y-2">
          {groupedTasks.completed.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      </div>
    </div>
  );
};

const TaskCard: React.FC<{ task: Task }> = ({ task }) => {
  const statusColors = {
    ongoing: theme.colors.accent.info,
    pending: theme.colors.accent.warning,
    completed: theme.colors.accent.success,
  };

  const ownerIcons = {
    agent: '🤖',
    human: '👤',
  };

  return (
    <div
      className="p-3 rounded-md bg-background-primary cursor-pointer hover:bg-opacity-80 transition-colors"
      style={{ borderLeft: `3px solid ${statusColors[task.status]}` }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium">{task.title}</span>
        <span>{ownerIcons[task.owner]}</span>
      </div>
      <p className="text-sm text-text-secondary">{task.nextAction}</p>
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
  section: {
    marginBottom: theme.spacing[6],
  },
  sectionTitle: {
    fontSize: theme.typography.fontSize.sm,
    fontWeight: 500,
    color: theme.colors.text.secondary,
    marginBottom: theme.spacing[2],
  },
  taskCard: {
    padding: theme.spacing[3],
    borderRadius: theme.borderRadius.md,
    backgroundColor: theme.colors.background.primary,
    cursor: 'pointer',
    transition: 'background-color 0.2s',
    '&:hover': {
      backgroundColor: 'rgba(35, 37, 38, 0.8)',
    },
  },
} as const; 