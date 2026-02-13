'use client'

import { useState } from 'react'
import { useExport } from '@/hooks/useExport'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Shield, AlertTriangle, CreditCard, Bot, Download, Loader2, FileText } from 'lucide-react'
import type { ExportType } from '@/hooks/useExport'

const EXPORT_OPTIONS: { type: ExportType; label: string; icon: React.ElementType; description: string }[] = [
  { type: 'compliance', label: 'Compliance Logs', icon: Shield, description: 'Export compliance events and audit trail' },
  { type: 'incidents', label: 'Incidents', icon: AlertTriangle, description: 'Export incident records and status' },
  { type: 'transactions', label: 'Transactions', icon: CreditCard, description: 'Export scored transactions with anomaly data' },
  { type: 'agent-actions', label: 'Agent Actions', icon: Bot, description: 'Export AI agent actions and approvals' },
  { type: 'audit-trail', label: 'Audit Trail', icon: FileText, description: 'Export unified agentic audit trail (SEC 17a-4, FINRA 4511)' },
]

export default function ExportPage() {
  const {
    exportData,
    loading,
    error,
    approvalPending,
    clearError,
    clearApprovalPending,
  } = useExport()
  const [auditStartDate, setAuditStartDate] = useState('')
  const [auditEndDate, setAuditEndDate] = useState('')

  const getAuditTrailParams = () => {
    const params: Record<string, string> = {}
    if (auditStartDate) params.start = `${auditStartDate}T00:00:00Z`
    if (auditEndDate) params.end = `${auditEndDate}T23:59:59Z`
    return params
  }

  const handleAuditExport = (format: 'csv' | 'json') => {
    exportData('audit-trail', format, getAuditTrailParams())
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Download className="h-6 w-6 text-primary" />
          Export Data
        </h1>
        <p className="text-sm text-muted-foreground">
          Download compliance logs, incidents, transactions, or agent actions as CSV or JSON.
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>
            {error}
            <Button variant="ghost" size="sm" className="ml-2 h-6" onClick={clearError}>
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {approvalPending && (
        <Alert>
          <AlertDescription>
            Export requires approval (request #{approvalPending.id}). Check with your admin.
            <Button variant="ghost" size="sm" className="ml-2 h-6" onClick={clearApprovalPending}>
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {EXPORT_OPTIONS.map(({ type, label, icon: Icon, description }) => (
          <Card key={type}>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Icon className="h-4 w-4" />
                {label}
              </CardTitle>
              <CardDescription>{description}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              {type === 'audit-trail' && (
                <div className="flex flex-wrap gap-2 items-center">
                  <Input
                    type="date"
                    placeholder="Start"
                    value={auditStartDate}
                    onChange={(e) => setAuditStartDate(e.target.value)}
                    className="w-[140px]"
                  />
                  <Input
                    type="date"
                    placeholder="End"
                    value={auditEndDate}
                    onChange={(e) => setAuditEndDate(e.target.value)}
                    className="w-[140px]"
                  />
                  <span className="text-xs text-muted-foreground">Optional date range</span>
                </div>
              )}
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => type === 'audit-trail' ? handleAuditExport('csv') : exportData(type, 'csv')}
                  disabled={!!loading}
                >
                  {loading === type ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <Download className="h-4 w-4 mr-1" />
                      CSV
                    </>
                  )}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => type === 'audit-trail' ? handleAuditExport('json') : exportData(type, 'json')}
                  disabled={!!loading}
                >
                  {loading === type ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <Download className="h-4 w-4 mr-1" />
                      JSON
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
