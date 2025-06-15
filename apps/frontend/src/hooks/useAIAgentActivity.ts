import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient, { validateResponse } from '@/lib/api-client'
import { AgentAction, AgentActionSchema } from '@/types/api'
import { z } from 'zod'

export function useAIAgentActivity() {
  const queryClient = useQueryClient()

  // Fetch agent actions
  const { data, isLoading, isError, error } = useQuery<AgentAction[]>({
    queryKey: ['agentActions'],
    queryFn: async () => {
      const response = await apiClient.get('/agent/actions')
      return validateResponse<AgentAction[]>(response, z.array(AgentActionSchema))
    }
  })

  // Trigger triage
  const triageIncident = useMutation({
    mutationFn: async (incident: any) => {
      const response = await apiClient.post('/agent/triage', incident)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agentActions'] })
    }
  })

  // Approve action
  const approveAction = useMutation({
    mutationFn: async ({ actionId, approvedBy }: { actionId: number, approvedBy: number }) => {
      const response = await apiClient.post(`/agent/actions/${actionId}/approve`, { approved_by: approvedBy })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agentActions'] })
    }
  })

  // Reject action
  const rejectAction = useMutation({
    mutationFn: async ({ actionId, approvedBy }: { actionId: number, approvedBy: number }) => {
      const response = await apiClient.post(`/agent/actions/${actionId}/reject`, { approved_by: approvedBy })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agentActions'] })
    }
  })

  return {
    actions: (data as AgentAction[]) || [],
    isLoading,
    isError,
    error,
    triageIncident,
    approveAction,
    rejectAction
  }
}