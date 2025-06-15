import { useQuery } from '@tanstack/react-query';

export function useMockScenarios() {
  return useQuery({
    queryKey: ['mock_scenarios'],
    queryFn: async () => {
      const res = await fetch('/api/mock_scenarios');
      if (!res.ok) throw new Error('Failed to fetch mock scenarios');
      return res.json();
    },
  });
} 