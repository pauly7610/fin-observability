import { useQuery } from '@tanstack/react-query';

export function useMockAuditTrail() {
  return useQuery({
    queryKey: ['mock_audit_trail'],
    queryFn: async () => {
      const res = await fetch('/api/mock_audit_trail');
      if (!res.ok) throw new Error('Failed to fetch mock audit trail');
      return res.json();
    },
  });
} 