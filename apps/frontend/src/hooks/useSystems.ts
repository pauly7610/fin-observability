'use client'
import { useQuery } from '@tanstack/react-query'

export function useSystems() {
  return useQuery({
    queryKey: ['systems'],
    queryFn: async ({ signal }) => {
      const res = await fetch('/api/systems', { signal })
      if (!res.ok) throw new Error('Network response was not ok')
      return res.json()
    }
  })
}
