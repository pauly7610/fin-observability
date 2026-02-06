'use client';

import { useState } from 'react';

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

export function AgentComplianceMonitor() {
  const [result, setResult] = useState<ComplianceResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
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
      const response = await fetch('http://localhost:8000/agent/compliance/monitor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(txnData)
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check compliance');
      console.error('Compliance check failed:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const getActionBadgeColor = (action: string) => {
    switch (action) {
      case 'approve': return 'bg-green-100 text-green-800 border-green-300';
      case 'block': return 'bg-red-100 text-red-800 border-red-300';
      case 'manual_review': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };
  
  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">🤖</span>
          <h2 className="text-2xl font-bold text-gray-900">
            AI Agent: Financial Compliance Monitor
          </h2>
        </div>
        <div className="flex gap-2 flex-wrap">
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 border border-blue-300">
            FINRA 4511
          </span>
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 border border-blue-300">
            SEC 17a-4
          </span>
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800 border border-purple-300">
            Isolation Forest ML
          </span>
        </div>
      </div>
      
      {/* Transaction Selector */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Select Test Transaction:
        </label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {testTransactions.map((txn) => (
            <button
              key={txn.id}
              onClick={() => setSelectedTxn(txn)}
              className={`p-3 rounded-lg border-2 transition-all text-left ${
                selectedTxn.id === txn.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              <div className="font-semibold text-sm">{txn.label}</div>
              <div className="text-xs text-gray-600 mt-1">
                {txn.counterparty}
              </div>
            </button>
          ))}
        </div>
      </div>
      
      {/* Transaction Details */}
      <div className="mb-6 bg-slate-50 p-4 rounded-lg border border-slate-200">
        <h3 className="font-semibold text-sm text-gray-700 mb-2">
          Transaction Details
        </h3>
        <pre className="text-xs text-gray-800 overflow-auto">
          {JSON.stringify(selectedTxn, null, 2)}
        </pre>
      </div>
      
      {/* Run Button */}
      <button
        onClick={runComplianceCheck}
        disabled={loading}
        className={`w-full py-3 px-6 rounded-lg font-semibold text-white transition-all ${
          loading
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800'
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
        <div className="mt-6 p-4 bg-red-50 border-l-4 border-red-500 rounded">
          <div className="flex items-center gap-2">
            <span className="text-red-600 font-semibold">❌ Error:</span>
            <span className="text-red-700">{error}</span>
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
            <span className="text-sm text-gray-600">
              Confidence: <span className="font-semibold">{result.confidence}%</span>
            </span>
          </div>
          
          {/* Reasoning */}
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
            <p className="text-sm font-semibold text-blue-900 mb-1">
              🧠 Agent Reasoning:
            </p>
            <p className="text-sm text-blue-800">{result.reasoning}</p>
          </div>
          
          {/* Alternatives */}
          {result.alternatives.length > 0 && (
            <div>
              <p className="text-sm font-semibold text-gray-700 mb-2">
                🔀 Alternative Actions Considered:
              </p>
              <div className="space-y-2">
                {result.alternatives.map((alt, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-50 p-3 rounded-lg border border-slate-200"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm text-gray-900">
                        {alt.action}
                      </span>
                      <span className="text-xs text-gray-500">
                        ({(alt.confidence * 100).toFixed(1)}% confidence)
                      </span>
                    </div>
                    <p className="text-xs text-gray-700">{alt.reasoning}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Audit Trail */}
          <div className="bg-gray-50 p-4 rounded-lg border-t-2 border-gray-300">
            <p className="text-xs font-semibold text-gray-600 mb-2">
              📋 Audit Trail
            </p>
            <div className="space-y-1 text-xs text-gray-700">
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
