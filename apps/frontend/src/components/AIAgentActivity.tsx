'use client'

import { useState } from 'react'
import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useAIAgentActivity } from '@/hooks/useAIAgentActivity'
import { useModelConfig } from '@/hooks/useModelManagement'
import { AgentAction } from '@/types/api'
import { CardSkeleton } from '@/components/CardSkeleton'
import { ErrorState } from '@/components/ErrorState'
import { Bot, CheckCircle, XCircle, Clock, ChevronDown, ChevronUp, Cpu, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'

const statusConfig: Record<string, { class: string; icon: React.ReactNode }> = {
  pending: {
    class: 'text-amber-500 border-amber-500/30 bg-amber-500/10',
    icon: <Clock className="h-3 w-3" />,
  },
  approved: {
    class: 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10',
    icon: <CheckCircle className="h-3 w-3" />,
  },
  rejected: {
    class: 'text-red-500 border-red-500/30 bg-red-500/10',
    icon: <XCircle className="h-3 w-3" />,
  },
  executed: {
    class: 'text-blue-500 border-blue-500/30 bg-blue-500/10',
    icon: <Zap className="h-3 w-3" />,
  },
}

export function AIAgentActivity() {
  const { actions, isLoading, isError, error, approveAction, rejectAction } = useAIAgentActivity()
  const { config } = useModelConfig()
  const typedActions: AgentAction[] = actions
  const [expandedId, setExpandedId] = useState<number | null>(null)

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (isError) {
    return <ErrorState message={error?.message} onRetry={() => window.location.reload()} />
  }

  return (
    <div className="space-y-4">
      {/* Model Status */}
      {config && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-4 flex-wrap">
              <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Mode:</span>
                <Badge
                  variant="outline"
                  className={cn(
                    'text-xs',
                    config.source === 'llm'
                      ? 'text-purple-500 border-purple-500/30 bg-purple-500/10'
                      : 'text-muted-foreground'
                  )}
                >
                  {config.source === 'llm' ? `LLM (${config.model})` : 'Heuristic'}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Provider:</span>
                <span className="text-sm font-medium capitalize">{config.provider || 'none'}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Fallback:</span>
                <Badge
                  variant="outline"
                  className={cn(
                    'text-xs',
                    config.fallback_active
                      ? 'text-amber-500 border-amber-500/30 bg-amber-500/10'
                      : 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10'
                  )}
                >
                  {config.fallback_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Agent Actions */}
      {typedActions.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Bot className="h-10 w-10 text-muted-foreground/30 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">No agent actions yet.</p>
          </CardContent>
        </Card>
      ) : (
        typedActions.map((action) => {
          const stat = statusConfig[action.status] || statusConfig.pending
          const isExpanded = expandedId === action.id
          const isPending = action.status === 'pending'

          return (
            <Card
              key={action.id}
              className={cn(
                'transition-colors',
                isPending && 'border-l-2 border-l-amber-500'
              )}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                      <span className="text-sm font-semibold">{action.action}</span>
                      <Badge variant="outline" className={cn('text-xs gap-1', stat.class)}>
                        {stat.icon}
                        {action.status}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={cn(
                          'text-xs',
                          action.source === 'llm'
                            ? 'text-purple-500 border-purple-500/30 bg-purple-500/10'
                            : 'text-muted-foreground'
                        )}
                      >
                        {action.source === 'llm' ? `LLM` : 'Heuristic'}
                        {action.model && ` · ${action.model}`}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>By: {action.submitted_by}</span>
                      <span className="tabular-nums">
                        {new Date(action.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    {isPending && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => approveAction.mutate({ actionId: action.id, approvedBy: 1 })}
                          className="text-emerald-500 border-emerald-500/30 hover:bg-emerald-500/10 h-7 text-xs"
                        >
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => rejectAction.mutate({ actionId: action.id, approvedBy: 1 })}
                          className="text-red-500 border-red-500/30 hover:bg-red-500/10 h-7 text-xs"
                        >
                          <XCircle className="h-3 w-3 mr-1" />
                          Reject
                        </Button>
                      </>
                    )}
                  </div>
                </div>

                {/* AI Explanation */}
                {action.ai_explanation && (
                  <div className="mt-3">
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : action.id)}
                      className="flex items-center gap-1 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                    >
                      {isExpanded ? (
                        <ChevronUp className="h-3 w-3" />
                      ) : (
                        <ChevronDown className="h-3 w-3" />
                      )}
                      AI Explanation
                    </button>
                    {isExpanded && (
                      <div className="mt-2 p-3 rounded-lg bg-primary/5 border border-primary/10 text-sm text-foreground">
                        {action.ai_explanation}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })
      )}
    </div>
  )
}
