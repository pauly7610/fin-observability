'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Cpu,
  ExternalLink,
  Globe,
  RefreshCw,
  Server,
  Zap,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const GRAFANA_BASE = process.env.NEXT_PUBLIC_GRAFANA_URL || ''
const PUBLIC_DASHBOARD_TOKEN = process.env.NEXT_PUBLIC_GRAFANA_PUBLIC_DASHBOARD || ''

interface PanelConfig {
  id: number
  title: string
  icon: React.ReactNode
  description: string
  height: number
  span: 'full' | 'half'
}

const overviewPanels: PanelConfig[] = [
  { id: 1, title: 'Request Rate', icon: <Zap className="h-4 w-4" />, description: 'Requests per second across all endpoints', height: 200, span: 'half' },
  { id: 2, title: 'Error Rate (5xx)', icon: <AlertTriangle className="h-4 w-4" />, description: 'Server error percentage over 15m window', height: 200, span: 'half' },
  { id: 3, title: 'Anomalies Detected', icon: <Activity className="h-4 w-4" />, description: 'ML-detected anomalies in the last hour', height: 200, span: 'half' },
  { id: 4, title: 'Compliance Actions', icon: <BarChart3 className="h-4 w-4" />, description: 'Compliance decisions in the last hour', height: 200, span: 'half' },
]

const performancePanels: PanelConfig[] = [
  { id: 5, title: 'API Latency by Endpoint', icon: <Activity className="h-4 w-4" />, description: 'p50 and p95 latency across routes', height: 350, span: 'half' },
  { id: 6, title: 'Request Rate by Status Code', icon: <BarChart3 className="h-4 w-4" />, description: 'Traffic breakdown by HTTP status', height: 350, span: 'half' },
  { id: 7, title: 'Request Rate by Endpoint', icon: <Globe className="h-4 w-4" />, description: 'Per-route traffic volume', height: 350, span: 'half' },
  { id: 8, title: 'Business Metrics', icon: <Zap className="h-4 w-4" />, description: 'Anomalies, compliance actions, export jobs', height: 350, span: 'half' },
]

const infraPanels: PanelConfig[] = [
  { id: 9, title: 'Host CPU Load Average', icon: <Cpu className="h-4 w-4" />, description: '1m, 5m, 15m CPU load averages', height: 350, span: 'half' },
  { id: 10, title: 'Host Memory Usage', icon: <Server className="h-4 w-4" />, description: 'Used, free, and cached memory', height: 350, span: 'half' },
  { id: 11, title: 'Recent Traces', icon: <Activity className="h-4 w-4" />, description: 'Latest distributed traces from Tempo', height: 400, span: 'full' },
]

function GrafanaPanel({ panel, theme }: { panel: PanelConfig; theme: string }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  if (!GRAFANA_BASE || !PUBLIC_DASHBOARD_TOKEN) {
    return (
      <div
        className={cn(
          'rounded-lg border border-border bg-muted/50 flex flex-col items-center justify-center text-center p-6',
          panel.span === 'full' ? 'col-span-2' : ''
        )}
        style={{ height: panel.height }}
      >
        <Server className="h-8 w-8 text-muted-foreground/30 mb-3" />
        <p className="text-sm font-medium text-muted-foreground">{panel.title}</p>
        <p className="text-xs text-muted-foreground/60 mt-1">{panel.description}</p>
        <Badge variant="outline" className="mt-3 text-xs text-amber-500 border-amber-500/30 bg-amber-500/10">
          Configure Grafana env vars
        </Badge>
      </div>
    )
  }

  const panelUrl = `${GRAFANA_BASE}/public-dashboards/${PUBLIC_DASHBOARD_TOKEN}?panelId=${panel.id}&theme=${theme}&refresh=30s`

  return (
    <div
      className={cn(
        'rounded-lg border border-border overflow-hidden relative',
        panel.span === 'full' ? 'col-span-2' : ''
      )}
      style={{ height: panel.height }}
    >
      {loading && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted/80 z-10">
          <RefreshCw className="h-5 w-5 text-muted-foreground animate-spin" />
        </div>
      )}
      {error ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-muted/50 z-10">
          <AlertTriangle className="h-6 w-6 text-muted-foreground/40 mb-2" />
          <p className="text-xs text-muted-foreground">Failed to load panel</p>
        </div>
      ) : (
        <iframe
          src={panelUrl}
          width="100%"
          height="100%"
          frameBorder="0"
          className="bg-transparent"
          onLoad={() => setLoading(false)}
          onError={() => { setError(true); setLoading(false) }}
          allow="fullscreen"
        />
      )}
    </div>
  )
}

function PanelSection({
  title,
  icon,
  panels,
  theme,
}: {
  title: string
  icon: React.ReactNode
  panels: PanelConfig[]
  theme: string
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {panels.map((panel) => (
            <GrafanaPanel key={panel.id} panel={panel} theme={theme} />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export default function ObservabilityPage() {
  const [activeTab, setActiveTab] = useState('overview')
  const grafanaTheme = 'dark'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Observability</h1>
          <p className="text-sm text-muted-foreground">
            Live Grafana dashboards — API performance, ML metrics, and infrastructure health.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {GRAFANA_BASE && PUBLIC_DASHBOARD_TOKEN ? (
            <>
              <Badge variant="outline" className="text-xs text-emerald-500 border-emerald-500/30 bg-emerald-500/10">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
                Live
              </Badge>
              <Button
                size="sm"
                variant="outline"
                className="text-muted-foreground"
                asChild
              >
                <a
                  href={`${GRAFANA_BASE}/public-dashboards/${PUBLIC_DASHBOARD_TOKEN}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="h-3.5 w-3.5 mr-1.5" />
                  Open in Grafana
                </a>
              </Button>
            </>
          ) : (
            <Badge variant="outline" className="text-xs text-amber-500 border-amber-500/30 bg-amber-500/10">
              Grafana URL not configured
            </Badge>
          )}
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="performance">API Performance</TabsTrigger>
          <TabsTrigger value="infrastructure">Infrastructure</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-4">
          <PanelSection
            title="Platform Overview"
            icon={<BarChart3 className="h-4 w-4" />}
            panels={overviewPanels}
            theme={grafanaTheme}
          />
        </TabsContent>

        <TabsContent value="performance" className="mt-4">
          <PanelSection
            title="API Performance"
            icon={<Activity className="h-4 w-4" />}
            panels={performancePanels}
            theme={grafanaTheme}
          />
        </TabsContent>

        <TabsContent value="infrastructure" className="mt-4">
          <PanelSection
            title="Infrastructure & Traces"
            icon={<Server className="h-4 w-4" />}
            panels={infraPanels}
            theme={grafanaTheme}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}
