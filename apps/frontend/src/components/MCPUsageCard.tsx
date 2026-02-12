'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Plug, Zap, Clock, AlertCircle } from 'lucide-react'
import apiClient from '@/lib/api-client'

interface MCPStats {
  total_calls: number
  tools: Record<string, number>
  avg_latency_ms: number
  errors: number
  recent: Array<{
    tool: string
    timestamp: string
    latency_ms: number
    decision: string
    error: string
  }>
}

export function MCPUsageCard() {
  const { data: stats, isLoading } = useQuery<MCPStats>({
    queryKey: ['mcp-stats'],
    queryFn: async () => {
      const res = await apiClient.get('/mcp/stats')
      return res.data
    },
    refetchInterval: 10000,
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Plug className="h-4 w-4" />
            MCP Connections
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-20 flex items-center justify-center">
            <p className="text-xs text-muted-foreground">Loading...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const totalCalls = stats?.total_calls ?? 0
  const toolCount = stats?.tools ? Object.keys(stats.tools).length : 0
  const avgLatency = stats?.avg_latency_ms ?? 0
  const errors = stats?.errors ?? 0

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Plug className="h-4 w-4" />
            MCP Connections
          </CardTitle>
          {totalCalls > 0 ? (
            <Badge variant="outline" className="text-xs text-emerald-500 border-emerald-500/30 bg-emerald-500/10">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
              Active
            </Badge>
          ) : (
            <Badge variant="outline" className="text-xs text-muted-foreground">
              No calls yet
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-3 mb-3">
          <div className="text-center p-2 rounded-md bg-muted/50">
            <div className="flex items-center justify-center gap-1">
              <Zap className="h-3 w-3 text-primary" />
              <p className="text-lg font-bold">{totalCalls}</p>
            </div>
            <p className="text-[10px] text-muted-foreground">Tool Calls</p>
          </div>
          <div className="text-center p-2 rounded-md bg-muted/50">
            <div className="flex items-center justify-center gap-1">
              <Clock className="h-3 w-3 text-primary" />
              <p className="text-lg font-bold">{avgLatency > 0 ? `${avgLatency}` : '—'}</p>
            </div>
            <p className="text-[10px] text-muted-foreground">Avg ms</p>
          </div>
          <div className="text-center p-2 rounded-md bg-muted/50">
            <div className="flex items-center justify-center gap-1">
              <AlertCircle className="h-3 w-3 text-primary" />
              <p className="text-lg font-bold">{errors}</p>
            </div>
            <p className="text-[10px] text-muted-foreground">Errors</p>
          </div>
        </div>

        {stats?.tools && Object.keys(stats.tools).length > 0 && (
          <div className="space-y-1.5">
            <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">Top Tools</p>
            {Object.entries(stats.tools)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 4)
              .map(([tool, count]) => (
                <div key={tool} className="flex items-center justify-between text-xs">
                  <code className="font-mono text-muted-foreground truncate max-w-[180px]">{tool}</code>
                  <span className="font-medium tabular-nums">{count}</span>
                </div>
              ))}
          </div>
        )}

        {totalCalls === 0 && (
          <p className="text-xs text-muted-foreground text-center py-2">
            Connect an AI agent via <code className="bg-muted px-1 rounded">/connect</code> to see usage.
          </p>
        )}
      </CardContent>
    </Card>
  )
}
