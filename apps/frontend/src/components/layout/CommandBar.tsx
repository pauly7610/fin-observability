import React, { useState, useEffect } from 'react';
import { theme } from '@/styles/theme';

interface Command {
  id: string;
  title: string;
  description: string;
  category: 'system' | 'agent' | 'user';
  action: () => void;
}

interface CommandBarProps {
  commands?: Command[];
  onCommandSelect?: (command: Command) => void;
}

export const CommandBar: React.FC<CommandBarProps> = ({
  commands = [],
  onCommandSelect,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  const filteredCommands = commands.filter((command) =>
    command.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    command.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setIsOpen(true);
      } else if (e.key === 'Escape') {
        setIsOpen(false);
      } else if (isOpen) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          setSelectedIndex((prev) =>
            Math.min(prev + 1, filteredCommands.length - 1)
          );
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          setSelectedIndex((prev) => Math.max(prev - 1, 0));
        } else if (e.key === 'Enter' && filteredCommands[selectedIndex]) {
          e.preventDefault();
          handleCommandSelect(filteredCommands[selectedIndex]);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredCommands, selectedIndex]);

  const handleCommandSelect = (command: Command) => {
    command.action();
    onCommandSelect?.(command);
    setIsOpen(false);
    setSearchQuery('');
    setSelectedIndex(0);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-start justify-center pt-20">
      <div className="w-full max-w-2xl bg-background-primary rounded-lg shadow-lg">
        <div className="p-4 border-b border-gray-800">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Type a command or search..."
            className="w-full bg-background-secondary text-text-primary px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-accent-primary"
            autoFocus
          />
        </div>
        <div className="max-h-96 overflow-y-auto">
          {filteredCommands.map((command, index) => (
            <div
              key={command.id}
              className={`p-4 cursor-pointer ${
                index === selectedIndex ? 'bg-background-secondary' : ''
              }`}
              onClick={() => handleCommandSelect(command)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">{command.title}</h3>
                  <p className="text-sm text-text-secondary">
                    {command.description}
                  </p>
                </div>
                <span className="text-xs px-2 py-1 rounded-full bg-background-secondary">
                  {command.category}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Styles
const styles = {
  overlay: {
    position: 'fixed',
    inset: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'center',
    paddingTop: '5rem',
  },
  container: {
    width: '100%',
    maxWidth: '42rem',
    backgroundColor: theme.colors.background.primary,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.lg,
  },
  input: {
    width: '100%',
    backgroundColor: theme.colors.background.secondary,
    color: theme.colors.text.primary,
    padding: `${theme.spacing[2]} ${theme.spacing[4]}`,
    borderRadius: theme.borderRadius.md,
    '&:focus': {
      outline: 'none',
      boxShadow: `0 0 0 2px ${theme.colors.accent.primary}`,
    },
  },
  commandList: {
    maxHeight: '24rem',
    overflowY: 'auto',
  },
  commandItem: {
    padding: theme.spacing[4],
    cursor: 'pointer',
    '&:hover': {
      backgroundColor: theme.colors.background.secondary,
    },
  },
  commandTitle: {
    fontWeight: 500,
  },
  commandDescription: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
  },
  commandCategory: {
    fontSize: theme.typography.fontSize.xs,
    padding: `${theme.spacing[1]} ${theme.spacing[2]}`,
    borderRadius: theme.borderRadius.full,
    backgroundColor: theme.colors.background.secondary,
  },
} as const; 