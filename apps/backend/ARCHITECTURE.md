# Backend Architecture Overview

## System Overview

The backend is a modular financial AI observability platform built with FastAPI, SQLAlchemy, and PostgreSQL. It combines ML-based anomaly detection, LLM-powered agentic workflows, a Model Context Protocol (MCP) server for AI agent integration, and a full webhook/streaming system for external data ingestion — all instrumented with OpenTelemetry.

> **Live:** https://fin-observability-production.up.railway.app

---

## Major Components

### 1. MCP Server (`mcp_server.py`)
Model Context Protocol server exposing 9 tools for AI agents (Windsurf, Claude Desktop, Cursor, etc.):
- Transaction compliance scoring, SHAP explainability, batch processing (up to 10K)
- Portfolio risk analysis, incident browsing, drift status, model leaderboard
- `ingest_transactions` — agents push data for continuous compliance monitoring
- Input validation, OTel tracing per tool call, rate limiting (60/min per tool)
- Mounted at `/mcp` (Streamable HTTP transport)

### 2. Webhook & Streaming System (`routers/webhooks.py`)
Full-featured data ingestion and notification pipeline:
- **Inbound webhooks** — `POST /webhooks/transactions` (up to 10K per request)
- **SSE streaming** — `GET /webhooks/stream` (real-time compliance decisions via Server-Sent Events)
- **Outbound notifications** — Register callback URLs, flagged transactions POSTed with 3x retry + dead letter queue
- **Scheduled pull ingestion** — Configure external APIs to poll on intervals, auto-score and store
- **Shared scoring pipeline** — `score_and_store_transaction()` used by webhooks, MCP, and pull ingestion
- Auth via `X-Webhook-Key` header or `?key=` query param

### 3. ML Pipeline (`ml/`)
- **Anomaly detection** — Ensemble: Isolation Forest + PCA-Autoencoder (ONNX Runtime)
- **Explainability** — SHAP TreeExplainer, per-prediction feature importance
- **Drift detection** — PSI + Kolmogorov-Smirnov tests on sliding window (500 predictions)
- **Automated retraining** — Drift-triggered (every 6 hours via `DRIFT_CHECK_HOURS`), auto-versioning
- **A/B testing** — Chi-squared significance testing with hash-based traffic routing
- **Evaluation** — Batch eval, model leaderboard, precision/recall/F1

### 4. API Layer (FastAPI Routers)
- `routers/agent.py`: Compliance monitoring, ML scoring, SHAP explainability, drift, retraining, experiments
- `routers/incidents.py`: Incident CRUD, assignment, escalation, comments
- `routers/webhooks.py`: Webhook ingestion, SSE, outbound notifications, pull ingestion
- `routers/ops_metrics.py`: System metrics and operational health
- `routers/export_metadata.py`: Export lifecycle, batch verification, redelivery
- `routers/transactions.py`: Transaction export with digital signatures
- RBAC enforced on all sensitive endpoints (4 roles, 25 permissions)

### 5. Agentic AI Services (`services/`)
- `agent_service.py`: LLM-powered triage with explainability
- `incident_remediation_service.py`: Automated remediation workflows
- `compliance_automation_service.py`: Automated compliance checks
- `audit_summary_service.py`: Audit log summarization
- LangChain with pluggable providers (OpenAI, Anthropic, Google Gemini)

### 6. Models & Database
- `models.py`: SQLAlchemy ORM — Transaction, Incident, User, ComplianceLog, AgentAction, AgentActionAuditLog, ExportMetadata, ComplianceFeedback, SystemMetric
- PostgreSQL in production, SQLite for tests
- Alembic for migrations (`alembic/`)

### 7. Observability (`telemetry.py`)
- OpenTelemetry SDK (1.39.1) — traces every request, DB query, ML inference, MCP tool call
- Direct OTLP/HTTP export to Grafana Cloud (Tempo + Prometheus)
- OTel Collector also available (Railway service `ravishing-prosperity`)
- Custom metrics: request rate, latency histograms, anomaly counts, MCP tool usage

### 8. Security & RBAC (`rbac.py`, `security.py`)
- 4 roles: admin, compliance, analyst, viewer
- 25 fine-grained permissions
- Demo mode with write guard (blocks mutations for unauthenticated users)
- Webhook API key auth (constant-time comparison via `hmac.compare_digest`)

---

## Data Flow

### Transaction Scoring (any ingestion path)
```
External System / AI Agent / Scheduled Pull
        │
        ▼
┌─────────────────────────────────────────┐
│  Ingestion Layer                         │
│  (webhook POST / MCP tool / pull job)   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  score_and_store_transaction()           │
│  - ML Ensemble scoring (IF + Autoenc.)  │
│  - Store result in DB                    │
│  - Publish to SSE EventBus              │
│  - Notify outbound callbacks if flagged │
│  - OTel span with all attributes        │
└──────────────┬──────────────────────────┘
               │
        ┌──────┼──────┐
        ▼      ▼      ▼
   Database  SSE    Callbacks
   (stored)  Stream  (if flagged)
```

### Agentic Action
1. Incident detected (via API, webhook, or scheduled job)
2. Agentic triage (`/agent/triage`) — LLM reasoning with explainability
3. Action submitted for approval (multi-party, RBAC-enforced)
4. Human approves/rejects, triggering audit log
5. Export or compliance workflow may follow

---

## Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `WEBHOOK_API_KEY` | Auth key for webhook endpoints |
| `WEBHOOK_CALLBACK_URLS` | Comma-separated outbound callback URLs |
| `PULL_INGESTION_SOURCES` | JSON array of pull ingestion source configs |
| `DRIFT_CHECK_HOURS` | Interval for drift-triggered retraining (default: 6) |
| `PII_HASH_SALT` | Salt for deterministic PII hashing |
| `PII_HASH_ENABLED` | Enable PII sanitization in audit trail (default: true) |
| `AUDIT_RETENTION_YEARS` | Years to retain audit entries (default: 7, per SEC 17a-4) |
| `GRAFANA_CLOUD_INSTANCE_ID` | Grafana Cloud instance for OTel export |
| `GRAFANA_CLOUD_API_TOKEN` | Grafana Cloud API token |
| `OTEL_SERVICE_NAME` | Service name for traces (default: fin-observability) |

---

## Testing

122 backend tests covering:
- Webhook ingestion (single, batch, auth, errors)
- SSE EventBus (pub/sub, replay, queue overflow)
- Outbound notifications (callbacks, DLQ)
- Pull ingestion (source management)
- Scoring pipeline (positive/negative/zero amounts, bad timestamps)
- RBAC (roles, permissions, deactivation)
- Drift detection (PSI, KS tests)
- Telemetry (spans, metrics)
- Integration (all API endpoints)

```bash
DATABASE_URL=sqlite:///./test.db pytest apps/backend/tests/ -v
```

---

## References
- See `README.md` for setup and quick start
- See `API.md` for full endpoint reference
- See `AGENTIC_AUDITABILITY.md` for audit field details
- See `../../docs/ARCHITECTURE.md` for system-level architecture
