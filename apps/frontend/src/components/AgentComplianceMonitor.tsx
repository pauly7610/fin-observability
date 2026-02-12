'use client';

import { useState, useEffect } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Transaction {
  id: string;
  amount: number;
  counterparty: string;
  account: string;
  timestamp: string;
  type: 'wire' | 'ach' | 'internal';
}

interface Alternative {
  action: string;
  confidence: number;
  reasoning: string;
}

interface AuditTrail {
  regulation: string;
  timestamp: string;
  agent: string;
}

interface ComplianceResult {
  action: 'approve' | 'block' | 'manual_review';
  confidence: number;
  reasoning: string;
  alternatives: Alternative[];
  audit_trail: AuditTrail;
}

interface TestTransaction extends Transaction {
  label: string;
}

interface ComplianceMetrics {
  total_transactions: number;
  approved: number;
  blocked: number;
  manual_review: number;
  approval_rate: number;
  block_rate: number;
  manual_review_rate: number;
  avg_confidence: number;
  storage: string;
  model?: {
    version: string;
    algorithm: string;
    features: string[];
    training_samples: number;
  };
}

interface TestBatchResult {
  total: number;
  approved: number;
  blocked: number;
  manual_review: number;
  approval_rate: number;
  block_rate: number;
  manual_review_rate: number;
  avg_confidence: number;
  transactions: Array<{
    id: string;
    amount: number;
    type: string;
    hour: number;
    anomaly_score: number;
    action: string;
    confidence: number;
  }>;
}

export function AgentComplianceMonitor() {
  const [result, setResult] = useState<ComplianceResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<ComplianceMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [testBatchResult, setTestBatchResult] = useState<TestBatchResult | null>(null);
  const [testBatchLoading, setTestBatchLoading] = useState(false);
  
  // Fetch metrics on mount and after actions
  const fetchMetrics = async () => {
    setMetricsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/agent/compliance/metrics`);
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
    } finally {
      setMetricsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchMetrics();
  }, []);
  
  const runTestBatch = async () => {
    setTestBatchLoading(true);
    setTestBatchResult(null);
    try {
      const response = await fetch(`${API_BASE}/agent/compliance/test-batch?count=100`, {
        method: 'POST'
      });
      if (response.ok) {
        const data = await response.json();
        setTestBatchResult(data);
        // Refresh metrics after test batch
        fetchMetrics();
      }
    } catch (err) {
      console.error('Test batch failed:', err);
    } finally {
      setTestBatchLoading(false);
    }
  };
  
  const testTransactions: TestTransaction[] = [
    {
      id: 'txn_safe_001',
      amount: 5000,
      counterparty: 'Regular Customer Inc',
      account: '1234567890',
      timestamp: new Date().toISOString(),
      type: 'ach',
      label: 'Safe Transaction ($5k ACH)'
    },
    {
      id: 'txn_suspicious_001',
      amount: 50000,
      counterparty: 'ACME Corp',
      account: '9876543210',
      timestamp: new Date().toISOString(),
      type: 'wire',
      label: 'Suspicious ($50k Wire)'
    },
    {
      id: 'txn_blocked_001',
      amount: 150000,
      counterparty: 'Unknown Entity LLC',
      account: '5555555555',
      timestamp: new Date().toISOString(),
      type: 'wire',
      label: 'Should Block ($150k Wire)'
    }
  ];
  
  const [selectedTxn, setSelectedTxn] = useState<TestTransaction>(testTransactions[1]);
  
  const runComplianceCheck = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const { label, ...txnData } = selectedTxn;
      const response = await fetch(`${API_BASE}/agent/compliance/monitor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(txnData)
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      setResult(data);
      // Refresh metrics after compliance check
      fetchMetrics();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check compliance');
      console.error('Compliance check failed:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const getActionBadgeColor = (action: string) => {
    switch (action) {
      case 'approve': return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30';
      case 'block': return 'bg-red-500/10 text-red-500 border-red-500/30';
      case 'manual_review': return 'bg-amber-500/10 text-amber-500 border-amber-500/30';
      default: return 'bg-muted text-muted-foreground border-border';
    }
  };
  
  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-card rounded-lg border border-border">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">🤖</span>
          <h2 className="text-2xl font-bold text-foreground">
            AI Agent: Financial Compliance Monitor
          </h2>
        </div>
        <div className="flex gap-2 flex-wrap">
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-blue-500/10 text-blue-500 border border-blue-500/30">
            FINRA 4511
          </span>
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-blue-500/10 text-blue-500 border border-blue-500/30">
            SEC 17a-4
          </span>
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-purple-500/10 text-purple-500 border border-purple-500/30">
            Isolation Forest ML v{metrics?.model?.version || '2.0.0'}
          </span>
        </div>
      </div>
      
      {/* Metrics Dashboard */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-foreground">📊 Performance Metrics</h3>
          <button
            onClick={fetchMetrics}
            disabled={metricsLoading}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            {metricsLoading ? 'Refreshing...' : '🔄 Refresh'}
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-muted p-3 rounded-lg border border-border">
            <div className="text-xs text-muted-foreground mb-1">Total Processed</div>
            <div className="text-xl font-bold text-foreground tabular-nums">
              {metrics?.total_transactions ?? 0}
            </div>
          </div>
          <div className="bg-emerald-500/5 p-3 rounded-lg border border-emerald-500/20">
            <div className="text-xs text-muted-foreground mb-1">Auto-Approved</div>
            <div className="text-xl font-bold text-emerald-500 tabular-nums">
              {metrics?.approval_rate ?? 0}%
            </div>
          </div>
          <div className="bg-red-500/5 p-3 rounded-lg border border-red-500/20">
            <div className="text-xs text-muted-foreground mb-1">Blocked</div>
            <div className="text-xl font-bold text-red-500 tabular-nums">
              {metrics?.block_rate ?? 0}%
            </div>
          </div>
          <div className="bg-blue-500/5 p-3 rounded-lg border border-blue-500/20">
            <div className="text-xs text-muted-foreground mb-1">Avg Confidence</div>
            <div className="text-xl font-bold text-blue-500 tabular-nums">
              {metrics?.avg_confidence ?? 0}%
            </div>
          </div>
        </div>
        {metrics?.storage && (
          <div className="mt-2 text-xs text-muted-foreground">
            Storage: {metrics.storage} | Model: {metrics?.model?.algorithm || 'IsolationForest'}
          </div>
        )}
      </div>
      
      {/* Test Batch Section */}
      <div className="mb-6 p-4 bg-amber-500/5 rounded-lg border border-amber-500/20">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-amber-500">🧪 Batch Testing</h3>
            <p className="text-xs text-amber-500/70 mt-1">
              Run 100 synthetic transactions to validate model performance
            </p>
          </div>
          <button
            onClick={runTestBatch}
            disabled={testBatchLoading}
            className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
              testBatchLoading
                ? 'bg-muted text-muted-foreground cursor-not-allowed'
                : 'bg-amber-600 text-white hover:bg-amber-700'
            }`}
          >
            {testBatchLoading ? 'Running...' : 'Run Test Batch'}
          </button>
        </div>
        {testBatchResult && (
          <div className="mt-4 p-3 bg-card rounded border border-amber-500/20">
            <div className="grid grid-cols-4 gap-2 text-center text-sm">
              <div>
                <div className="font-bold text-green-600">{testBatchResult.approval_rate}%</div>
                <div className="text-xs text-muted-foreground">Approved</div>
              </div>
              <div>
                <div className="font-bold text-yellow-600">{testBatchResult.manual_review_rate}%</div>
                <div className="text-xs text-muted-foreground">Review</div>
              </div>
              <div>
                <div className="font-bold text-red-500">{testBatchResult.block_rate}%</div>
                <div className="text-xs text-muted-foreground">Blocked</div>
              </div>
              <div>
                <div className="font-bold text-blue-500">{testBatchResult.avg_confidence}%</div>
                <div className="text-xs text-muted-foreground">Confidence</div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Transaction Selector */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-foreground mb-2">
          Select Test Transaction:
        </label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {testTransactions.map((txn) => (
            <button
              key={txn.id}
              onClick={() => setSelectedTxn(txn)}
              className={`p-3 rounded-lg border-2 transition-all text-left ${
                selectedTxn.id === txn.id
                  ? 'border-primary bg-primary/5'
                  : 'border-border bg-card hover:border-muted-foreground/30'
              }`}
            >
              <div className="font-semibold text-sm">{txn.label}</div>
              <div className="text-xs text-muted-foreground mt-1">
                {txn.counterparty}
              </div>
            </button>
          ))}
        </div>
      </div>
      
      {/* Transaction Details */}
      <div className="mb-6 bg-muted p-4 rounded-lg border border-border">
        <h3 className="font-semibold text-sm text-foreground mb-2">
          Transaction Details
        </h3>
        <pre className="text-xs text-muted-foreground overflow-auto">
          {JSON.stringify(selectedTxn, null, 2)}
        </pre>
      </div>
      
      {/* Run Button */}
      <button
        onClick={runComplianceCheck}
        disabled={loading}
        className={`w-full py-3 px-6 rounded-lg font-semibold text-white transition-all ${
          loading
            ? 'bg-muted text-muted-foreground cursor-not-allowed'
            : 'bg-primary text-primary-foreground hover:bg-primary/90'
        }`}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Analyzing Transaction...
          </span>
        ) : (
          '🔍 Run Compliance Check'
        )}
      </button>
      
      {/* Error Display */}
      {error && (
        <div className="mt-6 p-4 bg-red-500/5 border-l-4 border-red-500 rounded">
          <div className="flex items-center gap-2">
            <span className="text-red-500 font-semibold">❌ Error:</span>
            <span className="text-red-400">{error}</span>
          </div>
        </div>
      )}
      
      {/* Results Display */}
      {result && (
        <div className="mt-6 space-y-4">
          {/* Action Badge */}
          <div className="flex items-center gap-3">
            <span className={`px-4 py-2 text-sm font-bold rounded-lg border-2 ${getActionBadgeColor(result.action)}`}>
              {result.action.toUpperCase().replace('_', ' ')}
            </span>
            <span className="text-sm text-muted-foreground">
              Confidence: <span className="font-semibold tabular-nums">{result.confidence}%</span>
            </span>
          </div>
          
          {/* Reasoning */}
          <div className="bg-primary/5 border-l-4 border-primary p-4 rounded">
            <p className="text-sm font-semibold text-foreground mb-1">
              🧠 Agent Reasoning:
            </p>
            <p className="text-sm text-muted-foreground">{result.reasoning}</p>
          </div>
          
          {/* Alternatives */}
          {result.alternatives.length > 0 && (
            <div>
              <p className="text-sm font-semibold text-foreground mb-2">
                🔀 Alternative Actions Considered:
              </p>
              <div className="space-y-2">
                {result.alternatives.map((alt, idx) => (
                  <div
                    key={idx}
                    className="bg-muted p-3 rounded-lg border border-border"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm text-foreground">
                        {alt.action}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        ({(alt.confidence * 100).toFixed(1)}% confidence)
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">{alt.reasoning}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Audit Trail */}
          <div className="bg-muted p-4 rounded-lg border-t-2 border-border">
            <p className="text-xs font-semibold text-muted-foreground mb-2">
              📋 Audit Trail
            </p>
            <div className="space-y-1 text-xs text-foreground">
              <div className="flex gap-2">
                <span className="font-semibold">Regulation:</span>
                <span>{result.audit_trail.regulation}</span>
              </div>
              <div className="flex gap-2">
                <span className="font-semibold">Agent:</span>
                <span>{result.audit_trail.agent}</span>
              </div>
              <div className="flex gap-2">
                <span className="font-semibold">Timestamp:</span>
                <span>{new Date(result.audit_trail.timestamp).toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
