import { useQuery } from '@tanstack/react-query'

export function useCompliance() {
  return useQuery({
    queryKey: ['compliance'],
    queryFn: async () => {
      const res = await fetch('/api/compliance')
      return res.json()
    }
  })
}
