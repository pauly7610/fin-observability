'use client'
import { AIAgentActivity } from "@/components/AIAgentActivity"

export default function AgentPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">AI Agent Activity</h1>
      <AIAgentActivity />
    </div>
  )
}
