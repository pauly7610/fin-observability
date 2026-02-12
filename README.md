# Financial AI Observability Platform

[![CI](https://github.com/pauly7610/fin-observability/actions/workflows/ci.yml/badge.svg)](https://github.com/pauly7610/fin-observability/actions/workflows/ci.yml)
[![Deploy](https://img.shields.io/badge/Railway-deployed-blueviolet?logo=railway)](https://fin-observability-production.up.railway.app)
[![Grafana](https://img.shields.io/badge/Grafana-dashboard-F46800?logo=grafana)](https://pauly7610.grafana.net)
[![Backend Tests](https://img.shields.io/badge/backend%20tests-122-brightgreen?logo=pytest)](https://github.com/pauly7610/fin-observability/actions/workflows/ci.yml)
[![Frontend Tests](https://img.shields.io/badge/frontend%20tests-35-brightgreen?logo=jest)](https://github.com/pauly7610/fin-observability/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js)](https://nextjs.org/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-1.39-7B61FF?logo=opentelemetry)](https://opentelemetry.io/)

> **Live:** [fin-observability-production.up.railway.app](https://fin-observability-production.up.railway.app)

---

## The Problem

AI models in financial services make high-stakes decisions — flagging fraud, blocking transactions, escalating compliance issues. But once deployed, most teams have no visibility into _why_ the model made a decision, _whether_ it's still performing correctly, or _what happened_ when a human overrode it.

This platform answers three questions that regulated AI teams struggle with:

1. **"Why did the model flag this?"** — SHAP-based explainability for every prediction, traceable end-to-end via OpenTelemetry
2. **"Is the model still working?"** — Automated drift detection (PSI + KS tests) with self-triggered retraining
3. **"Who approved what, and when?"** — Full audit trail from model inference → agent recommendation → human decision, with role-based access control

---

## MCP Server — Connect Claude or Cursor Directly

Connect any AI agent (Claude Desktop, Cursor, Windsurf, etc.) to the platform's compliance engine via the [Model Context Protocol](https://modelcontextprotocol.io):

```
Endpoint: https://fin-observability-production.up.railway.app/mcp
Transport: Streamable HTTP
```

**Add to your MCP config:**

```json
{
  "mcpServers": {
    "fin-observability": {
      "url": "https://fin-observability-production.up.railway.app/mcp",
      "transport": "streamable-http"
    }
  }
}
```

**Available tools:**

| Tool                           | Description                                                                                         |
| ------------------------------ | --------------------------------------------------------------------------------------------------- |
| `check_transaction_compliance` | Score a transaction — returns approve/review decision, anomaly score, risk factors, FINRA reference |
| `explain_transaction`          | SHAP-based feature importance showing WHY the model flagged or approved                             |
| `batch_check_compliance`       | Score up to 10,000 transactions in one call — ideal for ledger scanning                             |
| `analyze_portfolio`            | Aggregate risk assessment: risk distribution, top flagged items, concentration warnings (up to 10K) |
| `ingest_transactions`          | Push up to 10,000 transactions for scoring + storage — MCP equivalent of the webhook endpoint       |
| `get_compliance_metrics`       | Real-time approval rates, confidence scores, model info                                             |
| `list_incidents`               | Browse incidents with status/severity filters                                                       |
| `get_drift_status`             | PSI + KS test results and retrain recommendations                                                   |
| `get_model_leaderboard`        | Model versions ranked by F1 score                                                                   |

---

## Grafana Dashboard

View live traces, metrics, and infrastructure health:

- **[Live Dashboard →](https://pauly7610.grafana.net)**

Pre-built 12-panel dashboard covering API performance, error rates, infrastructure, and live traces. Import the JSON from `grafana/dashboards/fin-observability.json` for self-hosted Grafana.

---

## How It Works

```
Transaction comes in
        │
        ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  ML Ensemble     │────▶│  LLM Agent        │────▶│  Human Review    │
│  (IF + Autoenc.) │     │  (triage/action)  │     │  (approve/deny)  │
│                  │     │                   │     │                  │
│  anomaly score   │     │  recommendation   │     │  final decision  │
│  + SHAP explain  │     │  + reasoning      │     │  + audit log     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   OpenTelemetry Traces   │
                    │   → Grafana Cloud        │
                    │   (every step, linked)   │
                    └─────────────────────────┘
```

Every step in this chain — from the raw prediction to the human override — is instrumented with OpenTelemetry and visible in Grafana. You can trace a single transaction from model inference through agent reasoning to final human decision.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Railway Cloud                            │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   FastAPI     │───▶│  PostgreSQL   │    │  OTel Collector  │  │
│  │   Backend     │    │  (50K txns)   │    │  (contrib 0.145) │  │
│  │              │───▶│              │    │       │          │  │
│  │  - ML Models  │    └──────────────┘    │       ▼          │  │
│  │  - LLM Agents │                        │  Grafana Cloud   │  │
│  │  - OTel SDK   │───────────────────────▶│  (Tempo/Prom)    │  │
│  └──────────────┘   direct OTLP/HTTP      └──────────────────┘  │
│         │                                                       │
│  ┌──────────────┐                                               │
│  │    Redis      │  (metrics cache)                             │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
         │
    ┌────▼─────┐
    │ Next.js  │  Dashboard (App Router, React 19)
    │ Frontend │
    └──────────┘
```

## Key Capabilities

### ML Pipeline

- **Ensemble detection** — Isolation Forest + PCA-Autoencoder (ONNX Runtime), scoring every transaction
- **Explainability** — SHAP TreeExplainer generates per-prediction feature importance, surfaced as waterfall charts
- **Drift detection** — Population Stability Index + Kolmogorov-Smirnov tests on a sliding window; retraining auto-triggers when thresholds are exceeded
- **A/B testing** — Chi-squared significance testing for model variants with hash-based traffic routing

### Agentic AI (Human-in-the-Loop)

- **LLM-powered agents** — LangChain with pluggable providers (OpenAI, Anthropic, Google Gemini) for compliance monitoring, incident triage, remediation, and audit summarization
- **Approval workflows** — Multi-step chains with role-gated approvals, escalation policies, and simulation mode
- **Full attribution** — Every agent action records its input, output, reasoning, model version, and actor type

### Observability

- **Distributed tracing** — OpenTelemetry SDK instruments every request, DB query, and ML inference; traces flow to Grafana Tempo
- **Custom metrics** — Request rate, latency histograms, anomaly counts, compliance actions → Grafana Prometheus
- **12-panel dashboard** — Pre-built Grafana dashboard covering API performance, error rates, infrastructure, and live traces

### Access Control & Compliance

- **Authentication** — Clerk for sign-in, sign-up, and session management
- **RBAC** — Four roles (admin/compliance/analyst/viewer) with 25 fine-grained permissions
- **Audit trail** — Every action, override, and escalation is logged with timestamps and actor identity
- **Regulatory alignment** — SEC 17a-4 / FINRA 4511 rule engine

### Webhook & Streaming System

Four ways to get data in and results out — all feeding the same ML scoring pipeline:

| Channel                    | Endpoint                      | Description                                                                                |
| -------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------ |
| **Inbound Webhook**        | `POST /webhooks/transactions` | Push up to 10,000 transactions per request (Plaid, Stripe, bank feeds)                     |
| **SSE Stream**             | `GET /webhooks/stream`        | Real-time Server-Sent Events feed of every compliance decision                             |
| **Outbound Notifications** | `POST /webhooks/callbacks`    | Register callback URLs — flagged transactions are POSTed with 3x retry + dead letter queue |
| **Scheduled Pull**         | `POST /webhooks/pull/sources` | Configure external APIs to poll on a schedule — auto-scores and stores                     |
| **System Status**          | `GET /webhooks/status`        | Full overview: SSE subscribers, callback count, DLQ size, pull sources                     |

Authentication: `X-Webhook-Key` header or `?key=` query param (set `WEBHOOK_API_KEY` env var).

## Quick Start

```bash
# Backend
python -m venv venv && source venv/bin/activate
pip install -r apps/backend/requirements.txt
uvicorn apps.backend.main:app --reload

# Frontend
pnpm install && pnpm run dev

# Full stack (Docker)
docker compose up -d
```

### Clerk Authentication

Sign-in and sign-up use [Clerk](https://clerk.com). Set these env vars for the frontend:

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

Get keys at [dashboard.clerk.com](https://dashboard.clerk.com). For local dev, Clerk's keyless mode works when keys are unset.

### Run Tests

```bash
# Backend (122 tests)
DATABASE_URL=sqlite:///./test.db pytest apps/backend/tests/ -v

# Frontend (35 tests)
pnpm run test --filter=@fin-ai-observability/frontend
```

## Demo Walkthrough

Here's the story this platform tells in 2 minutes:

1. **A transaction arrives** → `POST /agent/compliance/monitor` with amount, type, timestamp
2. **The ML ensemble scores it** → Isolation Forest + Autoencoder produce an anomaly score
3. **SHAP explains why** → `POST /agent/compliance/explain` returns feature importance (amount was 4.2σ above mean, timestamp was off-hours)
4. **The LLM agent recommends an action** → "Flag for manual review" with reasoning: "High amount + unusual timing pattern matches historical fraud profile"
5. **A compliance officer reviews** → Approves or overrides via the dashboard, with notes logged
6. **Everything is traceable** → Open Grafana, search by transaction ID, see the full chain: model inference → agent reasoning → human decision, with latency at every step

## Project Structure

```
fin-observability/
├── apps/
│   ├── backend/                  # FastAPI + ML + Agents
│   │   ├── ml/                   # Anomaly detector, drift detector, retraining
│   │   ├── services/             # LLM-powered agent services
│   │   ├── routers/              # API endpoints (incl. webhooks.py — SSE, outbound, pull)
│   │   ├── mcp_server.py         # MCP server — 9 tools for AI agents
│   │   ├── telemetry.py          # OpenTelemetry setup (tracing + metrics)
│   │   ├── rbac.py               # Role-based access control
│   │   └── tests/                # 122 tests (webhooks, RBAC, drift, telemetry, integration)
│   └── frontend/                 # Next.js 16 (App Router, React 19)
│       └── __tests__/            # Jest smoke tests
├── otel-collector/               # OTel Collector config + Dockerfile
├── grafana/dashboards/           # Importable 12-panel dashboard JSON
├── infra/                        # Pulumi IaC for Railway
├── docker-compose.yml            # Local dev stack
└── .github/workflows/            # CI: pytest + Jest + Next.js build
```

## Tech Stack

| Layer             | Technology                                                            |
| ----------------- | --------------------------------------------------------------------- |
| **Backend**       | FastAPI, SQLAlchemy, PostgreSQL, Redis                                |
| **ML**            | scikit-learn (Isolation Forest), ONNX Runtime (PCA-Autoencoder), SHAP |
| **LLM**           | LangChain (OpenAI / Anthropic / Google Gemini)                        |
| **Frontend**      | Next.js 16, React 19, TailwindCSS, Recharts, TanStack Query, Clerk     |
| **Observability** | OpenTelemetry SDK, OTel Collector, Grafana Cloud (Tempo + Prometheus) |
| **Infra**         | Railway, Docker Compose, Pulumi IaC                                   |
| **CI/CD**         | GitHub Actions (pytest + Jest + Next.js build)                        |
| **Testing**       | pytest (122 backend), Jest (35 frontend), load_test.py                 |

> For architectural decisions and tradeoffs, see [DESIGN.md](./DESIGN.md).

## License

Proprietary - All rights reserved
