'use client'

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { cn } from '@/lib/utils'
import { useState } from 'react'
import { CheckCircle, AlertTriangle, Clock, Search, ChevronUp, ChevronDown } from 'lucide-react'

const severityStyles: Record<string, string> = {
  critical: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-amber-500',
  low: 'bg-blue-500',
}

const severityBadge: Record<string, string> = {
  critical: 'text-red-500 border-red-500/30 bg-red-500/10',
  high: 'text-orange-500 border-orange-500/30 bg-orange-500/10',
  medium: 'text-amber-500 border-amber-500/30 bg-amber-500/10',
  low: 'text-blue-500 border-blue-500/30 bg-blue-500/10',
}

const statusBadge: Record<string, { class: string; icon: React.ReactNode }> = {
  open: {
    class: 'text-red-500 border-red-500/30 bg-red-500/10',
    icon: <AlertTriangle className="h-3 w-3" />,
  },
  investigating: {
    class: 'text-amber-500 border-amber-500/30 bg-amber-500/10',
    icon: <Search className="h-3 w-3" />,
  },
  resolved: {
    class: 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10',
    icon: <CheckCircle className="h-3 w-3" />,
  },
  closed: {
    class: 'text-muted-foreground border-border bg-muted',
    icon: <CheckCircle className="h-3 w-3" />,
  },
}

function timeAgo(dateStr: string): string {
  const now = new Date()
  const date = new Date(dateStr)
  const diffMs = now.getTime() - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return 'just now'
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.floor(diffHr / 24)
  return `${diffDay}d ago`
}

interface IncidentTableProps {
  incidents: any[]
  onSelect?: (incident: any) => void
  onBulkResolve?: (ids: string[]) => void
  onBulkAssign?: (ids: string[], assignedTo: number) => void
}

type SortField = 'severity' | 'created_at' | 'status' | 'title'
type SortDir = 'asc' | 'desc'

const severityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 }

export function IncidentTable({ incidents, onSelect, onBulkResolve }: IncidentTableProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [sortField, setSortField] = useState<SortField>('created_at')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  const toggleSelect = (id: string) => {
    const next = new Set(selected)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelected(next)
  }

  const toggleAll = () => {
    if (selected.size === incidents.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(incidents.map((i: any) => i.incident_id || i.id)))
    }
  }

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDir('desc')
    }
  }

  const sorted = [...incidents].sort((a, b) => {
    const dir = sortDir === 'asc' ? 1 : -1
    if (sortField === 'severity') {
      return ((severityOrder[a.severity] ?? 4) - (severityOrder[b.severity] ?? 4)) * dir
    }
    if (sortField === 'created_at') {
      return (new Date(a.created_at).getTime() - new Date(b.created_at).getTime()) * dir
    }
    if (sortField === 'status' || sortField === 'title') {
      return (a[sortField] || '').localeCompare(b[sortField] || '') * dir
    }
    return 0
  })

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null
    return sortDir === 'asc' ? (
      <ChevronUp className="h-3 w-3 inline ml-1" />
    ) : (
      <ChevronDown className="h-3 w-3 inline ml-1" />
    )
  }

  return (
    <div>
      {/* Bulk actions toolbar */}
      {selected.size > 0 && (
        <div className="flex items-center gap-3 mb-3 p-3 rounded-lg bg-muted border border-border">
          <span className="text-sm font-medium">
            {selected.size} selected
          </span>
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              onBulkResolve?.(Array.from(selected))
              setSelected(new Set())
            }}
            className="text-emerald-500 border-emerald-500/30 hover:bg-emerald-500/10"
          >
            <CheckCircle className="h-3.5 w-3.5 mr-1.5" />
            Resolve
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setSelected(new Set())}
          >
            Clear
          </Button>
        </div>
      )}

      <div className="rounded-lg border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-10">
                <Checkbox
                  checked={selected.size === incidents.length && incidents.length > 0}
                  onCheckedChange={toggleAll}
                />
              </TableHead>
              <TableHead className="w-8" />
              <TableHead
                className="cursor-pointer select-none"
                onClick={() => handleSort('title')}
              >
                Incident <SortIcon field="title" />
              </TableHead>
              <TableHead
                className="cursor-pointer select-none"
                onClick={() => handleSort('severity')}
              >
                Severity <SortIcon field="severity" />
              </TableHead>
              <TableHead
                className="cursor-pointer select-none"
                onClick={() => handleSort('status')}
              >
                Status <SortIcon field="status" />
              </TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Desk</TableHead>
              <TableHead
                className="cursor-pointer select-none text-right"
                onClick={() => handleSort('created_at')}
              >
                Time <SortIcon field="created_at" />
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sorted.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-12">
                  <div className="flex flex-col items-center gap-2">
                    <CheckCircle className="h-8 w-8 text-emerald-500/50" />
                    <p className="text-sm text-muted-foreground">No incidents found</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              sorted.map((incident: any) => {
                const id = incident.incident_id || incident.id
                const sev = severityStyles[incident.severity] || severityStyles.low
                const sevBadge = severityBadge[incident.severity] || severityBadge.low
                const stat = statusBadge[incident.status] || statusBadge.open
                const isSelected = selected.has(id)

                return (
                  <TableRow
                    key={id}
                    className={cn(
                      'cursor-pointer transition-colors',
                      isSelected && 'bg-muted/50'
                    )}
                    onClick={() => onSelect?.(incident)}
                  >
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={() => toggleSelect(id)}
                      />
                    </TableCell>
                    <TableCell>
                      <div className={cn('h-2.5 w-2.5 rounded-full', sev)} />
                    </TableCell>
                    <TableCell>
                      <div>
                        <span className="text-sm font-medium">{incident.title}</span>
                        <p className="text-xs text-muted-foreground truncate max-w-[300px]">
                          {incident.description}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={cn('text-xs', sevBadge)}>
                        {incident.severity}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={cn('text-xs gap-1', stat.class)}>
                        {stat.icon}
                        {incident.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-xs text-muted-foreground">
                        {incident.type || '—'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-xs text-muted-foreground">
                        {incident.desk || '—'}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="text-xs text-muted-foreground tabular-nums">
                        {timeAgo(incident.created_at)}
                      </span>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
