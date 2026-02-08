'use client'
import { useState } from 'react'
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card"
import { useAIAgentActivity } from "@/hooks/useAIAgentActivity"
import { useModelConfig } from "@/hooks/useModelManagement"
import { AgentAction } from "@/types/api"

function SourceBadge({ source, model }: { source?: string; model?: string | null }) {
  if (source === 'llm') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded-full bg-purple-100 text-purple-800 border border-purple-300">
        LLM {model && <span className="text-purple-600">({model})</span>}
      </span>
    )
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 text-xs font-semibold rounded-full bg-gray-100 text-gray-600 border border-gray-300">
      Heuristic
    </span>
  )
}

export function AIAgentActivity() {
  const { actions, isLoading, isError, error, triageIncident, approveAction, rejectAction } = useAIAgentActivity()
  const { config } = useModelConfig()
  const typedActions: AgentAction[] = actions
  const [expandedId, setExpandedId] = useState<number | null>(null)

  if (isLoading) return <div>Loading...</div>
  if (isError) return <div>Error loading data: {error?.message}</div>

  return (
    <div className="space-y-4">
      {/* Model Status Card */}
      {config && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Model Status
              <SourceBadge source={config.source} model={config.model} />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div>
                <span className="text-gray-500">Provider:</span>{' '}
                <span className="font-medium capitalize">{config.provider || 'none'}</span>
              </div>
              <div>
                <span className="text-gray-500">Model:</span>{' '}
                <span className="font-medium">{config.model || 'heuristic'}</span>
              </div>
              <div>
                <span className="text-gray-500">Mode:</span>{' '}
                <span className="font-medium">{config.source}</span>
              </div>
              <div>
                <span className="text-gray-500">Fallback:</span>{' '}
                <span className="font-medium">{config.fallback_active ? 'Active' : 'Inactive'}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Agent Actions</CardTitle>
        </CardHeader>
        <CardContent>
          {typedActions.length === 0 ? (
            <div>No agent actions available.</div>
          ) : (
            <ul>
              {typedActions.map(action => (
                <li key={action.id} className="mb-4 border-b pb-2">
                  <div className="flex items-center gap-2 mb-1">
                    <b>Type:</b> {action.action}
                    <SourceBadge source={action.source} model={action.model} />
                  </div>
                  <div><b>Status:</b> {action.status}</div>
                  <div><b>Submitted by:</b> {action.submitted_by}</div>
                  <div><b>Created at:</b> {action.created_at}</div>
                  {/* Collapsible AI Explanation */}
                  {action.ai_explanation && (
                    <div className="mt-2">
                      <button
                        onClick={() => setExpandedId(expandedId === action.id ? null : action.id)}
                        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                      >
                        {expandedId === action.id ? 'Hide' : 'Show'} AI Explanation
                      </button>
                      {expandedId === action.id && (
                        <div className="mt-2 p-3 bg-blue-50 border-l-4 border-blue-500 rounded text-sm text-blue-900">
                          {action.ai_explanation}
                        </div>
                      )}
                    </div>
                  )}
                  <div className="flex gap-2 mt-2">
                    {action.status === 'pending' && (
                      <>
                        <button className="px-2 py-1 bg-green-500 text-white rounded" onClick={() => approveAction.mutate({ actionId: action.id, approvedBy: 1 })}>Approve</button>
                        <button className="px-2 py-1 bg-red-500 text-white rounded" onClick={() => rejectAction.mutate({ actionId: action.id, approvedBy: 1 })}>Reject</button>
                      </>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
      {/* Example triage trigger (replace with real form as needed) */}
      <Card>
        <CardHeader>
          <CardTitle>Trigger Triage (Demo)</CardTitle>
        </CardHeader>
        <CardContent>
          <button className="px-4 py-2 bg-blue-500 text-white rounded" onClick={() => triageIncident.mutate({ incident_id: 'demo', description: 'Test incident' })}>
            Trigger Triage
          </button>
        </CardContent>
      </Card>
    </div>
  )
}
