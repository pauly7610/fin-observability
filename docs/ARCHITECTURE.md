# Architecture Documentation for Financial AI Observability Monorepo

## Overview

The Financial AI Observability Platform is a monorepo combining a FastAPI backend (ML + agentic AI + MCP server), a Next.js frontend, and full OpenTelemetry instrumentation. It provides real-time anomaly detection, compliance automation, SHAP explainability, and external data ingestion — all traceable end-to-end via Grafana Cloud.

> **Live:** https://fin-observability-production.up.railway.app
> **Grafana:** https://pauly7610.grafana.net

---

## Monorepo Structure

```
fin-observability/
├── apps/
│   ├── backend/                  # FastAPI 0.111.0 + ML + MCP Server
│   │   ├── ml/                   # Anomaly detector, drift detector, retraining
│   │   ├── services/             # LLM-powered agent services
│   │   ├── routers/              # API endpoints (incl. webhooks — SSE, outbound, pull)
│   │   ├── mcp_server.py         # MCP server — 9 tools for AI agents
│   │   ├── telemetry.py          # OpenTelemetry setup (tracing + metrics)
│   │   ├── rbac.py               # Role-based access control (4 roles, 25 permissions)
│   │   └── tests/                # 122 tests
│   └── frontend/                 # Next.js 16 (App Router, React 19)
│       ├── app/                  # Pages: dashboard, compliance, incidents, explainability, connect, observability, agent
│       └── src/components/       # UI components (shadcn/ui + Recharts)
├── otel-collector/               # OTel Collector config + Dockerfile
├── grafana/dashboards/           # Importable 12-panel dashboard JSON
├── infra/                        # Pulumi IaC for Railway
├── docker-compose.yml            # Local dev: Postgres 16, Redis 7, OTel Collector, Backend
└── .github/workflows/            # CI: pytest + Jest + Next.js build
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Railway Cloud                               │
│                                                                      │
│  ┌──────────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │   FastAPI Backend │───▶│  PostgreSQL   │    │  OTel Collector  │   │
│  │                   │    │              │    │  (contrib 0.145) │   │
│  │  - ML Ensemble    │    └──────────────┘    │       │          │   │
│  │  - MCP Server     │                        │       ▼          │   │
│  │  - Webhook System │                        │  Grafana Cloud   │   │
│  │  - LLM Agents     │───────────────────────▶│  (Tempo + Prom)  │   │
│  │  - OTel SDK 1.39  │   direct OTLP/HTTP     └──────────────────┘   │
│  └──────────────────┘                                                │
│         │                                                            │
│  ┌──────────────┐                                                    │
│  │    Redis      │  (metrics cache)                                  │
│  └──────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────┘
         │
    ┌────▼─────┐
    │ Next.js  │  Dashboard (App Router, React 19)
    │ Frontend │  Pages: /, /compliance, /incidents, /explainability,
    └──────────┘         /connect, /observability, /agent
```

---

## Data Flow

### Transaction Scoring (all ingestion paths)

```
External Systems (Plaid, Stripe, bank feeds)
AI Agents (via MCP ingest_transactions)
Scheduled Pull (configured external APIs)
        │
        ▼
┌─────────────────────────────────────────┐
│  Ingestion Layer                         │
│  - POST /webhooks/transactions           │
│  - MCP ingest_transactions tool          │
│  - Scheduled pull job                    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  score_and_store_transaction()           │
│  - Isolation Forest + PCA-Autoencoder   │
│  - Decision: approve / manual_review    │
│  - Store in PostgreSQL                   │
│  - Publish to SSE EventBus              │
│  - POST to outbound callbacks if flagged│
│  - OTel span with all attributes        │
└──────────────┬──────────────────────────┘
               │
        ┌──────┼──────┐
        ▼      ▼      ▼
   Database  SSE    Outbound
   (stored)  Stream  Callbacks
             (live)  (if flagged,
                      3x retry + DLQ)
```

### Agentic Workflow

```
Incident → LLM Triage → Agent Recommendation → Human Approval → Audit Log
    │           │              │                     │              │
    └───────────┴──────────────┴─────────────────────┴──────────────┘
                              OpenTelemetry Traces → Grafana
```

---

## Key Components & Versions

### Frontend
- **Next.js:** 16.1.6 (App Router)
- **React:** 19
- **TailwindCSS** + **shadcn/ui** (components)
- **Recharts** (charts, SHAP waterfall)
- **TanStack Query** (data fetching)
- **Lucide** (icons)

### Backend
- **FastAPI:** 0.111.0
- **Python:** 3.12
- **SQLAlchemy:** 2.0 + Alembic
- **PostgreSQL:** 16 (production), SQLite (tests)
- **Redis:** 7 (metrics cache)
- **APScheduler:** 3.10.4 (background jobs)
- **httpx:** 0.27+ (async HTTP for outbound webhooks + pull ingestion)

### ML Pipeline
- **scikit-learn:** Isolation Forest
- **ONNX Runtime:** PCA-Autoencoder inference
- **SHAP:** TreeExplainer (per-prediction feature importance)
- **Drift detection:** PSI + KS tests (sliding window)
- **A/B testing:** Chi-squared significance, hash-based routing

### MCP Server
- **mcp:** 1.2+ (Model Context Protocol)
- 9 tools, input validation, OTel tracing, rate limiting (60/min)
- Mounted at `/mcp` (Streamable HTTP)

### Agentic AI
- **LangChain:** 0.3+ (core, openai, anthropic, google-genai)
- Pluggable LLM providers (OpenAI, Anthropic, Google Gemini)

### Observability
- **OpenTelemetry SDK:** 1.39.1 (Python)
- **OTel Collector:** contrib 0.145.0 (Railway)
- **Grafana Cloud:** Tempo (traces) + Prometheus (metrics)
- Direct OTLP/HTTP export (bypasses collector when Grafana creds set)

### Security
- **RBAC:** 4 roles (admin/compliance/analyst/viewer), 25 permissions
- **Webhook auth:** HMAC constant-time comparison
- **JWT:** python-jose + passlib + bcrypt
- **Export integrity:** Hash chain + digital signatures

---

## Design Decisions

- **Shared scoring pipeline** — `score_and_store_transaction()` is the single path for all ingestion (webhook, MCP, pull), ensuring consistent scoring and storage
- **SSE over WebSocket for streaming** — Simpler, HTTP-native, works through proxies, auto-reconnect built into EventSource API
- **Outbound retry + DLQ** — 3 attempts with exponential backoff; failed deliveries preserved in dead letter queue for inspection
- **MCP as primary AI integration** — Standardized protocol means any MCP-compatible agent (Windsurf, Claude, Cursor) connects without custom code
- **Drift-triggered retraining** — No blind cron; PSI + KS tests determine when the model actually needs retraining
- **Demo mode write guard** — Production deployment is read-only for unauthenticated users; webhook API key bypasses this

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `WEBHOOK_API_KEY` | Auth key for webhook endpoints |
| `WEBHOOK_CALLBACK_URLS` | Comma-separated outbound callback URLs |
| `PULL_INGESTION_SOURCES` | JSON array of pull ingestion source configs |
| `DRIFT_CHECK_HOURS` | Drift check interval (default: 6) |
| `PII_HASH_SALT` | Salt for deterministic PII hashing in audit trail |
| `PII_HASH_ENABLED` | Enable PII sanitization (default: true) |
| `AUDIT_RETENTION_YEARS` | Years to retain audit entries (default: 7, SEC 17a-4) |
| `GRAFANA_CLOUD_INSTANCE_ID` | Grafana Cloud instance ID |
| `GRAFANA_CLOUD_API_TOKEN` | Grafana Cloud API token |
| `OTEL_SERVICE_NAME` | OTel service name (default: fin-observability) |
| `JWT_SECRET_KEY` | JWT signing key |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) |

---

## References

- [README.md](../../README.md) — Quick start, demo walkthrough
- [apps/backend/API.md](../backend/API.md) — Full endpoint reference
- [apps/backend/ARCHITECTURE.md](../backend/ARCHITECTURE.md) — Backend-specific architecture
- [DESIGN.md](./DESIGN.md) — UI design vision
- [PRD.md](./PRD.md) — Product requirements and business case
