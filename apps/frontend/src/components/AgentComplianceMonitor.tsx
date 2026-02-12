'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  Activity,
  RefreshCw,
  FlaskConical,
  Search,
  AlertTriangle,
  Brain,
  GitBranch,
  ClipboardList,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Eye,
  Loader2,
  Banknote,
  Building2,
  Landmark,
} from 'lucide-react';
import { cn } from '@/lib/utils';

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

const getActionIcon = (action: string) => {
  switch (action) {
    case 'approve': return <CheckCircle2 className="h-4 w-4" />;
    case 'block': return <XCircle className="h-4 w-4" />;
    case 'manual_review': return <Eye className="h-4 w-4" />;
    default: return <Shield className="h-4 w-4" />;
  }
};

const getActionVariant = (action: string) => {
  switch (action) {
    case 'approve': return 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10';
    case 'block': return 'text-red-500 border-red-500/30 bg-red-500/10';
    case 'manual_review': return 'text-amber-500 border-amber-500/30 bg-amber-500/10';
    default: return 'text-muted-foreground border-border bg-muted';
  }
};

const getTxnIcon = (type: string) => {
  switch (type) {
    case 'ach': return <Banknote className="h-4 w-4 text-emerald-500" />;
    case 'wire': return <Landmark className="h-4 w-4 text-blue-500" />;
    case 'internal': return <Building2 className="h-4 w-4 text-purple-500" />;
    default: return <Banknote className="h-4 w-4 text-muted-foreground" />;
  }
};

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

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Shield className="h-4 w-4" />
              AI Agent: Financial Compliance Monitor
            </CardTitle>
            <Button
              size="sm"
              variant="ghost"
              onClick={fetchMetrics}
              disabled={metricsLoading}
              className="text-muted-foreground hover:text-foreground"
            >
              <RefreshCw className={cn('h-3.5 w-3.5 mr-1.5', metricsLoading && 'animate-spin')} />
              {metricsLoading ? 'Refreshing' : 'Refresh'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 flex-wrap mb-5">
            <Badge variant="outline" className="text-xs text-blue-500 border-blue-500/30 bg-blue-500/10">
              FINRA 4511
            </Badge>
            <Badge variant="outline" className="text-xs text-blue-500 border-blue-500/30 bg-blue-500/10">
              SEC 17a-4
            </Badge>
            <Badge variant="outline" className="text-xs text-purple-500 border-purple-500/30 bg-purple-500/10">
              Isolation Forest ML v{metrics?.model?.version || '2.0.0'}
            </Badge>
          </div>

          {/* Performance Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 rounded-lg bg-muted border border-border">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-muted-foreground">Total Processed</span>
                <Activity className="h-3.5 w-3.5 text-muted-foreground" />
              </div>
              <div className="text-2xl font-bold tabular-nums">
                {metrics?.total_transactions ?? 0}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-muted border border-border">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-muted-foreground">Auto-Approved</span>
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
              </div>
              <div className="text-2xl font-bold text-emerald-500 tabular-nums">
                {metrics?.approval_rate ?? 0}%
              </div>
              <Progress value={metrics?.approval_rate ?? 0} className="h-1 mt-2 [&>div]:bg-emerald-500" />
            </div>
            <div className="p-3 rounded-lg bg-muted border border-border">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-muted-foreground">Blocked</span>
                <ShieldX className="h-3.5 w-3.5 text-red-500" />
              </div>
              <div className="text-2xl font-bold text-red-500 tabular-nums">
                {metrics?.block_rate ?? 0}%
              </div>
              <Progress value={metrics?.block_rate ?? 0} className="h-1 mt-2 [&>div]:bg-red-500" />
            </div>
            <div className="p-3 rounded-lg bg-muted border border-border">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-muted-foreground">Avg Confidence</span>
                <ShieldAlert className="h-3.5 w-3.5 text-blue-500" />
              </div>
              <div className="text-2xl font-bold text-blue-500 tabular-nums">
                {metrics?.avg_confidence ?? 0}%
              </div>
              <Progress value={metrics?.avg_confidence ?? 0} className="h-1 mt-2 [&>div]:bg-blue-500" />
            </div>
          </div>

          {metrics?.storage && (
            <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-muted-foreground" />
                Storage: {metrics.storage}
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-purple-500" />
                Model: {metrics?.model?.algorithm || 'IsolationForest'}
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Batch Testing */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <FlaskConical className="h-4 w-4" />
              Batch Testing
            </CardTitle>
            <Button
              size="sm"
              variant="outline"
              onClick={runTestBatch}
              disabled={testBatchLoading}
              className="text-amber-500 border-amber-500/30 hover:bg-amber-500/10"
            >
              <FlaskConical className={cn('h-3.5 w-3.5 mr-1.5', testBatchLoading && 'animate-spin')} />
              {testBatchLoading ? 'Running...' : 'Run Test Batch'}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Run 100 synthetic transactions to validate model performance
          </p>
        </CardHeader>
        {testBatchResult && (
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              <div className="p-3 rounded-lg bg-muted border border-border text-center">
                <div className="text-lg font-bold text-emerald-500 tabular-nums">{testBatchResult.approval_rate}%</div>
                <div className="text-xs text-muted-foreground mt-0.5">Approved</div>
              </div>
              <div className="p-3 rounded-lg bg-muted border border-border text-center">
                <div className="text-lg font-bold text-amber-500 tabular-nums">{testBatchResult.manual_review_rate}%</div>
                <div className="text-xs text-muted-foreground mt-0.5">Review</div>
              </div>
              <div className="p-3 rounded-lg bg-muted border border-border text-center">
                <div className="text-lg font-bold text-red-500 tabular-nums">{testBatchResult.block_rate}%</div>
                <div className="text-xs text-muted-foreground mt-0.5">Blocked</div>
              </div>
              <div className="p-3 rounded-lg bg-muted border border-border text-center">
                <div className="text-lg font-bold text-blue-500 tabular-nums">{testBatchResult.avg_confidence}%</div>
                <div className="text-xs text-muted-foreground mt-0.5">Confidence</div>
              </div>
            </div>

            {/* Batch Results Table */}
            {testBatchResult.transactions.length > 0 && (
              <div className="mt-4 rounded-lg border border-border overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead>ID</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead className="text-right">Anomaly</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead className="text-right">Confidence</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {testBatchResult.transactions.slice(0, 8).map((txn) => (
                      <TableRow key={txn.id}>
                        <TableCell className="font-mono text-xs">{txn.id.slice(0, 12)}</TableCell>
                        <TableCell className="text-right tabular-nums">${txn.amount.toLocaleString()}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs capitalize">{txn.type}</Badge>
                        </TableCell>
                        <TableCell className="text-right tabular-nums">{txn.anomaly_score.toFixed(3)}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className={cn('text-xs', getActionVariant(txn.action))}>
                            {getActionIcon(txn.action)}
                            <span className="ml-1">{txn.action.replace('_', ' ')}</span>
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right tabular-nums">{txn.confidence}%</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {testBatchResult.transactions.length > 8 && (
                  <div className="px-4 py-2 text-xs text-muted-foreground text-center border-t border-border bg-muted/50">
                    Showing 8 of {testBatchResult.transactions.length} transactions
                  </div>
                )}
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Transaction Selector */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Search className="h-4 w-4" />
            Test Transaction
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {testTransactions.map((txn) => (
              <button
                key={txn.id}
                onClick={() => setSelectedTxn(txn)}
                className={cn(
                  'p-4 rounded-lg border transition-all text-left group',
                  selectedTxn.id === txn.id
                    ? 'border-primary bg-primary/5 ring-1 ring-primary/20'
                    : 'border-border bg-muted hover:border-muted-foreground/30 hover:bg-muted/80'
                )}
              >
                <div className="flex items-center gap-2 mb-2">
                  {getTxnIcon(txn.type)}
                  <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{txn.type}</span>
                </div>
                <div className="font-semibold text-sm">{txn.label}</div>
                <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <Building2 className="h-3 w-3" />
                  {txn.counterparty}
                </div>
              </button>
            ))}
          </div>

          {/* Transaction Details */}
          <div className="rounded-lg border border-border overflow-hidden">
            <div className="px-4 py-2 bg-muted border-b border-border">
              <span className="text-xs font-medium text-muted-foreground">Transaction Payload</span>
            </div>
            <pre className="p-4 text-xs text-muted-foreground overflow-auto font-mono leading-relaxed">
              {JSON.stringify(selectedTxn, null, 2)}
            </pre>
          </div>

          {/* Run Button */}
          <Button
            onClick={runComplianceCheck}
            disabled={loading}
            className="w-full"
            size="lg"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Analyzing Transaction...
              </>
            ) : (
              <>
                <Search className="h-4 w-4 mr-2" />
                Run Compliance Check
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-red-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-full bg-red-500/10">
                <AlertTriangle className="h-4 w-4 text-red-500" />
              </div>
              <div>
                <p className="text-sm font-semibold text-red-500">Compliance Check Failed</p>
                <p className="text-xs text-red-400 mt-0.5">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Display */}
      {result && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <ShieldCheck className="h-4 w-4" />
                Compliance Result
              </CardTitle>
              <Badge
                variant="outline"
                className={cn('text-sm font-bold px-3 py-1', getActionVariant(result.action))}
              >
                {getActionIcon(result.action)}
                <span className="ml-1.5">{result.action.toUpperCase().replace('_', ' ')}</span>
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Confidence */}
            <div className="p-3 rounded-lg bg-muted border border-border">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-muted-foreground">Confidence Score</span>
                <span className="text-sm font-bold tabular-nums">{result.confidence}%</span>
              </div>
              <Progress
                value={result.confidence}
                className={cn(
                  'h-2',
                  result.confidence >= 80 ? '[&>div]:bg-emerald-500' :
                  result.confidence >= 50 ? '[&>div]:bg-amber-500' :
                  '[&>div]:bg-red-500'
                )}
              />
            </div>

            {/* Reasoning */}
            <div className="p-4 rounded-lg border border-primary/20 bg-primary/5">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="h-4 w-4 text-primary" />
                <span className="text-sm font-semibold">Agent Reasoning</span>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">{result.reasoning}</p>
            </div>

            {/* Alternatives */}
            {result.alternatives.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <GitBranch className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-semibold">Alternative Actions Considered</span>
                </div>
                <div className="space-y-2">
                  {result.alternatives.map((alt, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg bg-muted border border-border flex items-start gap-3"
                    >
                      <ArrowRight className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline" className={cn('text-xs', getActionVariant(alt.action))}>
                            {alt.action}
                          </Badge>
                          <span className="text-xs text-muted-foreground tabular-nums">
                            {(alt.confidence * 100).toFixed(1)}% confidence
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground">{alt.reasoning}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Audit Trail */}
            <div className="p-4 rounded-lg bg-muted border border-border">
              <div className="flex items-center gap-2 mb-3">
                <ClipboardList className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Audit Trail</span>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-xs text-muted-foreground mb-0.5">Regulation</div>
                  <div className="text-sm font-medium">{result.audit_trail.regulation}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-0.5">Agent</div>
                  <div className="text-sm font-medium">{result.audit_trail.agent}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-0.5">Timestamp</div>
                  <div className="text-sm font-medium">{new Date(result.audit_trail.timestamp).toLocaleString()}</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
