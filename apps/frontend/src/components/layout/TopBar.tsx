import React from 'react';
import { SystemStatus } from './SystemStatus';
import { SearchCommand } from './SearchCommand';
import { UserMenu } from './UserMenu';
import { theme } from '@/styles/theme';

export const TopBar: React.FC = () => {
  return (
    <div className="flex items-center justify-between h-14 px-4 bg-background-secondary border-b border-gray-800">
      {/* System Status */}
      <div className="flex items-center space-x-4">
        <SystemStatus />
      </div>

      {/* Search/Command */}
      <div className="flex-1 max-w-2xl mx-4">
        <SearchCommand />
      </div>

      {/* User Menu */}
      <div className="flex items-center space-x-4">
        <UserMenu />
      </div>
    </div>
  );
};

// Styles
const styles = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: '3.5rem',
    padding: `0 ${theme.spacing[4]}`,
    backgroundColor: theme.colors.background.secondary,
    borderBottom: `1px solid ${theme.colors.background.primary}`,
  },
  searchContainer: {
    flex: 1,
    maxWidth: '32rem',
    margin: `0 ${theme.spacing[4]}`,
  },
} as const; 