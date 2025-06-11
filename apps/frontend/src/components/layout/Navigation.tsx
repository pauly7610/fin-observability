import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { theme } from '@/styles/theme';

const navigationItems = [
  { name: 'Incidents', path: '/incidents', icon: '🚨' },
  { name: 'Dashboard', path: '/incidents', icon: '📊' }, // Dashboard points to /incidents
  { name: 'Compliance', path: '/compliance', icon: '📋' },
  { name: 'Agentic Workflows', path: '/agentic', icon: '🤖' },
  { name: 'Users', path: '/users', icon: '👤' },
  { name: 'Exports', path: '/exports', icon: '📤' },
  // { name: 'Alerts', path: '/alerts', icon: '🔔' },
  // { name: 'Reports', path: '/reports', icon: '📈' },
];

export const Navigation: React.FC = () => {
  const router = useRouter();

  return (
    <nav className="w-48 bg-background-secondary p-4">
      <div className="space-y-2">
        {navigationItems.map((item) => {
          const isActive = router.pathname === item.path;
          return (
            <Link
              key={item.path}
              href={item.path}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                isActive
                  ? 'bg-accent-info text-white'
                  : 'text-text-secondary hover:bg-background-primary'
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.name}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};

// Styles
const styles = {
  container: {
    width: '12rem',
    backgroundColor: theme.colors.background.secondary,
    padding: theme.spacing[4],
  },
  item: {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing[2],
    padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
    borderRadius: theme.borderRadius.md,
    transition: 'background-color 0.2s',
  },
  activeItem: {
    backgroundColor: theme.colors.accent.info,
    color: theme.colors.text.primary,
  },
  inactiveItem: {
    color: theme.colors.text.secondary,
    '&:hover': {
      backgroundColor: theme.colors.background.primary,
    },
  },
} as const; 