'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  Check,
  ChevronRight,
  Circle,
  ClipboardCopy,
  Code2,
  ExternalLink,
  Loader2,
  Plug,
  Play,
  Shield,
  Terminal,
  Zap,
  MessageSquare,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import apiClient from '@/lib/api-client'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const MCP_ENDPOINT = `${API_URL}/mcp`

// MCP config templates for different clients
const mcpConfigs: Record<string, { label: string; config: string }> = {
  windsurf: {
    label: 'Windsurf / Cascade',
    config: JSON.stringify({
      mcpServers: {
        'fin-observability': {
          url: `${API_URL}/mcp`,
          transport: 'streamable-http',
        },
      },
    }, null, 2),
  },
  claude: {
    label: 'Claude Desktop',
    config: JSON.stringify({
      mcpServers: {
        'fin-observability': {
          url: `${API_URL}/mcp`,
          transport: 'streamable-http',
        },
      },
    }, null, 2),
  },
  cursor: {
    label: 'Cursor',
    config: JSON.stringify({
      mcpServers: {
        'fin-observability': {
          url: `${API_URL}/mcp`,
          transport: 'streamable-http',
        },
      },
    }, null, 2),
  },
}

interface MCPTool {
  name: string
  description: string
  parameters: Record<string, unknown>
}

interface MCPToolsResponse {
  endpoint: string
  transport: string
  tool_count: number
  tools: MCPTool[]
}

interface MCPStats {
  total_calls: number
  tools: Record<string, number>
  avg_latency_ms: number
  errors: number
  recent: Array<{
    tool: string
    timestamp: string
    latency_ms: number
    decision: string
    error: string
  }>
}

interface KafkaStatus {
  enabled: boolean
  brokers: string
  topics: string[]
  stuck_order_threshold_minutes: number
}

export default function ConnectPage() {
  const [tools, setTools] = useState<MCPTool[]>([])
  const [stats, setStats] = useState<MCPStats | null>(null)
  const [isOnline, setIsOnline] = useState<boolean | null>(null)
  const [copied, setCopied] = useState<string | null>(null)
  const [selectedClient, setSelectedClient] = useState('windsurf')
  const [expandedTool, setExpandedTool] = useState<string | null>(null)

  // Try-it-live state
  const [tryAmount, setTryAmount] = useState('25000')
  const [tryType, setTryType] = useState('wire_transfer')
  const [tryResult, setTryResult] = useState<Record<string, unknown> | null>(null)
  const [tryLoading, setTryLoading] = useState(false)
  const [kafkaStatus, setKafkaStatus] = useState<KafkaStatus | null>(null)

  // Fetch tools and stats
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [toolsRes, statsRes, kafkaRes] = await Promise.all([
          apiClient.get<MCPToolsResponse>('/mcp/tools'),
          apiClient.get<MCPStats>('/mcp/stats'),
          apiClient.get<KafkaStatus>('/api/kafka/status').catch(() => ({ data: null })),
        ])
        setTools(toolsRes.data.tools || [])
        setStats(statsRes.data)
        setIsOnline(true)
        setKafkaStatus(kafkaRes.data)
      } catch {
        setIsOnline(false)
      }
    }
    fetchData()
    const interval = setInterval(fetchData, 15000)
    return () => clearInterval(interval)
  }, [])

  const copyConfig = (client: string) => {
    navigator.clipboard.writeText(mcpConfigs[client].config)
    setCopied(client)
    setTimeout(() => setCopied(null), 2000)
  }

  const runTryIt = async () => {
    setTryLoading(true)
    setTryResult(null)
    try {
      const res = await apiClient.post('/api/compliance/check', {
        transaction_id: `try-${Date.now()}`,
        amount: parseFloat(tryAmount),
        transaction_type: tryType,
        timestamp: new Date().toISOString(),
      })
      setTryResult(res.data)
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      setTryResult({ error: error.response?.data?.detail || 'Request failed' })
    } finally {
      setTryLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
            <Plug className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Connect Your AI Agent</h1>
            <p className="text-sm text-muted-foreground">
              Plug any MCP-compatible AI into real-time compliance monitoring, anomaly detection, and SHAP explainability.
            </p>
          </div>
        </div>
      </div>

      {/* Status + Endpoint */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className={cn(
                'flex items-center justify-center w-8 h-8 rounded-full',
                isOnline === true ? 'bg-emerald-500/10' : isOnline === false ? 'bg-red-500/10' : 'bg-muted',
              )}>
                <Circle className={cn(
                  'h-3 w-3',
                  isOnline === true ? 'fill-emerald-500 text-emerald-500' : isOnline === false ? 'fill-red-500 text-red-500' : 'fill-muted-foreground text-muted-foreground',
                )} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">
                  {isOnline === true ? 'MCP Server Online' : isOnline === false ? 'MCP Server Offline' : 'Checking...'}
                </p>
                <code className="text-xs text-muted-foreground font-mono truncate block">{MCP_ENDPOINT}</code>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">Streamable HTTP</Badge>
              {stats && stats.total_calls > 0 && (
                <Badge variant="outline" className="text-xs text-emerald-500 border-emerald-500/30 bg-emerald-500/10">
                  {stats.total_calls} calls
                </Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Connect */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold tracking-tight">Quick Connect</h2>
        <p className="text-sm text-muted-foreground">
          Copy the config below into your MCP client settings. Works with any client that supports Streamable HTTP transport.
        </p>
        <p className="text-xs text-muted-foreground">
          If <code className="bg-muted px-1 rounded">MCP_API_KEY</code> is set on the server, include it as <code className="bg-muted px-1 rounded">X-MCP-API-Key</code> header or <code className="bg-muted px-1 rounded">Authorization: Bearer &lt;key&gt;</code> in your client config.
        </p>

        <Tabs value={selectedClient} onValueChange={setSelectedClient}>
          <TabsList>
            {Object.entries(mcpConfigs).map(([key, { label }]) => (
              <TabsTrigger key={key} value={key} className="text-xs">{label}</TabsTrigger>
            ))}
          </TabsList>

          {Object.entries(mcpConfigs).map(([key, { config }]) => (
            <TabsContent key={key} value={key}>
              <Card>
                <CardContent className="pt-4 pb-4">
                  <div className="relative">
                    <pre className="bg-muted/50 rounded-lg p-4 text-xs font-mono overflow-x-auto border border-border">
                      {config}
                    </pre>
                    <Button
                      size="sm"
                      variant="outline"
                      className="absolute top-2 right-2"
                      onClick={() => copyConfig(key)}
                    >
                      {copied === key ? (
                        <><Check className="h-3.5 w-3.5 mr-1.5 text-emerald-500" /> Copied</>
                      ) : (
                        <><ClipboardCopy className="h-3.5 w-3.5 mr-1.5" /> Copy</>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>
      </div>

      {/* Tool Catalog + Try It Live side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Tool Catalog */}
        <div className="lg:col-span-3 space-y-3">
          <h2 className="text-lg font-semibold tracking-tight">Tool Catalog</h2>
          <p className="text-sm text-muted-foreground">
            {tools.length} tools available. Click to expand parameters.
          </p>
          <div className="space-y-2">
            {tools.map((tool) => (
              <Card
                key={tool.name}
                className={cn(
                  'cursor-pointer transition-colors hover:border-primary/30',
                  expandedTool === tool.name && 'border-primary/40 bg-primary/[0.02]',
                )}
                onClick={() => setExpandedTool(expandedTool === tool.name ? null : tool.name)}
              >
                <CardContent className="py-3 px-4">
                  <div className="flex items-start gap-3">
                    <div className="flex items-center justify-center w-7 h-7 rounded-md bg-primary/10 mt-0.5 shrink-0">
                      <Code2 className="h-3.5 w-3.5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <code className="text-sm font-semibold font-mono">{tool.name}</code>
                        <ChevronRight className={cn(
                          'h-3.5 w-3.5 text-muted-foreground transition-transform',
                          expandedTool === tool.name && 'rotate-90',
                        )} />
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                        {tool.description?.split('\n')[0]}
                      </p>

                      {expandedTool === tool.name && (
                        <div className="mt-3 space-y-2">
                          {tool.description && (
                            <pre className="text-xs text-muted-foreground whitespace-pre-wrap bg-muted/50 rounded-md p-3 border border-border">
                              {tool.description}
                            </pre>
                          )}
                          {tool.parameters && Object.keys(tool.parameters).length > 0 && (
                            <div>
                              <p className="text-xs font-medium mb-1">Parameters:</p>
                              <pre className="text-xs font-mono bg-muted/50 rounded-md p-3 border border-border overflow-x-auto">
                                {JSON.stringify(tool.parameters, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {tools.length === 0 && (
              <Card>
                <CardContent className="py-8 text-center">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">Loading tools...</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Try It Live */}
        <div className="lg:col-span-2 space-y-3">
          <h2 className="text-lg font-semibold tracking-tight">Try It Live</h2>
          <p className="text-sm text-muted-foreground">
            This is what your agent gets when it calls <code className="text-xs bg-muted px-1 py-0.5 rounded">check_transaction_compliance</code>.
          </p>

          <Card>
            <CardContent className="pt-4 space-y-3">
              <div className="space-y-2">
                <label className="text-xs font-medium">Amount (USD)</label>
                <Input
                  type="number"
                  value={tryAmount}
                  onChange={(e) => setTryAmount(e.target.value)}
                  placeholder="25000"
                  className="font-mono text-sm"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-medium">Transaction Type</label>
                <select
                  value={tryType}
                  onChange={(e) => setTryType(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="wire_transfer">Wire Transfer</option>
                  <option value="ach">ACH</option>
                  <option value="trade">Trade</option>
                  <option value="internal">Internal</option>
                  <option value="card">Card</option>
                  <option value="crypto">Crypto</option>
                </select>
              </div>
              <Button
                className="w-full"
                onClick={runTryIt}
                disabled={tryLoading || !tryAmount}
              >
                {tryLoading ? (
                  <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Running...</>
                ) : (
                  <><Play className="h-4 w-4 mr-2" /> Run Compliance Check</>
                )}
              </Button>

              {tryResult && (
                <div className="mt-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Terminal className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="text-xs font-medium">Response</span>
                    {Boolean(tryResult.decision ?? tryResult.action) && (
                      <Badge
                        variant="outline"
                        className={cn(
                          'text-xs',
                          (tryResult.decision ?? tryResult.action) === 'approve'
                            ? 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10'
                            : (tryResult.decision ?? tryResult.action) === 'manual_review'
                            ? 'text-amber-500 border-amber-500/30 bg-amber-500/10'
                            : 'text-red-500 border-red-500/30 bg-red-500/10',
                        )}
                      >
                        {String(tryResult.decision ?? tryResult.action)}
                      </Badge>
                    )}
                  </div>
                  <pre className="bg-muted/50 rounded-lg p-3 text-xs font-mono overflow-x-auto border border-border max-h-80 overflow-y-auto">
                    {JSON.stringify(tryResult, null, 2)}
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Usage Stats */}
          {stats && stats.total_calls > 0 && (
            <Card>
              <CardHeader className="pb-2 pt-4 px-4">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Zap className="h-4 w-4 text-primary" />
                  MCP Usage
                </CardTitle>
              </CardHeader>
              <CardContent className="px-4 pb-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-2 rounded-md bg-muted/50">
                    <p className="text-lg font-bold">{stats.total_calls}</p>
                    <p className="text-xs text-muted-foreground">Total Calls</p>
                  </div>
                  <div className="text-center p-2 rounded-md bg-muted/50">
                    <p className="text-lg font-bold">{stats.avg_latency_ms}ms</p>
                    <p className="text-xs text-muted-foreground">Avg Latency</p>
                  </div>
                </div>
                {Object.keys(stats.tools).length > 0 && (
                  <div className="mt-3 space-y-1">
                    <p className="text-xs font-medium">By Tool</p>
                    {Object.entries(stats.tools)
                      .sort(([, a], [, b]) => b - a)
                      .map(([tool, count]) => (
                        <div key={tool} className="flex items-center justify-between text-xs">
                          <code className="font-mono text-muted-foreground">{tool}</code>
                          <span className="font-medium">{count}</span>
                        </div>
                      ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Kafka Event Ingestion */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold tracking-tight flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-primary" />
          Kafka Event Ingestion
        </h2>
        <p className="text-sm text-muted-foreground">
          When <code className="bg-muted px-1 rounded">KAFKA_BROKERS</code> is set, the platform consumes trading events (orders, executions, trades) and auto-creates incidents for stuck orders, missed trades, and volume spikes.
        </p>
        <Card>
          <CardContent className="pt-4 space-y-4">
            <div className="flex items-center gap-3">
              <div className={cn(
                'flex items-center justify-center w-8 h-8 rounded-full',
                kafkaStatus?.enabled ? 'bg-emerald-500/10' : 'bg-muted',
              )}>
                <Circle className={cn(
                  'h-3 w-3',
                  kafkaStatus?.enabled ? 'fill-emerald-500 text-emerald-500' : 'fill-muted-foreground text-muted-foreground',
                )} />
              </div>
              <div>
                <p className="text-sm font-medium">
                  {kafkaStatus?.enabled ? 'Kafka consumer running' : 'Kafka not configured'}
                </p>
                <code className="text-xs text-muted-foreground font-mono">
                  {kafkaStatus?.brokers || '(not configured)'}
                </code>
              </div>
            </div>
            {kafkaStatus && (
              <div className="space-y-2">
                <p className="text-xs font-medium">Topics</p>
                <code className="text-xs font-mono bg-muted/50 px-2 py-1 rounded border border-border">
                  {kafkaStatus.topics?.join(', ') || 'orders, executions, trades'}
                </code>
                <p className="text-xs text-muted-foreground">
                  Stuck order threshold: {kafkaStatus.stuck_order_threshold_minutes} minutes
                </p>
              </div>
            )}
            <div>
              <p className="text-xs font-medium mb-1.5">Environment</p>
              <pre className="bg-muted/50 rounded-lg p-3 text-xs font-mono overflow-x-auto border border-border">{`KAFKA_BROKERS=localhost:9092
KAFKA_TOPICS=orders,executions,trades
STUCK_ORDER_THRESHOLD_MINUTES=5`}</pre>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Webhook Ingestion */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold tracking-tight">Webhook Ingestion</h2>
        <p className="text-sm text-muted-foreground">
          Push transactions from external systems (Plaid, Stripe, bank feeds) via HTTP POST. Each transaction is scored and stored automatically.
        </p>
        <Card>
          <CardContent className="pt-4 space-y-4">
            <div>
              <p className="text-xs font-medium mb-1.5">Endpoint</p>
              <code className="text-xs font-mono bg-muted/50 px-3 py-1.5 rounded-md border border-border block">
                POST {API_URL}/webhooks/transactions
              </code>
            </div>
            <div>
              <p className="text-xs font-medium mb-1.5">Authentication</p>
              <p className="text-xs text-muted-foreground">
                Set <code className="bg-muted px-1 rounded">WEBHOOK_API_KEY</code> env var on Railway, then pass it as <code className="bg-muted px-1 rounded">X-Webhook-Key</code> header.
              </p>
            </div>
            <div>
              <p className="text-xs font-medium mb-1.5">Example: Single Transaction</p>
              <pre className="bg-muted/50 rounded-lg p-3 text-xs font-mono overflow-x-auto border border-border">{`curl -X POST ${API_URL}/webhooks/transactions \\
  -H "Content-Type: application/json" \\
  -H "X-Webhook-Key: YOUR_KEY" \\
  -d '{"amount": 25000, "type": "wire_transfer", "transaction_id": "TXN-001"}'`}</pre>
            </div>
            <div>
              <p className="text-xs font-medium mb-1.5">Example: Batch (up to 10,000)</p>
              <pre className="bg-muted/50 rounded-lg p-3 text-xs font-mono overflow-x-auto border border-border">{`curl -X POST ${API_URL}/webhooks/transactions \\
  -H "Content-Type: application/json" \\
  -H "X-Webhook-Key: YOUR_KEY" \\
  -d '[{"amount": 5000, "type": "ach"}, {"amount": 150000, "type": "wire"}]'`}</pre>
            </div>
            <div>
              <p className="text-xs font-medium mb-1.5">Retrieve Results</p>
              <code className="text-xs font-mono bg-muted/50 px-3 py-1.5 rounded-md border border-border block">
                GET {API_URL}/webhooks/results?flagged_only=true
              </code>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Real-Time SSE Stream */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold tracking-tight">Real-Time Stream (SSE)</h2>
        <p className="text-sm text-muted-foreground">
          Subscribe to a Server-Sent Events feed for live compliance decisions. Every scored transaction is broadcast in real-time — replays the last 50 events on connect.
        </p>
        <Card>
          <CardContent className="pt-4 space-y-4">
            <div>
              <p className="text-xs font-medium mb-1.5">Endpoint</p>
              <code className="text-xs font-mono bg-muted/50 px-3 py-1.5 rounded-md border border-border block">
                GET {API_URL}/webhooks/stream
              </code>
            </div>
            <div>
              <p className="text-xs font-medium mb-1.5">Browser (EventSource)</p>
              <pre className="bg-muted/50 rounded-lg p-3 text-xs font-mono overflow-x-auto border border-border">{`const es = new EventSource('${API_URL}/webhooks/stream');
es.onmessage = (e) => {
  const decision = JSON.parse(e.data);
  console.log(decision.transaction_id, decision.decision, decision.anomaly_score);
};`}</pre>
            </div>
            <div>
              <p className="text-xs font-medium mb-1.5">curl</p>
              <pre className="bg-muted/50 rounded-lg p-3 text-xs font-mono overflow-x-auto border border-border">{`curl -N ${API_URL}/webhooks/stream`}</pre>
            </div>
            <div>
              <p className="text-xs font-medium mb-1.5">Stream Status</p>
              <code className="text-xs font-mono bg-muted/50 px-3 py-1.5 rounded-md border border-border block">
                GET {API_URL}/webhooks/stream/status
              </code>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Outbound Webhook Notifications */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold tracking-tight">Outbound Notifications</h2>
        <p className="text-sm text-muted-foreground">
          Register callback URLs to receive POST notifications when transactions are flagged. Includes automatic retry (3 attempts, exponential backoff) and a dead letter queue for failed deliveries.
        </p>
        <Card>
          <CardContent className="pt-4 space-y-4">
            <div>
              <p className="text-xs font-medium mb-1.5">Register a Callback</p>
              <pre className="bg-muted/50 rounded-lg p-3 text-xs font-mono overflow-x-auto border border-border">{`curl -X POST ${API_URL}/webhooks/callbacks \\
  -H "Content-Type: application/json" \\
  -H "X-Webhook-Key: YOUR_KEY" \\
  -d '{"url": "https://your-service.com/webhook"}'`}</pre>
            </div>
            <div>
              <p className="text-xs font-medium mb-1.5">Payload Format</p>
              <pre className="bg-muted/50 rounded-lg p-3 text-xs font-mono overflow-x-auto border border-border">{`{
  "event": "transaction.flagged",
  "timestamp": "2025-02-11T23:45:00",
  "data": {
    "transaction_id": "TXN-001",
    "decision": "manual_review",
    "anomaly_score": 0.82,
    "risk_factors": ["high_amount", "off_hours"]
  }
}`}</pre>
            </div>
            <div>
              <p className="text-xs font-medium mb-1.5">Management</p>
              <div className="space-y-1">
                <code className="text-xs font-mono bg-muted/50 px-3 py-1.5 rounded-md border border-border block">
                  GET {API_URL}/webhooks/callbacks — list callbacks + delivery log
                </code>
                <code className="text-xs font-mono bg-muted/50 px-3 py-1.5 rounded-md border border-border block">
                  GET {API_URL}/webhooks/callbacks/dlq — dead letter queue
                </code>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Scheduled Pull Ingestion */}
      <div className="space-y-3">
        <h2 className="text-lg font-semibold tracking-tight">Scheduled Pull Ingestion</h2>
        <p className="text-sm text-muted-foreground">
          Configure external API sources and the platform will periodically pull transactions, score them, and store results automatically.
        </p>
        <Card>
          <CardContent className="pt-4 space-y-4">
            <div>
              <p className="text-xs font-medium mb-1.5">Add a Source</p>
              <pre className="bg-muted/50 rounded-lg p-3 text-xs font-mono overflow-x-auto border border-border">{`curl -X POST ${API_URL}/webhooks/pull/sources \\
  -H "Content-Type: application/json" \\
  -H "X-Webhook-Key: YOUR_KEY" \\
  -d '{
    "name": "plaid-transactions",
    "url": "https://api.example.com/transactions",
    "headers": {"Authorization": "Bearer xxx"},
    "interval_seconds": 300,
    "enabled": true
  }'`}</pre>
            </div>
            <div>
              <p className="text-xs font-medium mb-1.5">Management</p>
              <div className="space-y-1">
                <code className="text-xs font-mono bg-muted/50 px-3 py-1.5 rounded-md border border-border block">
                  GET {API_URL}/webhooks/pull/sources — list sources + recent results
                </code>
                <code className="text-xs font-mono bg-muted/50 px-3 py-1.5 rounded-md border border-border block">
                  POST {API_URL}/webhooks/pull/trigger/&#123;id&#125; — manual trigger
                </code>
                <code className="text-xs font-mono bg-muted/50 px-3 py-1.5 rounded-md border border-border block">
                  DELETE {API_URL}/webhooks/pull/sources/&#123;id&#125; — remove source
                </code>
              </div>
            </div>
            <div>
              <p className="text-xs font-medium mb-1.5">System Status</p>
              <code className="text-xs font-mono bg-muted/50 px-3 py-1.5 rounded-md border border-border block">
                GET {API_URL}/webhooks/status — full system overview
              </code>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* How It Works */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">How It Works</CardTitle>
          <CardDescription>
            Your AI agent connects via the Model Context Protocol and gets structured compliance decisions.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 shrink-0">
                <span className="text-sm font-bold text-primary">1</span>
              </div>
              <div>
                <p className="text-sm font-medium">Connect</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Add the MCP config to your AI client. Your agent discovers available tools automatically.
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 shrink-0">
                <span className="text-sm font-bold text-primary">2</span>
              </div>
              <div>
                <p className="text-sm font-medium">Call Tools</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Your agent calls <code className="text-xs bg-muted px-1 rounded">check_transaction_compliance</code> or <code className="text-xs bg-muted px-1 rounded">analyze_portfolio</code> with real data.
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 shrink-0">
                <span className="text-sm font-bold text-primary">3</span>
              </div>
              <div>
                <p className="text-sm font-medium">Get Decisions</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Structured JSON with approve/review decisions, SHAP explanations, risk factors, and audit trail. Every call traced in Grafana.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
