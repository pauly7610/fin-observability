'use client'
import { useQuery } from '@tanstack/react-query'

export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: async ({ signal }) => {
      const res = await fetch('/api/metrics', { signal })
      if (!res.ok) throw new Error('Network response was not ok')
      return res.json()
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
