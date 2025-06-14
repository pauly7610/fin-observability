import { useQuery } from '@tanstack/react-query'

export function useAlerts() {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: async () => {
      const res = await fetch('/api/alerts')
      return res.json()
    }
  })
}
