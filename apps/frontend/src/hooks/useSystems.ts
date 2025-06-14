import { useQuery } from '@tanstack/react-query'

export function useSystems() {
  return useQuery({
    queryKey: ['systems'],
    queryFn: async () => {
      const res = await fetch('/api/systems')
      return res.json()
    }
  })
}
