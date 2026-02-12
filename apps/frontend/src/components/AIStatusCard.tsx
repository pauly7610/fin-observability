'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useModelConfig, useRetrainStatus } from '@/hooks/useModelManagement'
import { CardSkeleton } from '@/components/CardSkeleton'
import { Bot, Cpu, RefreshCw, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'

export function AIStatusCard() {
  const { config, isLoading: configLoading } = useModelConfig()
  const { status: retrainStatus, isLoading: retrainLoading } = useRetrainStatus()

  if (configLoading || retrainLoading) return <CardSkeleton />

  const isLLM = config?.source === 'llm'

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Bot className="h-4 w-4" />
          AI Agent Status
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Mode */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className={cn('h-4 w-4', isLLM ? 'text-purple-500' : 'text-muted-foreground')} />
            <span className="text-sm font-medium">Mode</span>
          </div>
          <Badge
            variant="outline"
            className={cn(
              'text-xs',
              isLLM
                ? 'text-purple-500 border-purple-500/30 bg-purple-500/10'
                : 'text-muted-foreground'
            )}
          >
            {isLLM ? 'LLM Active' : 'Heuristic'}
          </Badge>
        </div>

        {/* Provider / Model */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Model</span>
          </div>
          <span className="text-xs text-muted-foreground font-mono">
            {config?.model || 'heuristic'}
          </span>
        </div>

        {/* Provider */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium ml-6">Provider</span>
          <span className="text-xs text-muted-foreground capitalize">
            {config?.provider || 'none'}
          </span>
        </div>

        {/* Fallback */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium ml-6">Fallback</span>
          <Badge
            variant="outline"
            className={cn(
              'text-xs',
              config?.fallback_active
                ? 'text-amber-500 border-amber-500/30 bg-amber-500/10'
                : 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10'
            )}
          >
            {config?.fallback_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>

        {/* Divider */}
        <div className="border-t border-border" />

        {/* Retrain Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Last Retrain</span>
          </div>
          <span className="text-xs text-muted-foreground font-mono">
            {retrainStatus?.last_retrain
              ? new Date(retrainStatus.last_retrain).toLocaleDateString()
              : 'Never'}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm font-medium ml-6">Retrain Count</span>
          <span className="text-xs text-muted-foreground font-mono tabular-nums">
            {retrainStatus?.retrain_count ?? 0}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm font-medium ml-6">Schedule</span>
          <span className="text-xs text-muted-foreground">
            Every {retrainStatus?.schedule_hours ?? '—'}h
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
