'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts'
import apiClient from '@/lib/api-client'

interface FeatureExplanation {
  feature: string
  value: number
  shap_value: number
  direction: string
  abs_importance: number
}

interface ExplainResult {
  anomaly_score: number
  base_value: number
  model_output: number
  model_version: string
  features: FeatureExplanation[]
  top_risk_factors: FeatureExplanation[]
  top_safe_factors: FeatureExplanation[]
  waterfall: {
    base: number
    steps: { feature: string; contribution: number }[]
    final: number
  }
}

const FEATURE_LABELS: Record<string, string> = {
  amount: 'Transaction Amount',
  hour: 'Hour of Day',
  day_of_week: 'Day of Week',
  is_weekend: 'Weekend',
  is_off_hours: 'Off-Hours',
  txn_type_encoded: 'Transaction Type',
}

interface WaterfallProps {
  waterfall: {
    base: number
    steps: { feature: string; contribution: number }[]
    final: number
  }
}

function WaterfallChart({ waterfall }: WaterfallProps) {
  // Build waterfall data: each bar shows the invisible "base" portion and the visible contribution
  const data: {
    name: string
    invisible: number
    value: number
    isPositive: boolean
    isTotal: boolean
  }[] = []

  let running = waterfall.base
  data.push({
    name: 'Base',
    invisible: 0,
    value: waterfall.base,
    isPositive: true,
    isTotal: true,
  })

  for (const step of waterfall.steps) {
    const contribution = step.contribution
    if (contribution >= 0) {
      data.push({
        name: FEATURE_LABELS[step.feature] || step.feature,
        invisible: running,
        value: contribution,
        isPositive: true,
        isTotal: false,
      })
    } else {
      data.push({
        name: FEATURE_LABELS[step.feature] || step.feature,
        invisible: running + contribution,
        value: Math.abs(contribution),
        isPositive: false,
        isTotal: false,
      })
    }
    running += contribution
  }

  data.push({
    name: 'Final',
    invisible: 0,
    value: waterfall.final,
    isPositive: waterfall.final >= waterfall.base,
    isTotal: true,
  })

  const maxVal = Math.max(...data.map((d) => d.invisible + d.value), 0.01)

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={Math.max(280, data.length * 40)}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 10, right: 40, left: 120, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis
            type="number"
            domain={[0, Math.ceil(maxVal * 1.1 * 10000) / 10000]}
            tickFormatter={(v: number) => v.toFixed(3)}
            fontSize={11}
          />
          <YAxis type="category" dataKey="name" width={110} fontSize={11} />
          <Tooltip
            formatter={(value: number, name: string) => {
              if (name === 'invisible') return [null, null]
              return [value.toFixed(4), 'Contribution']
            }}
            labelFormatter={(label: string) => label}
          />
          <ReferenceLine x={waterfall.base} stroke="#888" strokeDasharray="3 3" />
          {/* Invisible spacer bar */}
          <Bar dataKey="invisible" stackId="stack" fill="transparent" />
          {/* Visible contribution bar */}
          <Bar dataKey="value" stackId="stack" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={index}
                fill={
                  entry.isTotal
                    ? '#6366f1'
                    : entry.isPositive
                    ? '#ef4444'
                    : '#22c55e'
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="flex gap-4 mt-2 text-xs text-muted-foreground justify-center">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-indigo-500 rounded inline-block" /> Total
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-red-500 rounded inline-block" /> Risk Increasing
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 bg-green-500 rounded inline-block" /> Risk Decreasing
        </span>
      </div>
    </div>
  )
}

export default function ExplainabilityPage() {
  const [amount, setAmount] = useState('25000')
  const [type, setType] = useState('wire')
  const [timestamp, setTimestamp] = useState(new Date().toISOString().slice(0, 16))
  const [result, setResult] = useState<ExplainResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleExplain = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await apiClient.post('/agent/compliance/explain', {
        transaction: {
          amount: parseFloat(amount),
          type,
          timestamp: new Date(timestamp).toISOString(),
        },
      })
      setResult(res.data)
    } catch (e: unknown) {
      const err = e as { message?: string; response?: { data?: { detail?: string } } }
      setError(err.message || err.response?.data?.detail || 'Failed to explain')
    } finally {
      setLoading(false)
    }
  }

  const maxShap = result
    ? Math.max(...result.features.map((f) => f.abs_importance), 0.001)
    : 1

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Model Explainability</h1>
        <p className="text-sm text-muted-foreground">
          Understand why the model made a specific compliance decision. SHAP values show each
          feature&apos;s contribution to the anomaly score.
        </p>
      </div>

      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction to Explain</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Amount ($)</label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full h-9 px-3 py-2 border border-border rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Type</label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="w-full h-9 px-3 py-2 border border-border rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="ach">ACH</option>
                <option value="wire">Wire</option>
                <option value="internal">Internal</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Timestamp</label>
              <input
                type="datetime-local"
                value={timestamp}
                onChange={(e) => setTimestamp(e.target.value)}
                className="w-full h-9 px-3 py-2 border border-border rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          </div>
          <button
            onClick={handleExplain}
            disabled={loading}
            className="mt-4 inline-flex items-center justify-center h-9 px-6 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:pointer-events-none transition-colors"
          >
            {loading ? 'Analyzing...' : 'Explain Decision'}
          </button>
          {error && (
            <div className="mt-3 p-3 rounded-lg bg-red-500/5 border border-red-500/20 text-sm text-red-500">
              {error.includes('fetch') || error.includes('Network')
                ? 'Backend unavailable — make sure the API server is running.'
                : error}
            </div>
          )}
        </CardContent>
      </Card>

      {result && (
        <>
          {/* Score Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-6 text-center">
                <div className="text-4xl font-bold">
                  {(result.anomaly_score * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-muted-foreground mt-1">Anomaly Score</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 text-center">
                <div className="text-4xl font-bold">{result.model_version}</div>
                <div className="text-sm text-muted-foreground mt-1">Model Version</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 text-center">
                <div className="text-4xl font-bold">{result.features.length}</div>
                <div className="text-sm text-muted-foreground mt-1">Features Analyzed</div>
              </CardContent>
            </Card>
          </div>

          {/* Feature Importance Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Feature Contributions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {result.features.map((f) => (
                  <div key={f.feature} className="flex items-center gap-3">
                    <div className="w-40 text-sm font-medium truncate">
                      {FEATURE_LABELS[f.feature] || f.feature}
                    </div>
                    <div className="flex-1 flex items-center gap-2">
                      <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden relative">
                        <div
                          className={`h-full rounded-full ${
                            f.direction === 'risk_increasing'
                              ? 'bg-red-500'
                              : 'bg-green-500'
                          }`}
                          style={{
                            width: `${(f.abs_importance / maxShap) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="w-20 text-xs text-right font-mono">
                        {f.shap_value > 0 ? '+' : ''}
                        {f.shap_value.toFixed(4)}
                      </span>
                    </div>
                    <div className="w-24 text-xs text-muted-foreground text-right">
                      val: {f.value.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex gap-4 mt-4 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-red-500 rounded-full inline-block" /> Risk
                  Increasing
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-green-500 rounded-full inline-block" /> Risk
                  Decreasing
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Waterfall Chart (Recharts) */}
          <Card>
            <CardHeader>
              <CardTitle>Score Waterfall</CardTitle>
            </CardHeader>
            <CardContent>
              <WaterfallChart waterfall={result.waterfall} />
            </CardContent>
          </Card>

          {/* Risk & Safe Factors */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-red-500">Top Risk Factors</CardTitle>
              </CardHeader>
              <CardContent>
                {result.top_risk_factors.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No risk-increasing factors</p>
                ) : (
                  <ul className="space-y-2">
                    {result.top_risk_factors.map((f) => (
                      <li key={f.feature} className="text-sm">
                        <strong>{FEATURE_LABELS[f.feature] || f.feature}</strong>: {f.value.toFixed(2)}{' '}
                        (impact: {f.shap_value.toFixed(4)})
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-green-500">Top Safe Factors</CardTitle>
              </CardHeader>
              <CardContent>
                {result.top_safe_factors.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No risk-decreasing factors</p>
                ) : (
                  <ul className="space-y-2">
                    {result.top_safe_factors.map((f) => (
                      <li key={f.feature} className="text-sm">
                        <strong>{FEATURE_LABELS[f.feature] || f.feature}</strong>: {f.value.toFixed(2)}{' '}
                        (impact: {f.shap_value.toFixed(4)})
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
