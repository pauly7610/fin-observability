import React, { useState, useEffect } from 'react';
import { theme } from '@/styles/theme';

interface SearchResult {
  id: string;
  title: string;
  description: string;
  type: 'incident' | 'alert' | 'metric' | 'log';
}

interface SearchCommandProps {
  onSearch?: (query: string) => void;
  onResultSelect?: (result: SearchResult) => void;
}

import { useRouter } from 'next/router';

export const SearchCommand: React.FC<SearchCommandProps> = ({
  onSearch,
  onResultSelect,
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const router = useRouter();

  const icons: Record<string, string> = {
    incident: '🚨',
    user: '👤',
    compliance: '📋',
    workflow: '🤖',
    export: '📤',
  };

  const groupedResults = results.reduce((acc: Record<string, SearchResult[]>, result) => {
    acc[result.type] = acc[result.type] || [];
    acc[result.type].push(result);
    return acc;
  }, {});

  const flatResults = Object.values(groupedResults).flat();

  const handleSearch = async (value: string) => {
    setQuery(value);
    onSearch?.(value);
    if (!value.trim()) {
      setResults([]);
      return;
    }
    // Parallel fetches to all major resource endpoints
    try {
      const [incidents, users, compliance, agentic, exportsJobs] = await Promise.all([
        fetch(`/incidents/?q=${encodeURIComponent(value)}`).then(r => r.ok ? r.json() : []),
        fetch(`/users?q=${encodeURIComponent(value)}`).then(r => r.ok ? r.json() : []),
        fetch(`/compliance/logs?q=${encodeURIComponent(value)}`).then(r => r.ok ? r.json() : []),
        fetch(`/agentic/workflows?q=${encodeURIComponent(value)}`).then(r => r.ok ? r.json() : []),
        fetch(`/exports?q=${encodeURIComponent(value)}`).then(r => r.ok ? r.json() : []),
      ]);
      const results = [
        ...incidents.map((i: any) => ({
          id: i.id,
          title: i.title,
          description: i.description || '',
          type: 'incident',
          link: `/incidents/${i.id}`
        })),
        ...users.map((u: any) => ({
          id: u.id,
          title: u.username,
          description: u.email,
          type: 'user',
          link: `/users/${u.id}`
        })),
        ...compliance.map((c: any) => ({
          id: c.id,
          title: c.type,
          description: c.description || '',
          type: 'compliance',
          link: `/compliance/${c.id}`
        })),
        ...agentic.map((a: any) => ({
          id: a.id,
          title: a.name,
          description: a.explainability || '',
          type: 'workflow',
          link: `/agentic/${a.id}`
        })),
        ...exportsJobs.map((e: any) => ({
          id: e.id,
          title: e.type,
          description: e.status,
          type: 'export',
          link: `/exports`
        })),
      ];
      setResults(results);
    } catch (err) {
      setResults([]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
    } else if (e.key === 'ArrowDown') {
      setSelectedIndex((prev) => Math.min(prev + 1, flatResults.length - 1));
    } else if (e.key === 'ArrowUp') {
      setSelectedIndex((prev) => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter' && flatResults[selectedIndex]) {
      const link = (flatResults[selectedIndex] as any).link;
      if (link) {
        setIsOpen(false);
        setQuery('');
        setSelectedIndex(0);
        router.push(link);
      }
    }
  };

  useEffect(() => {
    setSelectedIndex(0);
  }, [results]);


  return (
    <div className="relative">
      <div className="flex items-center space-x-2">
        <input
          type="text"
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search incidents, alerts, metrics..."
          className="w-64 bg-background-secondary text-text-primary px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-accent-primary"
        />
        <kbd className="px-2 py-1 text-xs bg-background-secondary text-text-secondary rounded">
          ⌘K
        </kbd>
      </div>

      {isOpen && (
        <div className="absolute top-full left-0 w-96 mt-2 bg-background-primary rounded-lg shadow-lg border border-gray-800 z-50">
          <div className="p-4 max-h-96 overflow-y-auto">
            <div className="text-sm text-text-secondary mb-2">
              Search Results
            </div>
            {flatResults.length > 0 ? (
              <div>
                {Object.entries(groupedResults).map(([type, items]) => (
                  <div key={type}>
                    <div className="uppercase text-xs text-text-secondary font-semibold mt-2 mb-1 flex items-center gap-1">
                      <span>{icons[type] || '🔎'}</span> {type}
                    </div>
                    {items.map((result, idx) => {
                      const globalIdx = flatResults.findIndex(r => r.id === result.id && r.type === result.type);
                      return (
                        <div
                          key={result.id}
                          className={`p-2 rounded-md flex items-center gap-2 cursor-pointer ${selectedIndex === globalIdx ? 'bg-accent-info text-white' : 'hover:bg-background-secondary'}`}
                          onClick={() => {
                            onResultSelect?.(result);
                            setIsOpen(false);
                            setQuery('');
                            setSelectedIndex(0);
                            if ((result as any).link) router.push((result as any).link);
                          }}
                          onMouseEnter={() => setSelectedIndex(globalIdx)}
                        >
                          <span className="text-lg">{icons[result.type] || '🔎'}</span>
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <span className="font-medium">{result.title}</span>
                              <span className="text-xs px-2 py-1 rounded-full bg-background-secondary">
                                {result.type}
                              </span>
                            </div>
                            <p className="text-sm text-text-secondary">
                              {result.description}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-text-secondary">
                No results found
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Styles
const styles = {
  container: {
    position: 'relative',
  },
  searchInput: {
    width: '16rem',
    backgroundColor: theme.colors.background.secondary,
    color: theme.colors.text.primary,
    padding: `${theme.spacing[2]} ${theme.spacing[4]}`,
    borderRadius: theme.borderRadius.md,
    '&:focus': {
      outline: 'none',
      boxShadow: `0 0 0 2px ${theme.colors.accent.info}`,
    },
  },
  keyboardShortcut: {
    padding: `${theme.spacing[1]} ${theme.spacing[2]}`,
    fontSize: theme.typography.fontSize.xs,
    backgroundColor: theme.colors.background.secondary,
    color: theme.colors.text.secondary,
    borderRadius: theme.borderRadius.md,
  },
  resultsContainer: {
    position: 'absolute',
    top: '100%',
    left: 0,
    width: '24rem',
    marginTop: theme.spacing[2],
    backgroundColor: theme.colors.background.primary,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.lg,
    border: `1px solid ${theme.colors.background.primary}`,
  },
  resultsHeader: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
    marginBottom: theme.spacing[2],
  },
  resultItem: {
    padding: theme.spacing[2],
    borderRadius: theme.borderRadius.md,
    cursor: 'pointer',
    '&:hover': {
      backgroundColor: theme.colors.background.secondary,
    },
  },
  resultTitle: {
    fontWeight: 500,
  },
  resultType: {
    fontSize: theme.typography.fontSize.xs,
    padding: `${theme.spacing[1]} ${theme.spacing[2]}`,
    borderRadius: theme.borderRadius.full,
    backgroundColor: theme.colors.background.secondary,
  },
  resultDescription: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
  },
  noResults: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
  },
} as const; 