import React from 'react';
import { TopBar } from './TopBar';
import { Navigation } from './Navigation';
import { TaskSidebar } from './TaskSidebar';
import { CommandBar } from './CommandBar';
import { AuditLogPanel } from './AuditLogPanel';
import { theme } from '@/styles/theme';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  return (
    <div className="flex flex-col h-screen bg-background-primary text-text-primary">
      {/* Top Bar */}
      <TopBar />

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Navigation Sidebar */}
        <Navigation />

        {/* Main Dashboard */}
        <main className="flex-1 overflow-auto p-4">
          {children}
        </main>

        {/* Task/Agent Sidebar */}
        <TaskSidebar />
      </div>

      {/* Command Bar */}
      <CommandBar />

      {/* Audit Log Panel */}
      <AuditLogPanel />
    </div>
  );
};

// Styles
const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    backgroundColor: theme.colors.background.primary,
    color: theme.colors.text.primary,
  },
  mainContent: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
  },
  main: {
    flex: 1,
    overflow: 'auto',
    padding: theme.spacing[4],
  },
} as const; 