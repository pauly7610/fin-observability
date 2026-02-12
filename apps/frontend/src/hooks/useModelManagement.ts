import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient, { validateResponse } from '@/lib/api-client'
import {
  LLMConfig,
  LLMConfigSchema,
  RetrainStatus,
  RetrainStatusSchema,
  LeaderboardEntry,
  LeaderboardEntrySchema,
} from '@/types/api'
import { z } from 'zod'

export function useModelConfig() {
  const queryClient = useQueryClient()

  const { data, isLoading, isError, error } = useQuery<LLMConfig>({
    queryKey: ['llmConfig'],
    queryFn: async () => {
      const response = await apiClient.get('/agent/config')
      return validateResponse<LLMConfig>(response, LLMConfigSchema)
    },
  })

  const updateModel = useMutation({
    mutationFn: async ({ provider, model }: { provider?: string; model?: string }) => {
      const params = new URLSearchParams()
      if (provider) params.set('provider', provider)
      if (model) params.set('model', model)
      const response = await apiClient.post(`/agent/config/model?${params.toString()}`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llmConfig'] })
    },
  })

  return {
    config: data || null,
    isLoading,
    isError,
    error,
    updateModel,
  }
}

export function useRetrainStatus() {
  const { data, isLoading, isError } = useQuery<RetrainStatus>({
    queryKey: ['retrainStatus'],
    queryFn: async () => {
      const response = await apiClient.get('/agent/compliance/retrain/status')
      return validateResponse<RetrainStatus>(response, RetrainStatusSchema)
    },
    refetchInterval: 30000,
  })

  return {
    status: data || null,
    isLoading,
    isError,
  }
}

export function useLeaderboard() {
  const { data, isLoading, isError } = useQuery<LeaderboardEntry[]>({
    queryKey: ['leaderboard'],
    queryFn: async () => {
      const response = await apiClient.get('/agent/compliance/eval/leaderboard')
      const wrapper = response.data as { leaderboard?: unknown[] }
      return validateResponse<LeaderboardEntry[]>(
        { data: wrapper.leaderboard ?? [] },
        z.array(LeaderboardEntrySchema)
      )
    },
  })

  return {
    entries: data || [],
    isLoading,
    isError,
  }
}

export function useTriggerRetrain() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/agent/compliance/retrain/scheduled')
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['retrainStatus'] })
      queryClient.invalidateQueries({ queryKey: ['leaderboard'] })
    },
  })
}
