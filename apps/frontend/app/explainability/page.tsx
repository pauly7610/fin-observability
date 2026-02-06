'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
      const res = await fetch(`${API_BASE}/agent/compliance/explain`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-user-email': 'admin@example.com',
          'x-user-role': 'admin',
        },
        body: JSON.stringify({
          transaction: {
            amount: parseFloat(amount),
            type,
            timestamp: new Date(timestamp).toISOString(),
          },
        }),
      })
      if (!res.ok) throw new Error(await res.text())
      setResult(await res.json())
    } catch (e: any) {
      setError(e.message || 'Failed to explain')
    } finally {
      setLoading(false)
    }
  }

  const maxShap = result
    ? Math.max(...result.features.map((f) => f.abs_importance), 0.001)
    : 1

  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">Model Explainability (SHAP)</h1>
      <p className="text-muted-foreground">
        Understand why the model made a specific compliance decision. SHAP values show each
        feature&apos;s contribution to the anomaly score.
      </p>

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
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Type</label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="w-full px-3 py-2 border rounded-md bg-background"
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
                className="w-full px-3 py-2 border rounded-md bg-background"
              />
            </div>
          </div>
          <button
            onClick={handleExplain}
            disabled={loading}
            className="mt-4 px-6 py-2 bg-primary text-primary-foreground rounded-md hover:opacity-90 disabled:opacity-50"
          >
            {loading ? 'Analyzing...' : 'Explain Decision'}
          </button>
          {error && <p className="mt-2 text-red-500 text-sm">{error}</p>}
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

          {/* Waterfall */}
          <Card>
            <CardHeader>
              <CardTitle>Score Waterfall</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 font-mono text-sm">
                <div className="flex justify-between border-b pb-1">
                  <span>Base Score</span>
                  <span>{result.waterfall.base.toFixed(4)}</span>
                </div>
                {result.waterfall.steps.map((step) => (
                  <div key={step.feature} className="flex justify-between">
                    <span className="text-muted-foreground">
                      {step.contribution >= 0 ? '+' : ''}
                      {step.contribution.toFixed(4)}{' '}
                      <span className="text-xs">
                        ({FEATURE_LABELS[step.feature] || step.feature})
                      </span>
                    </span>
                  </div>
                ))}
                <div className="flex justify-between border-t pt-1 font-bold">
                  <span>Final Score</span>
                  <span>{result.waterfall.final.toFixed(4)}</span>
                </div>
              </div>
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
