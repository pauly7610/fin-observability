import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient, { validateResponse } from '@/lib/api-client'
import { Incident, IncidentSchema } from '@/types/api'
import { z } from 'zod'

interface AlertsResponse {
  incidents: Incident[]
}

export function useAlerts() {
  const queryClient = useQueryClient()
  
  // Fetch incidents with filtering
  const { data, isLoading, isError, error } = useQuery<AlertsResponse>({
    queryKey: ['incidents'],
    queryFn: async () => {
      const response = await apiClient.get('/incidents')
      return validateResponse<AlertsResponse>(response, z.object({
        incidents: z.array(IncidentSchema)
      }))
    }
  })

  // Bulk operations
  const bulkResolve = useMutation({
    mutationFn: async (incidentIds: string[]) => {
      const response = await apiClient.post('/incidents/bulk/resolve', {
        incident_ids: incidentIds
      })
      return validateResponse(response, z.object({
        results: z.array(z.object({
          incident_id: z.string(),
          status: z.string()
        }))
      }))
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] })
    }
  })

  const bulkAssign = useMutation({
    mutationFn: async ({ incidentIds, assignedTo }: { incidentIds: string[], assignedTo: number }) => {
      const response = await apiClient.post('/incidents/bulk/assign', {
        incident_ids: incidentIds,
        assigned_to: assignedTo
      })
      return validateResponse(response, z.object({
        results: z.array(z.object({
          incident_id: z.string(),
          status: z.string(),
          assigned_to: z.number()
        }))
      }))
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] })
    }
  })

  return {
    data: {
      alerts: data?.incidents || [],
    },
    isLoading,
    isError,
    error,
    bulkResolve,
    bulkAssign
  }
}
