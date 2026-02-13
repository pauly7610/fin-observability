import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';

export function useMockScenarios() {
  return useQuery({
    queryKey: ['mock_scenarios'],
    queryFn: async () => {
      const res = await apiClient.get('/api/mock_scenarios');
      return res.data;
    },
  });
} 