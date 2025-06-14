import { useQuery } from '@tanstack/react-query'

export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: async () => {
      // Replace with your API endpoint
      const res = await fetch('/api/metrics')
      return res.json()
    }
  })
}
