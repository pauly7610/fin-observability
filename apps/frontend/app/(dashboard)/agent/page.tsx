'use client'
import { AIAgentActivity } from "@/components/AIAgentActivity"

export default function AgentPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AI Agent</h1>
        <p className="text-sm text-muted-foreground">
          Review, approve, and manage autonomous agent actions.
        </p>
      </div>
      <AIAgentActivity />
    </div>
  )
}
