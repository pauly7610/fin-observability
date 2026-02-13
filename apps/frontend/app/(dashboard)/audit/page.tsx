'use client'

import { useState } from 'react'
import { useAuditTrail } from '@/hooks/useAuditTrail'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { FileText, Filter, List, GitBranch } from 'lucide-react'
import { TableSkeleton } from '@/components/CardSkeleton'

const ENTITY_TYPES = [
  { value: 'all', label: 'All entities' },
  { value: 'incident', label: 'Incident' },
  { value: 'agent_action', label: 'Agent Action' },
  { value: 'transaction', label: 'Transaction' },
  { value: 'export', label: 'Export' },
  { value: 'compliance_log', label: 'Compliance Log' },
  { value: 'approval', label: 'Approval' },
]

const EVENT_TYPES = [
  { value: 'all', label: 'All events' },
  { value: 'incident_created', label: 'Incident Created' },
  { value: 'incident_status_change', label: 'Incident Status Change' },
  { value: 'incident_assignment', label: 'Incident Assignment' },
  { value: 'incident_escalation', label: 'Incident Escalation' },
  { value: 'agent_action_proposed', label: 'Agent Action Proposed' },
  { value: 'agent_action_approved', label: 'Agent Action Approved' },
  { value: 'agent_action_rejected', label: 'Agent Action Rejected' },
  { value: 'transaction_scored', label: 'Transaction Scored' },
  { value: 'compliance_monitor_decision', label: 'Compliance Monitor Decision' },
  { value: 'export_initiated', label: 'Export Initiated' },
  { value: 'approval_requested', label: 'Approval Requested' },
  { value: 'approval_decided', label: 'Approval Decided' },
  { value: 'compliance_log_created', label: 'Compliance Log Created' },
]

const REGULATION_TAGS = [
  { value: 'all', label: 'All regulations' },
  { value: 'SEC_17a4', label: 'SEC 17a-4' },
  { value: 'FINRA_4511', label: 'FINRA 4511' },
  { value: 'MiFID_II', label: 'MiFID II' },
  { value: 'CFTC_Part46', label: 'CFTC Part 46' },
]

export default function AuditTrailPage() {
  const [entityType, setEntityType] = useState<string>('all')
  const [eventType, setEventType] = useState<string>('all')
  const [regulationTag, setRegulationTag] = useState<string>('all')
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')

  const { data: entries, isLoading, isError, error } = useAuditTrail({
    limit: 100,
    entity_type: entityType !== 'all' ? entityType : undefined,
    event_type: eventType !== 'all' ? eventType : undefined,
    regulation_tag: regulationTag !== 'all' ? regulationTag : undefined,
    start: startDate ? `${startDate}T00:00:00Z` : undefined,
    end: endDate ? `${endDate}T23:59:59Z` : undefined,
  })

  const hasFilters = entityType !== 'all' || eventType !== 'all' || regulationTag !== 'all' || startDate || endDate
  const clearFilters = () => {
    setEntityType('all')
    setEventType('all')
    setRegulationTag('all')
    setStartDate('')
    setEndDate('')
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <FileText className="h-6 w-6 text-primary" />
          Audit Trail
        </h1>
        <p className="text-sm text-muted-foreground">
          Unified agentic audit trail for compliance (SEC 17a-4, FINRA 4511). Every auditable event from model inference through agent recommendation to human decision.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Audit Events</CardTitle>
          <CardDescription>
            Filterable timeline of all recorded events. Export from the Export page for regulatory evidence.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <Filter className="h-4 w-4 text-muted-foreground shrink-0" />
            <Select value={entityType} onValueChange={setEntityType}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Entity type" />
              </SelectTrigger>
              <SelectContent>
                {ENTITY_TYPES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={eventType} onValueChange={setEventType}>
              <SelectTrigger className="w-[220px]">
                <SelectValue placeholder="Event type" />
              </SelectTrigger>
              <SelectContent>
                {EVENT_TYPES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={regulationTag} onValueChange={setRegulationTag}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Regulation" />
              </SelectTrigger>
              <SelectContent>
                {REGULATION_TAGS.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              type="date"
              placeholder="Start"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-[160px]"
            />
            <Input
              type="date"
              placeholder="End"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-[160px]"
            />
            {hasFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                Clear filters
              </Button>
            )}
          </div>
          {isLoading && <TableSkeleton />}
          {isError && (
            <p className="text-sm text-destructive">
              {error instanceof Error ? error.message : 'Failed to load audit trail'}
            </p>
          )}
          {!isLoading && !isError && entries && (
            <Tabs defaultValue="table" className="w-full">
              <TabsList className="mb-4">
                <TabsTrigger value="table" className="gap-2">
                  <List className="h-4 w-4" />
                  Table
                </TabsTrigger>
                <TabsTrigger value="timeline" className="gap-2">
                  <GitBranch className="h-4 w-4" />
                  Timeline
                </TabsTrigger>
              </TabsList>
              <TabsContent value="table">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead>Actor</TableHead>
                      <TableHead>Details</TableHead>
                      <TableHead>Regulation</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {entries.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                          No audit events yet. Events will appear as incidents, agent actions, and transactions are processed.
                        </TableCell>
                      </TableRow>
                    ) : (
                      entries.map((entry, i) => (
                        <TableRow key={`${entry.timestamp}-${i}`}>
                          <TableCell className="text-muted-foreground text-sm font-mono">
                            {entry.timestamp ? new Date(entry.timestamp).toLocaleString() : '-'}
                          </TableCell>
                          <TableCell className="font-medium">{entry.action}</TableCell>
                          <TableCell>{entry.user}</TableCell>
                          <TableCell className="max-w-xs truncate" title={entry.details}>
                            {entry.details || '-'}
                          </TableCell>
                          <TableCell>
                            <Badge variant="secondary" className="text-xs">
                              {entry.compliance_tag}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TabsContent>
              <TabsContent value="timeline">
                {entries.length === 0 ? (
                  <p className="text-center text-muted-foreground py-8">
                    No audit events yet. Events will appear as incidents, agent actions, and transactions are processed.
                  </p>
                ) : (
                  <div className="relative">
                    {/* Vertical line */}
                    <div className="absolute left-4 top-0 bottom-0 w-px bg-border" />
                    <div className="space-y-0">
                      {[...entries].reverse().map((entry, i) => (
                        <div key={`timeline-${entry.timestamp}-${i}`} className="relative flex gap-4 pb-6 last:pb-0">
                          <div className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-primary bg-background">
                            <div className="h-2 w-2 rounded-full bg-primary" />
                          </div>
                          <div className="flex-1 space-y-1 pt-0.5">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="font-medium">{entry.action}</span>
                              <Badge variant="secondary" className="text-xs">
                                {entry.compliance_tag}
                              </Badge>
                              {entry.entity_type && (
                                <span className="text-xs text-muted-foreground">{entry.entity_type}</span>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {entry.details || '-'}
                            </p>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <span>{entry.user}</span>
                              <span>•</span>
                              <span>{entry.timestamp ? new Date(entry.timestamp).toLocaleString() : '-'}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
