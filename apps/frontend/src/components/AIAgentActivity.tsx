'use client'
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card"
import { useAIAgentActivity } from "@/hooks/useAIAgentActivity"
import { AgentAction } from "@/types/api"

export function AIAgentActivity() {
  const { actions, isLoading, isError, error, triageIncident, approveAction, rejectAction } = useAIAgentActivity()
  const typedActions: AgentAction[] = actions

  if (isLoading) return <div>Loading...</div>
  if (isError) return <div>Error loading data: {error?.message}</div>

  return (
    <div className="space-y-4">
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
                  <div><b>Type:</b> {action.action}</div>
                  <div><b>Status:</b> {action.status}</div>
                  <div><b>Submitted by:</b> {action.submitted_by}</div>
                  <div><b>Created at:</b> {action.created_at}</div>
                  <div><b>AI Explanation:</b> {action.ai_explanation}</div>
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
