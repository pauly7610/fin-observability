'use client'

import { useState } from 'react'
import apiClient from '@/lib/api-client'

export type ExportType = 'compliance' | 'incidents' | 'transactions' | 'agent-actions' | 'audit-trail'
export type ExportFormat = 'csv' | 'json'

const ENDPOINTS: Record<ExportType, string> = {
  compliance: '/compliance/export',
  incidents: '/incidents/export',
  transactions: '/transactions/export',
  'agent-actions': '/audit/actions/export',
  'audit-trail': '/api/audit_trail/export',
}

const DEFAULT_FILENAMES: Record<ExportType, Record<ExportFormat, string>> = {
  compliance: { csv: 'compliance_logs.csv', json: 'compliance_logs.json' },
  incidents: { csv: 'incidents.csv', json: 'incidents.json' },
  transactions: { csv: 'transactions.csv', json: 'transactions.json' },
  'agent-actions': { csv: 'agent_actions.csv', json: 'agent_actions.json' },
  'audit-trail': { csv: 'audit_trail.csv', json: 'audit_trail.json' },
}

interface ExportParams {
  format?: string
  event_type?: string
  severity?: string
  status?: string
  [key: string]: string | boolean | undefined
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export function useExport() {
  const [loading, setLoading] = useState<ExportType | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [approvalPending, setApprovalPending] = useState<{ id: number; status: string } | null>(null)

  async function exportData(
    type: ExportType,
    format: ExportFormat = 'csv',
    params: ExportParams = {}
  ): Promise<boolean> {
    setLoading(type)
    setError(null)
    setApprovalPending(null)

    try {
      const url = ENDPOINTS[type]
      const searchParams = new URLSearchParams({ format, ...params } as Record<string, string>)
      const fullUrl = `${url}?${searchParams.toString()}`

      const response = await apiClient.get(fullUrl, { responseType: 'blob' })
      const blob = response.data as Blob

      // Check if response is JSON (approval required or error)
      const contentType = response.headers?.['content-type'] || ''
      if (contentType.includes('application/json')) {
        const text = await blob.text()
        const data = JSON.parse(text)
        if (data.approval_request_id) {
          setApprovalPending({ id: data.approval_request_id, status: data.status || 'pending' })
          return false
        }
        if (data.detail) {
          setError(data.detail)
          return false
        }
      }

      // Extract filename from Content-Disposition or use default
      const disposition = response.headers?.['content-disposition']
      let filename = DEFAULT_FILENAMES[type][format]
      if (disposition?.includes('filename=')) {
        const match = disposition.match(/filename="?([^";]+)"?/)
        if (match) filename = match[1]
      }

      triggerDownload(blob, filename)
      return true
    } catch (err: unknown) {
      let msg = 'Export failed'
      if (err && typeof err === 'object' && 'response' in err) {
        const res = (err as { response?: { data?: Blob | { detail?: string }; status?: number } }).response
        if (res?.data) {
          if (res.data instanceof Blob) {
            msg = 'Export failed (check approval or permissions)'
          } else if (typeof res.data === 'object' && 'detail' in res.data) {
            msg = (res.data as { detail?: string }).detail || msg
          }
        }
      } else if (err && typeof err === 'object' && 'message' in err) {
        msg = (err as { message: string }).message
      }
      setError(msg)
      return false
    } finally {
      setLoading(null)
    }
  }

  return {
    exportData,
    loading,
    error,
    approvalPending,
    clearError: () => setError(null),
    clearApprovalPending: () => setApprovalPending(null),
  }
}
