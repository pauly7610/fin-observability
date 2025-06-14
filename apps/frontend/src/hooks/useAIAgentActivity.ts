import { useQuery } from '@tanstack/react-query'

export function useAIAgentActivity() {
  return useQuery({
    queryKey: ['ai-agent-activity'],
    queryFn: async () => {
      const res = await fetch('/api/ai-agent-activity')
      return res.json()
    }
  })
}
