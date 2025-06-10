import React, { useState } from 'react';
import { theme } from '@/styles/theme';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  avatar?: string;
}

interface UserMenuProps {
  user?: User;
  onLogout?: () => void;
  onSettingsClick?: () => void;
}

export const UserMenu: React.FC<UserMenuProps> = ({
  user,
  onLogout,
  onSettingsClick,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  const handleClickOutside = (e: React.MouseEvent) => {
    if (isOpen) {
      setIsOpen(false);
    }
  };

  if (!user) {
    return (
      <button
        className="px-4 py-2 bg-accent-primary text-white rounded-md hover:bg-opacity-90 transition-colors"
        onClick={onLogout}
      >
        Sign In
      </button>
    );
  }

  return (
    <div className="relative">
      <button
        className="flex items-center space-x-2 focus:outline-none"
        onClick={handleToggle}
      >
        {user.avatar ? (
          <img
            src={user.avatar}
            alt={user.name}
            className="w-8 h-8 rounded-full"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center text-white">
            {user.name.charAt(0).toUpperCase()}
          </div>
        )}
        <span className="text-sm font-medium">{user.name}</span>
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={handleClickOutside}
          />
          <div className="absolute right-0 mt-2 w-48 bg-background-primary rounded-lg shadow-lg border border-gray-800 z-20">
            <div className="p-4 border-b border-gray-800">
              <div className="font-medium">{user.name}</div>
              <div className="text-sm text-text-secondary">{user.email}</div>
              <div className="text-xs text-text-secondary mt-1">{user.role}</div>
            </div>
            <div className="py-1">
              <button
                className="w-full px-4 py-2 text-left text-sm hover:bg-background-secondary transition-colors"
                onClick={() => {
                  onSettingsClick?.();
                  setIsOpen(false);
                }}
              >
                Settings
              </button>
              <button
                className="w-full px-4 py-2 text-left text-sm text-accent-error hover:bg-background-secondary transition-colors"
                onClick={() => {
                  onLogout?.();
                  setIsOpen(false);
                }}
              >
                Sign Out
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// Styles
const styles = {
  container: {
    position: 'relative',
  },
  userButton: {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing[2],
    cursor: 'pointer',
    '&:focus': {
      outline: 'none',
    },
  },
  avatar: {
    width: theme.spacing[8],
    height: theme.spacing[8],
    borderRadius: theme.borderRadius.full,
  },
  avatarFallback: {
    width: theme.spacing[8],
    height: theme.spacing[8],
    borderRadius: theme.borderRadius.full,
    backgroundColor: theme.colors.accent.primary,
    color: theme.colors.text.primary,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  userName: {
    fontSize: theme.typography.fontSize.sm,
    fontWeight: 500,
  },
  menu: {
    position: 'absolute',
    right: 0,
    top: '100%',
    marginTop: theme.spacing[2],
    width: '12rem',
    backgroundColor: theme.colors.background.primary,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.lg,
    border: `1px solid ${theme.colors.background.primary}`,
    zIndex: 20,
  },
  userInfo: {
    padding: theme.spacing[4],
    borderBottom: `1px solid ${theme.colors.background.primary}`,
  },
  userInfoName: {
    fontWeight: 500,
  },
  userInfoEmail: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
  },
  userInfoRole: {
    fontSize: theme.typography.fontSize.xs,
    color: theme.colors.text.secondary,
    marginTop: theme.spacing[1],
  },
  menuItems: {
    padding: `${theme.spacing[1]} 0`,
  },
  menuItem: {
    width: '100%',
    padding: `${theme.spacing[2]} ${theme.spacing[4]}`,
    textAlign: 'left',
    fontSize: theme.typography.fontSize.sm,
    cursor: 'pointer',
    '&:hover': {
      backgroundColor: theme.colors.background.secondary,
    },
  },
  menuItemDanger: {
    color: theme.colors.accent.error,
  },
} as const; 