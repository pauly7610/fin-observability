'use client'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api-client'

export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: async ({ signal }) => {
      const res = await apiClient.get('/api/metrics', { signal })
      return res.data
    },
    initialData: {
      uptime: 0,
      activeAlerts: 0,
      noiseReduction: 0,
      mttr: 0,
      mttrImprovement: 0,
      complianceScore: 0,
      complianceStatus: 'Unknown'
    }
  })
}
