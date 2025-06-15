'use client'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useWebSocket } from './useWebSocket'
import apiClient, { validateResponse } from '@/lib/api-client'
import { ComplianceLog, ComplianceStats, ComplianceLogSchema, ComplianceStatsSchema } from '@/types/api'
import { z } from 'zod'

interface ComplianceResponse {
  logs: ComplianceLog[]
  stats: ComplianceStats
}

export function useCompliance() {
  const queryClient = useQueryClient()
  
  // Real-time updates via WebSocket
  const { data: wsData } = useWebSocket('/ws/compliance')
  
  // Fetch compliance logs
  const { data: logs, isLoading, isError, error } = useQuery<ComplianceLog[]>({
    queryKey: ['complianceLogs'],
    queryFn: async () => {
      const response = await apiClient.get('/compliance/logs')
      return validateResponse<ComplianceLog[]>(response, z.array(ComplianceLogSchema))
    }
  })

  // Fetch compliance stats
  const { data: stats } = useQuery<any>({
    queryKey: ['complianceStats'],
    queryFn: async () => {
      const response = await apiClient.get('/compliance/logs/stats')
      return response.data
    }
  })

  // Add new compliance log
  const addLog = useMutation({
    mutationFn: async (log: Omit<ComplianceLog, 'id' | 'timestamp'>) => {
      const response = await apiClient.post('/compliance/logs', log)
      return validateResponse<ComplianceLog>(response, ComplianceLogSchema)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['complianceLogs'] })
    }
  })

  // Resolve compliance log
  const resolveLog = useMutation({
    mutationFn: async (logId: number) => {
      const response = await apiClient.put(`/compliance/logs/${logId}/resolve`)
      return validateResponse<ComplianceLog>(response, ComplianceLogSchema)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['complianceLogs'] })
    }
  })

  return {
    logs: logs || [],
    stats,
    isLoading,
    isError,
    error,
    addLog,
    resolveLog
  }
}

