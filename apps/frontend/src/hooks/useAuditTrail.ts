import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';

export interface AuditTrailEntry {
  timestamp: string;
  action: string;
  user: string;
  details: string;
  compliance_tag: string;
  entity_type?: string;
  entity_id?: string;
  regulation_tags?: string[];
}

export interface UseAuditTrailParams {
  entity_type?: string;
  event_type?: string;
  regulation_tag?: string;
  start?: string;
  end?: string;
  limit?: number;
}

export function useAuditTrail(params?: UseAuditTrailParams) {
  return useQuery({
    queryKey: ['audit_trail', params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.entity_type) searchParams.set('entity_type', params.entity_type);
      if (params?.event_type) searchParams.set('event_type', params.event_type);
      if (params?.regulation_tag) searchParams.set('regulation_tag', params.regulation_tag);
      if (params?.start) searchParams.set('start', params.start);
      if (params?.end) searchParams.set('end', params.end);
      if (params?.limit) searchParams.set('limit', String(params.limit));
      const url = `/api/audit_trail${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
      const res = await apiClient.get(url);
      return res.data as AuditTrailEntry[];
    },
  });
}
