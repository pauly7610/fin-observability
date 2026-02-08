# Financial AI Observability Platform

> **Live:** [https://fin-observability-production.up.railway.app](https://fin-observability-production.up.railway.app)

## Overview

This monorepo contains the full-stack implementation of a Financial AI Observability platform designed to provide real-time anomaly detection, compliance monitoring, and agentic AI-driven automation for financial services clients.

## Features

- Real-time anomaly detection using Isolation Forest and PCA-Autoencoder ensemble
- Compliance monitoring with SEC 17a-4 and FINRA 4511 audit trails
- **Financial Compliance Agent** — AI-powered transaction monitoring with governance/audit trails
- **Multi-provider LLM integration** — OpenAI, Anthropic, and Google Gemini via LangChain with structured output and automatic heuristic fallback
- Agentic AI for incident triage, remediation, compliance automation, and audit summarization
- Runtime model switching via `/agent/config` endpoints (admin-only)
- SHAP explainability dashboard with waterfall charts
- A/B testing framework with chi-squared significance testing
- OpenTelemetry instrumentation with OTel Collector forwarding
- Next.js frontend with real-time dashboard, model management, and compliance badges

## 🚀 Quick Start

### Prerequisites

- Node.js 20+ and pnpm 9+
- Python 3.10+
- PostgreSQL 13+ (or SQLite for local dev)
- Redis (optional — falls back to in-memory)

### Backend Setup

1. **Navigate to the project root** (important!):

   ```bash
   cd /path/to/fin-observability
   ```

2. **Set up Python environment and install dependencies**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r apps/backend/requirements.txt
   ```

3. **Start the backend server**:

   ```bash
   # From the project root directory
   uvicorn apps.backend.main:app --reload
   ```

   > **Note**: Always start the backend from the project root to avoid import errors.

4. **Verify the backend** is running at: http://localhost:8000

### Frontend Setup

1. **Install Node.js dependencies** (from project root):

   ```bash
   pnpm install
   ```

2. **Start the development server**:

   ```bash
   pnpm run dev
   ```

3. **Open your browser** to: http://localhost:3000

## Project Structure

```
fin-ai-observability/
├── apps/
│   ├── frontend/          # Next.js 16.1.6 (App Router, Turbopack)
│   └── backend/           # FastAPI 0.111.0
│       ├── services/      # LLM-powered agent services with fallback
│       │   ├── llm_utils.py               # Multi-provider LLM (OpenAI/Anthropic/Google)
│       │   ├── agent_service.py           # Incident triage (LLM + heuristic)
│       │   ├── incident_remediation_service.py
│       │   ├── compliance_automation_service.py
│       │   └── audit_summary_service.py
│       ├── routers/       # FastAPI routers incl. /agent/config
│       └── tests/         # 60 tests (integration, unit, LLM fallback)
├── packages/
│   ├── agentic-core/      # LangChain agents (Python)
│   ├── shared-types/      # TypeScript shared types
│   └── telemetry/         # OpenTelemetry JS SDK
├── .github/workflows/     # CI: backend tests + frontend build
└── docs/                  # PRD, Architecture
```

## Approval Workflow & Compliance

Sensitive actions and exports are protected by a robust approval workflow. All major backend actions require explicit approval from privileged users (`admin`, `compliance`, or `analyst` roles) before execution.

- Approval requests appear in the frontend dashboard and resource detail pages
- Only authorized users can approve/reject actions
- All decisions are fully audit-logged
- Batch approval/rejection is supported
- The workflow supports multi-step and multi-role approvals

## Development

### Backend Development

- **Environment Variables**: Copy `apps/backend/env.example` to `apps/backend/.env` and update values
- **Migrations**: `alembic upgrade head`
- **Testing**: `DATABASE_URL=sqlite:///./test.db pytest apps/backend/tests/ -v`
- **LLM providers**: Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY` — services auto-detect the provider. Without any key, all services fall back to keyword heuristics.
- **Runtime model switching**: `GET /agent/config` shows current LLM config; `POST /agent/config/model?provider=openai&model=gpt-4o` switches at runtime (admin-only)

### Frontend Development

- **Environment Variables**: Copy `apps/frontend/env.example` to `apps/frontend/.env.local` and update values
- **Linting**: `pnpm run lint`
- **Testing**: `pnpm test`
- **Build all packages**: `pnpm run build`

## Troubleshooting

### Common Issues

**Backend Import Errors**

- **Error**: `ModuleNotFoundError: No module named 'apps'`
- **Solution**: Always start the backend from the project root directory, not from `apps/backend`

**Frontend Styling Issues**

- If Tailwind/DaisyUI styles aren't loading:
  1. Delete `.next` directory and `node_modules`
  2. Run `npm install`
  3. Restart the development server

## License

Proprietary - All rights reserved

## Authentication

The platform supports two authentication modes:

- **Header-based (default for development)**: Set `x-user-email` and `x-user-role` headers
- **JWT (production)**: Use `POST /auth/login` to get a Bearer token, then pass `Authorization: Bearer <token>`

Set `AUTH_MODE=jwt` in your `.env` to enforce JWT authentication. Both modes work simultaneously — JWT takes priority when a Bearer token is provided.

### Register & Login (JWT mode)

```bash
# Register
curl -X POST "http://localhost:8000/auth/register?email=admin@example.com&password=admin123&full_name=Admin&role=admin"

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

## Running Tests

```bash
# From project root
pytest apps/backend/tests/ -v

# Individual test suites
pytest apps/backend/tests/test_integration.py -v      # All API endpoints
pytest apps/backend/tests/test_anomaly_detector.py -v  # ML model
pytest apps/backend/tests/test_metrics_service.py -v   # Redis metrics
pytest apps/backend/tests/test_compliance_monitor.py -v # Compliance
```

Contributing
Please see CONTRIBUTING.md for guidelines.

## Recent Integration & Development Updates (2024-06)

### Major Improvements

- **REST & WebSocket Endpoints:** Added and rewired endpoints for agentic actions, compliance, and incidents. WebSocket endpoints now support real-time updates for incidents and compliance.
- **Frontend-Backend Integration:** Updated all frontend hooks and types to match backend API shapes. Improved error handling and type safety with Zod and TypeScript.
- **Proxy/Rewrite Setup:** Next.js frontend now proxies `/api/*` requests to the backend using a rewrite rule in `next.config.js` for seamless local development.
- **Test Data:** Backend endpoints return mock/test data if the database is empty, improving frontend development experience.
- **Authentication:** Supports both JWT (`POST /auth/login`) and header-based auth. Set `AUTH_MODE=jwt` for production. Header-based auth is the default for local development.
- **OpenTelemetry Tracing:** Backend is instrumented for OpenTelemetry. Trace/metric export is controlled by the `OTEL_EXPORTER_OTLP_ENDPOINT` env var:
  - **Production (Railway):** Set to `ravishing-prosperity.railway.internal:4317` — the OTel Collector runs as a separate Railway service.
  - **Local development:** Run a local collector:
    ```sh
    docker run --name otel-collector -p 4317:4317 -p 4318:4318 otel/opentelemetry-collector:latest
    ```
    Then set `OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317`.
  - **Disabled:** If the env var is not set, exporters are skipped entirely (no retry errors).

### Troubleshooting

- **WebSocket 403 Errors:** Ensure backend `/ws/incidents` and `/ws/compliance` endpoints call `await websocket.accept()` and have no permission checks for local testing.
- **API 404s on `/api/systems`:** Make sure the Next.js rewrite rule is present and restart the frontend dev server after changes.
- **Frontend `.map` Errors:** The backend now returns `{ systems: [...] }` for `/api/systems`. Use `data.systems.map(...)` in the frontend.
- **OpenTelemetry Exporter Errors:** If you see `StatusCode.UNAVAILABLE`, either start a local collector or unset `OTEL_EXPORTER_OTLP_ENDPOINT` to disable exporting.
- **DeprecationWarnings:** If you see `util._extend` warnings, update your dependencies with `npm update`.
- **Vue Source Map 404s:** These are likely from browser extensions and can be ignored unless you are developing Vue components.

### Commit Example

See the latest commit message for a summary of all major changes.

## 🤖 Financial Compliance Agent

The platform includes an AI-powered Financial Compliance Agent that monitors transactions for regulatory compliance.

### Features

- **FINRA 4511 & SEC 17a-4 Compliance** - Automated regulatory rule checking
- **Anomaly Detection** - ML-powered Isolation Forest scoring for suspicious transactions
- **Decision Transparency** - Full reasoning and alternative actions provided
- **Audit Trails** - Complete traceability for compliance reporting

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agent/compliance/monitor` | POST | Submit a transaction for compliance analysis |
| `/agent/compliance/status` | GET | Check agent health and capabilities |

### Example Request

```bash
curl -X POST http://localhost:8000/agent/compliance/monitor \
  -H "Content-Type: application/json" \
  -d '{
    "id": "txn_001",
    "amount": 50000,
    "counterparty": "ACME Corp",
    "account": "1234567890",
    "timestamp": "2024-01-15T14:30:00Z",
    "type": "wire"
  }'
```

### Decision Types

| Action | Description |
|--------|-------------|
| `approve` | Transaction passed all compliance checks |
| `manual_review` | High anomaly score requires human review |
| `block` | Regulatory violation detected |

### Frontend

Access the Compliance Monitor UI via the **Compliance Monitor** tab in the dashboard at `http://localhost:3000/incidents`.

### New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agent/compliance/monitor` | POST | Submit a transaction for ML-powered compliance analysis |
| `/agent/compliance/status` | GET | Check agent health, model version, and capabilities |
| `/agent/compliance/metrics` | GET | Real-time performance metrics (Redis-backed) |
| `/agent/compliance/test-batch` | POST | Run 100 synthetic transactions for validation |
| `/agent/compliance/metrics/reset` | POST | Admin-only: Reset metrics counters |

## 📊 ML Model & Performance Validation

### Anomaly Detection Model

- **Algorithm:** Isolation Forest (scikit-learn)
- **Training Data:** 2,000 synthetic normal transactions
- **Features (6):** amount, hour, day_of_week, is_weekend, is_off_hours, txn_type_encoded
- **Contamination:** 10% (expected outlier rate)
- **Model Version:** 2.0.0
- **Persistence:** Pickle (auto-trains on first run, loads from disk on restart)

### Test Results (100 synthetic transactions)

| Metric | Value |
|--------|-------|
| **Approval Rate** | ~72% |
| **Manual Review Rate** | ~23% |
| **Block Rate** | ~5% |
| **Avg Confidence** | ~85% |

Run your own validation:

```bash
curl -X POST http://localhost:8000/agent/compliance/test-batch?count=100
```

### Model Performance vs Baselines

| Approach | Approval Rate | Manual Review | Block Rate | Notes |
|----------|---------------|---------------|------------|-------|
| **Isolation Forest (Current)** | 72% | 23% | 5% | Feature-engineered ML |
| Random Forest (tested) | 68% | 27% | 5% | Overfits on small dataset |
| Rule-based heuristic | 60% | 35% | 5% | Too conservative |

**Why Isolation Forest:** Best balance of precision and recall on our synthetic data distribution. Unsupervised approach handles novel anomaly patterns without labeled training data.

### Metrics Persistence

Metrics are stored in Redis for persistence across restarts. Falls back to in-memory storage if Redis is unavailable.

**Required environment variables for production:**

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `DATABASE_URL` | PostgreSQL connection URL | SQLite (local) |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |

## 🚢 Deployment (Railway)

### Prerequisites

- [Railway CLI](https://docs.railway.app/develop/cli) installed
- Railway account

### Deploy Backend

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
cd fin-observability
railway init

# Add Redis addon
railway add --plugin redis

# Deploy
railway up

# Get public URL
railway domain
```

### Environment Variables (Railway Dashboard)

Set these in your Railway project settings:

```
REDIS_URL=<auto-populated by Railway Redis addon>
DATABASE_URL=<auto-populated by Railway Postgres addon>
CORS_ORIGINS=https://your-frontend.up.railway.app
OTEL_EXPORTER_OTLP_ENDPOINT=ravishing-prosperity.railway.internal:4317
```

### OpenTelemetry Collector (Railway)

The OTel Collector runs as a separate service (`ravishing-prosperity`) in the same Railway project:

- **Config:** `otel-collector/otel-collector-config.yaml`
- **Dockerfile:** `otel-collector/Dockerfile`
- **Receives:** OTLP gRPC (`:4317`) and HTTP (`:4318`)
- **Exports:** Logging (stdout → Railway logs). To forward to Grafana Cloud, Honeycomb, etc., add an `otlphttp` exporter to the config.

### Docker (Alternative)

```bash
docker build -t fin-obs-backend .
docker run -p 8000:8000 -e REDIS_URL=redis://host:6379 fin-obs-backend
```

## 🚀 Production Roadmap

### Phase 1: ✅ Complete
- ML-powered anomaly detection (Isolation Forest, 6 features)
- Compliance rule engine (FINRA 4511, SEC 17a-4)
- Real-time metrics (Redis-backed with in-memory fallback)
- JWT + header-based authentication
- 60 passing tests (integration, unit, ML model, LLM fallback)
- Railway deployment config

### Phase 2: ✅ Complete
- [x] Realistic transaction dataset (5,000 anonymized transactions via Faker)
- [x] Model retraining endpoint (`POST /agent/compliance/retrain`) with auto-versioning
- [x] Precision/recall tracking with analyst feedback loop
- [x] Confidence calibration analysis
- [x] Confusion matrix endpoint

### Phase 3: ✅ Complete
- [x] Multi-model ensemble (Isolation Forest + PCA-Autoencoder sequence model)
- [x] SHAP explainability dashboard (`/explainability` frontend page)
- [x] A/B testing framework with chi-squared significance testing
- [x] Internal evaluation service with leaderboard and audit trails

### New API Endpoints (Phase 2 & 3)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agent/compliance/feedback` | POST | Submit analyst feedback for precision/recall |
| `/agent/compliance/metrics/evaluation` | GET | Precision, recall, F1, confusion matrix |
| `/agent/compliance/metrics/calibration` | GET | Confidence calibration analysis |
| `/agent/compliance/metrics/confusion` | GET | Confusion matrix only |
| `/agent/compliance/retrain` | POST | Retrain model from dataset (admin) |
| `/agent/compliance/explain` | POST | SHAP explanation for a single transaction |
| `/agent/compliance/explain-batch` | POST | Aggregate SHAP feature importance |
| `/agent/compliance/ensemble` | POST | Ensemble prediction (IF + sequence) |
| `/agent/compliance/model/ensemble` | GET | Ensemble model metadata |
| `/agent/compliance/experiments` | POST/GET | Create/list A/B test experiments |
| `/agent/compliance/experiments/{id}/results` | GET | A/B test results with significance |
| `/agent/compliance/experiments/{id}/promote` | POST | Promote winning model variant |
| `/agent/compliance/eval/submit` | POST | Submit batch for evaluation |
| `/agent/compliance/eval/results` | GET | Recent evaluation results |
| `/agent/compliance/eval/leaderboard` | GET | Model version leaderboard by F1 |
| `/agent/compliance/eval/audit-trail` | GET | Full evaluation audit trail |

### Phase 4: ✅ Complete
- [x] Deploy to Railway (public URL): [fin-observability-production.up.railway.app](https://fin-observability-production.up.railway.app)
- [x] OpenTelemetry Collector deployed as Railway service with configurable OTLP exporters
- [x] Environment variable configuration (`env.example`)

### Phase 5: ✅ Complete
- [x] Enhanced production dataset (10K transactions, account profiles, temporal patterns, geo risk, velocity features)
- [x] 2-Layer PCA-Autoencoder with ONNX Runtime inference (~2x faster scoring)
- [x] SHAP waterfall charts in frontend (Recharts BarChart with stacked waterfall)
- [x] Automated retraining pipeline (weekly schedule via APScheduler, configurable via `RETRAIN_SCHEDULE_HOURS`)
- [x] OTel Collector forwarding configs for Grafana Cloud, Honeycomb, and Axiom (pre-configured, env var driven)

### New API Endpoints (Phase 5)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agent/compliance/retrain/scheduled` | POST | Manually trigger the automated retraining pipeline |
| `/agent/compliance/retrain/status` | GET | Get retraining pipeline status and schedule |

### Phase 6: ✅ Complete
- [x] Multi-provider LLM integration (OpenAI, Anthropic, Google Gemini) via LangChain
- [x] Structured LLM output with Pydantic schemas for all agent services
- [x] Graceful heuristic fallback when no API key is configured
- [x] Runtime model switching via `GET/POST /agent/config` endpoints
- [x] Frontend Model Management UI (compliance page → Model Management tab)
- [x] Source badges (LLM/Heuristic) on agent actions in frontend
- [x] GitHub Actions CI workflow (backend tests + frontend build)
- [x] pnpm monorepo migration with Turborepo
- [x] Dockerfile optimization (dropped gcc/libpq-dev, Python healthcheck)
- [x] OpenTelemetry telemetry package updated to OTel v2 API
- [x] 60 passing tests

### New API Endpoints (Phase 6)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agent/config` | GET | Current LLM provider, model, and available options |
| `/agent/config/model` | POST | Switch LLM provider/model at runtime (admin) |

### Phase 7: Future
- [ ] Real production dataset integration (live data feeds)
- [ ] Deep learning LSTM autoencoder (PyTorch + ONNX export)
- [ ] Grafana Cloud dashboard integration
- [ ] Automated CI/CD retraining on data drift detection
- [ ] Multi-tenant account isolation
