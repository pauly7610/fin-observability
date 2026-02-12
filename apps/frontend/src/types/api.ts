import { z } from 'zod'

// Incident Types
export const IncidentSchema = z.object({
  id: z.union([z.string(), z.number()]),
  incident_id: z.string().optional(),
  title: z.string(),
  description: z.string(),
  status: z.string(),
  severity: z.string(),
  priority: z.number(),
  created_at: z.string(),
  updated_at: z.string(),
  assigned_to: z.number().nullable(),
  type: z.string().optional(),
  desk: z.string().optional(),
  trader: z.string().optional(),
  root_cause: z.string().optional(),
  detection_method: z.string().optional()
})

export type Incident = z.infer<typeof IncidentSchema>

// Compliance Types
export const ComplianceLogSchema = z.object({
  id: z.number(),
  event_type: z.string(),
  severity: z.string(),
  is_resolved: z.boolean(),
  timestamp: z.string(),
  description: z.string()
})

export type ComplianceLog = z.infer<typeof ComplianceLogSchema>

export const ComplianceStatsSchema = z.object({
  total_logs: z.number(),
  resolved_logs: z.number(),
  unresolved_logs: z.number(),
  severity_distribution: z.record(z.string(), z.number())
})

export type ComplianceStats = z.infer<typeof ComplianceStatsSchema>

// AI Agent Types
export const AgentConfigSchema = z.object({
  model: z.string(),
  temperature: z.number(),
  max_tokens: z.number(),
  system_prompt: z.string()
})

export type AgentConfig = z.infer<typeof AgentConfigSchema>

export const AgentMetricsSchema = z.object({
  auto_remediation_status: z.string(),
  resolved_today: z.number(),
  predictive_status: z.string(),
  prevented_incidents: z.number(),
  compliance_status: z.string(),
  regulatory_checks: z.number(),
  config: AgentConfigSchema
})

export type AgentMetrics = z.infer<typeof AgentMetricsSchema>

export const AgentActionSchema = z.object({
  id: z.number(),
  action: z.string(),
  status: z.string(),
  submitted_by: z.string().nullable(),
  created_at: z.string(),
  ai_explanation: z.string().nullable(),
  result: z.any().optional(),
  source: z.string().optional(),
  model: z.string().nullable().optional()
})

export type AgentAction = z.infer<typeof AgentActionSchema>

// LLM Model Configuration
export const ModelOptionSchema = z.object({
  id: z.string(),
  name: z.string(),
  tier: z.string().optional(),
  finance_accuracy: z.string().optional()
})

export const LLMConfigSchema = z.object({
  provider: z.string().nullable(),
  model: z.string().nullable(),
  source: z.string(),
  fallback_active: z.boolean(),
  available_providers: z.array(z.string()),
  available_models: z.record(z.string(), z.array(ModelOptionSchema))
})

export type LLMConfig = z.infer<typeof LLMConfigSchema>

export const RetrainStatusSchema = z.object({
  last_retrain: z.string().nullable(),
  retrain_count: z.number(),
  schedule_hours: z.number()
})

export type RetrainStatus = z.infer<typeof RetrainStatusSchema>

export const LeaderboardEntrySchema = z.object({
  model_version: z.string(),
  f1_score: z.number(),
  precision: z.number(),
  recall: z.number(),
  total_predictions: z.number(),
  timestamp: z.string()
})

export type LeaderboardEntry = z.infer<typeof LeaderboardEntrySchema>

export const ExperimentResultSchema = z.object({
  id: z.string(),
  name: z.string(),
  model_a: z.string(),
  model_b: z.string(),
  traffic_split: z.number(),
  active: z.boolean(),
  results: z.any().optional()
})

export type ExperimentResult = z.infer<typeof ExperimentResultSchema>

// Error Types
export class APIError extends Error {
  constructor(
    public status: number,
    public message: string,
    public code?: string
  ) {
    super(message)
    this.name = 'APIError'
  }
}

export class ValidationError extends Error {
  constructor(public errors: z.ZodError) {
    super('Validation Error')
    this.name = 'ValidationError'
  }
} 