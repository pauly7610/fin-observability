'use client'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api-client'

export function useSystems() {
  return useQuery({
    queryKey: ['systems'],
    queryFn: async ({ signal }) => {
      const res = await apiClient.get('/api/systems', { signal })
      return res.data
    }
  })
}
