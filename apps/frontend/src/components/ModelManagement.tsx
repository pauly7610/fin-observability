'use client'

import { useState } from 'react'
import { useModelConfig, useRetrainStatus, useLeaderboard, useTriggerRetrain } from '@/hooks/useModelManagement'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { CardSkeleton, TableSkeleton } from '@/components/CardSkeleton'
import { Cpu, RefreshCw, Trophy, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'

export function ModelManagement() {
  const { config, isLoading: configLoading, updateModel } = useModelConfig()
  const { status: retrainStatus, isLoading: retrainLoading } = useRetrainStatus()
  const { entries: leaderboard, isLoading: leaderboardLoading } = useLeaderboard()
  const triggerRetrain = useTriggerRetrain()

  const [selectedProvider, setSelectedProvider] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState<string>('')

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider)
    const models = config?.available_models?.[provider]
    if (models && models.length > 0) {
      setSelectedModel(models[0].id)
    }
  }

  const handleApplyModel = () => {
    if (selectedProvider && selectedModel) {
      updateModel.mutate({ provider: selectedProvider, model: selectedModel })
    }
  }

  const currentProvider = config?.provider || 'none'
  const currentModel = config?.model || 'heuristic fallback'
  const isLLMActive = config?.source === 'llm'

  if (configLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
        <TableSkeleton rows={4} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Current Status */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Cpu className="h-4 w-4" />
            LLM Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="p-3 rounded-lg bg-muted border border-border">
              <div className="text-xs text-muted-foreground mb-1">Mode</div>
              <div className="flex items-center gap-2">
                <span className={cn(
                  'inline-block w-2 h-2 rounded-full',
                  isLLMActive ? 'bg-purple-500' : 'bg-muted-foreground'
                )} />
                <span className="text-sm font-semibold">
                  {isLLMActive ? 'LLM' : 'Heuristic'}
                </span>
              </div>
            </div>
            <div className="p-3 rounded-lg bg-muted border border-border">
              <div className="text-xs text-muted-foreground mb-1">Provider</div>
              <div className="text-sm font-semibold capitalize">{currentProvider}</div>
            </div>
            <div className="p-3 rounded-lg bg-muted border border-border">
              <div className="text-xs text-muted-foreground mb-1">Model</div>
              <div className="text-sm font-semibold truncate">{currentModel}</div>
            </div>
            <div className="p-3 rounded-lg bg-muted border border-border">
              <div className="text-xs text-muted-foreground mb-1">Fallback</div>
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
          </div>

          {/* Model Selector */}
          {config && (
            <div className="pt-4 border-t border-border">
              <div className="flex flex-wrap items-end gap-3">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">Provider</label>
                  <Select
                    value={selectedProvider || currentProvider}
                    onValueChange={handleProviderChange}
                  >
                    <SelectTrigger className="w-[160px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {config.available_providers.map((p) => (
                        <SelectItem key={p} value={p}>
                          {p.charAt(0).toUpperCase() + p.slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">Model</label>
                  <Select value={selectedModel} onValueChange={setSelectedModel}>
                    <SelectTrigger className="w-[280px]">
                      <SelectValue placeholder="Select model..." />
                    </SelectTrigger>
                    <SelectContent>
                      {(config.available_models[selectedProvider || currentProvider] || []).map((m) => (
                        <SelectItem key={m.id} value={m.id}>
                          {m.name} ({m.tier}) — {m.finance_accuracy}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  onClick={handleApplyModel}
                  disabled={updateModel.isPending}
                  size="sm"
                >
                  {updateModel.isPending ? 'Applying...' : 'Apply'}
                </Button>
              </div>
              {updateModel.isSuccess && (
                <p className="mt-2 text-xs text-emerald-500">Model updated successfully.</p>
              )}
              {updateModel.isError && (
                <p className="mt-2 text-xs text-red-500">Failed to update model.</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Retraining */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <RefreshCw className="h-4 w-4" />
              ML Model Retraining
            </CardTitle>
            <Button
              size="sm"
              variant="outline"
              onClick={() => triggerRetrain.mutate()}
              disabled={triggerRetrain.isPending}
              className="text-amber-500 border-amber-500/30 hover:bg-amber-500/10"
            >
              <RefreshCw className={cn('h-3.5 w-3.5 mr-1.5', triggerRetrain.isPending && 'animate-spin')} />
              {triggerRetrain.isPending ? 'Retraining...' : 'Trigger Retrain'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {retrainStatus && !retrainLoading && (
            <div className="grid grid-cols-3 gap-4">
              <div className="p-3 rounded-lg bg-muted border border-border">
                <div className="text-xs text-muted-foreground mb-1">Last Retrain</div>
                <div className="text-sm font-semibold">
                  {retrainStatus.last_retrain
                    ? new Date(retrainStatus.last_retrain).toLocaleString()
                    : 'Never'}
                </div>
              </div>
              <div className="p-3 rounded-lg bg-muted border border-border">
                <div className="text-xs text-muted-foreground mb-1">Retrain Count</div>
                <div className="text-sm font-semibold tabular-nums">{retrainStatus.retrain_count}</div>
              </div>
              <div className="p-3 rounded-lg bg-muted border border-border">
                <div className="text-xs text-muted-foreground mb-1">Schedule</div>
                <div className="text-sm font-semibold">Every {retrainStatus.schedule_hours}h</div>
              </div>
            </div>
          )}
          {triggerRetrain.isSuccess && (
            <p className="mt-3 text-xs text-emerald-500">Retraining completed successfully.</p>
          )}
          {triggerRetrain.isError && (
            <p className="mt-3 text-xs text-red-500">Retraining failed.</p>
          )}
        </CardContent>
      </Card>

      {/* Leaderboard */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Trophy className="h-4 w-4" />
            Model Leaderboard
          </CardTitle>
        </CardHeader>
        <CardContent>
          {leaderboardLoading ? (
            <TableSkeleton rows={4} />
          ) : leaderboard.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Trophy className="h-10 w-10 text-muted-foreground/30 mb-3" />
              <p className="text-sm text-muted-foreground">No model versions evaluated yet.</p>
            </div>
          ) : (
            <div className="rounded-lg border border-border overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead>Version</TableHead>
                    <TableHead className="text-right">F1</TableHead>
                    <TableHead className="text-right">Precision</TableHead>
                    <TableHead className="text-right">Recall</TableHead>
                    <TableHead className="text-right">Predictions</TableHead>
                    <TableHead className="text-right">Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {leaderboard.map((entry, idx) => (
                    <TableRow
                      key={entry.model_version}
                      className={cn(idx === 0 && 'bg-emerald-500/5')}
                    >
                      <TableCell className="font-medium">
                        {idx === 0 && (
                          <Trophy className="h-3.5 w-3.5 text-amber-500 inline mr-1.5" />
                        )}
                        {entry.model_version}
                      </TableCell>
                      <TableCell className="text-right font-semibold tabular-nums">
                        {(entry.f1_score * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell className="text-right tabular-nums text-muted-foreground">
                        {(entry.precision * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell className="text-right tabular-nums text-muted-foreground">
                        {(entry.recall * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell className="text-right tabular-nums text-muted-foreground">
                        {entry.total_predictions}
                      </TableCell>
                      <TableCell className="text-right text-xs text-muted-foreground">
                        {new Date(entry.timestamp).toLocaleDateString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
