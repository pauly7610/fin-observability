import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';

export function useMockAuditTrail() {
  return useQuery({
    queryKey: ['mock_audit_trail'],
    queryFn: async () => {
      const res = await apiClient.get('/api/mock_audit_trail');
      return res.data;
    },
  });
} 