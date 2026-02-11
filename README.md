# Financial AI Observability Platform

[![CI](https://github.com/pauly7610/fin-observability/actions/workflows/ci.yml/badge.svg)](https://github.com/pauly7610/fin-observability/actions/workflows/ci.yml)
[![Deploy](https://img.shields.io/badge/Railway-deployed-blueviolet?logo=railway)](https://fin-observability-production.up.railway.app)
[![Grafana](https://img.shields.io/badge/Grafana-dashboard-F46800?logo=grafana)](https://pauly7610.grafana.net)
[![Tests](https://img.shields.io/badge/tests-82%2F82-brightgreen?logo=pytest)](https://github.com/pauly7610/fin-observability/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-20+-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js)](https://nextjs.org/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-1.39-7B61FF?logo=opentelemetry)](https://opentelemetry.io/)
[![License](https://img.shields.io/badge/license-proprietary-red)](./LICENSE)

> **Live:** [fin-observability-production.up.railway.app](https://fin-observability-production.up.railway.app) | **Grafana:** [pauly7610.grafana.net](https://pauly7610.grafana.net)

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
│  │  - RBAC       │                        │  Grafana Cloud   │  │
│  │  - OTel SDK   │───────────────────────▶│  (Tempo/Prom)    │  │
│  └──────────────┘   direct OTLP/HTTP      └──────────────────┘  │
│         │                                                       │
│  ┌──────────────┐                                               │
│  │    Redis      │  (metrics cache, optional)                   │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
         │
    ┌────▼─────┐
    │ Next.js  │  Frontend (App Router, React 19)
    │ Frontend │
    └──────────┘
```

## Features

- **Anomaly Detection** — Isolation Forest + PCA-Autoencoder ensemble with ONNX Runtime inference
- **Drift Detection** — PSI + KS test with auto-triggered retraining pipeline
- **Compliance Monitoring** — SEC 17a-4 / FINRA 4511 rule engine with audit trails
- **RBAC** — Role-based access control (admin, compliance, analyst, viewer) with fine-grained permissions
- **Agentic AI** — LLM-powered incident triage, remediation, and compliance automation (OpenAI/Anthropic/Google)
- **SHAP Explainability** — Per-prediction feature importance with waterfall charts
- **A/B Testing** — Chi-squared significance testing for model variants
- **Observability** — OpenTelemetry traces + metrics → Grafana Cloud (Tempo + Prometheus)
- **Database Seeding** — Configurable seed script (50K+ transactions, idempotent)
- **Load Testing** — Concurrent load test script with endpoint breakdown and latency percentiles

## Quick Start

### Prerequisites

- Python 3.10+ / Node.js 20+ / pnpm 9+
- PostgreSQL 13+ (or SQLite for local dev)

### Backend

```bash
cd fin-observability
python -m venv venv && source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r apps/backend/requirements.txt
cp apps/backend/env.example apps/backend/.env

# Start (always from project root)
uvicorn apps.backend.main:app --reload
```

### Frontend

```bash
pnpm install
pnpm run dev    # http://localhost:3000
```

### Docker Compose (full stack)

```bash
docker compose up -d   # Postgres + Redis + OTel Collector + Backend
```

### Seed Database

```bash
# Local
python -m apps.backend.seed_data

# Railway (public URL)
DATABASE_URL="postgresql://..." python -m apps.backend.seed_data

# Custom size (env vars: SEED_TRANSACTIONS, SEED_COMPLIANCE_LOGS, SEED_SYSTEM_METRICS, SEED_INCIDENTS)
SEED_TRANSACTIONS=50000 DATABASE_URL="postgresql://..." python -m apps.backend.seed_data
```

### Load Test

```bash
python scripts/load_test.py --requests 200 --concurrency 5
python scripts/load_test.py --base-url http://localhost:8000 --requests 1000
python scripts/load_test.py --requests 2000 --concurrency 20   # stress test
```

Endpoints covered: `/health`, `/transactions`, `/compliance`, `/incidents`, `/system-metrics`, `/auth/roles`, `/agent/compliance/monitor`, `/agent/compliance/drift/status`, `/agent/compliance/retrain/status`, `/anomaly/detect`

### Run Tests

```bash
DATABASE_URL=sqlite:///./test.db pytest apps/backend/tests/ -v   # 82 tests
```

## Project Structure

```
fin-observability/
├── apps/
│   ├── backend/                  # FastAPI 0.111.0
│   │   ├── ml/                   # ML models, drift detection, retraining
│   │   │   ├── anomaly_detector.py        # IF + PCA-Autoencoder ensemble
│   │   │   ├── drift_detector.py          # PSI + KS test
│   │   │   ├── retraining_pipeline.py     # Auto-retrain on drift
│   │   │   └── data/generate_dataset.py   # 1M transaction generator
│   │   ├── routers/              # API endpoints (agent, auth, compliance, etc.)
│   │   ├── services/             # LLM-powered agent services
│   │   ├── rbac.py               # Role-based access control
│   │   ├── security.py           # JWT + header auth, require_permission
│   │   ├── seed_data.py          # Database seeding (configurable)
│   │   └── tests/                # 60 tests
│   └── frontend/                 # Next.js 16 (App Router, React 19)
├── otel-collector/               # OTel Collector contrib config + Dockerfile
├── grafana/dashboards/           # Importable Grafana dashboard JSON
├── scripts/                      # Load testing, utilities
├── infra/                        # Pulumi IaC for Railway
├── docker-compose.yml            # Local dev: Postgres + Redis + OTel + Backend
├── .github/workflows/            # CI: backend tests + frontend build
└── docs/                         # PRD, Architecture
```

## Authentication

| Mode | Usage | How |
|------|-------|-----|
| **Header-based** | Development | `x-user-email` + `x-user-role` headers |
| **JWT** | Production | `POST /auth/login` → `Authorization: Bearer <token>` |

```bash
# Register
curl -X POST "http://localhost:8000/auth/register?email=admin@example.com&password=admin123&full_name=Admin&role=admin"

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

## RBAC Roles & Permissions

| Role | Permissions |
|------|------------|
| **admin** | Full access (25 permissions) — user management, model config, system settings |
| **compliance** | Agent actions, compliance ops, audit, explain (16 permissions) |
| **analyst** | Read-only + anomaly/audit/explain access (8 permissions) |
| **viewer** | Read-only compliance, model, metrics, transactions (4 permissions) |

## Observability

### Grafana Cloud Integration

The backend sends traces and metrics **directly** to Grafana Cloud via OTLP/HTTP with basic auth. The OTel Collector also runs as a sidecar for host metrics.

**Backend env vars:**
```
GRAFANA_CLOUD_INSTANCE_ID=<instance_id>
GRAFANA_CLOUD_API_TOKEN=<glc_token>
OTEL_SERVICE_NAME=fin-observability
```

**Collector env vars** (ravishing-prosperity service):
```
GRAFANA_CLOUD_INSTANCE_ID=<instance_id>
GRAFANA_CLOUD_API_TOKEN=<glc_token>
```

### Grafana Dashboard (12 Panels)

Import `grafana/dashboards/fin-observability.json` into Grafana Cloud → Dashboards → Import:

| Section | Panels |
|---------|--------|
| **Overview** | Request Rate, Error Rate (5xx), Anomalies Detected, Compliance Actions |
| **API Performance** | API Latency by Endpoint (p50/p95), Request Rate by Status Code, Request Rate by Endpoint, Business Metrics |
| **Infrastructure** | Host CPU Load Average (1m/5m/15m), Host Memory Usage (used/free/cached) |
| **Traces** | Recent Traces (Tempo — trace ID, service, endpoint, duration) |

### Custom Metrics (OTLP → Prometheus)

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | HTTP requests by method, route, status code |
| `http_request_duration_ms` | Histogram | Request latency in ms by method, route, status code |
| `anomalies_detected_total` | Counter | Anomalies flagged by ML model |
| `compliance_actions_total` | Counter | Compliance actions performed |
| `export_jobs_total` | Counter | Scheduled export jobs |

## Drift Detection & Auto-Retraining

The platform monitors model performance using **Population Stability Index (PSI)** and **Kolmogorov-Smirnov tests**:

- Features are recorded on every prediction
- Drift is checked against the training reference distribution
- When drift exceeds thresholds, retraining is auto-triggered
- Retraining runs on a configurable schedule (`RETRAIN_SCHEDULE_HOURS`, default: 168h/weekly)

## API Endpoints (Key)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/transactions` | GET/POST | List/create transactions |
| `/compliance` | GET | Compliance logs |
| `/incidents` | GET | Incidents list |
| `/auth/register` | POST | Register user |
| `/auth/login` | POST | JWT login |
| `/auth/roles` | GET | Role hierarchy & permissions |
| `/auth/assign-role` | POST | Assign role (admin) |
| `/agent/compliance/monitor` | POST | ML compliance analysis |
| `/agent/compliance/explain` | POST | SHAP explanation |
| `/agent/compliance/drift/check` | POST | Check model drift |
| `/agent/compliance/drift/status` | GET | Drift status |
| `/agent/compliance/retrain` | POST | Trigger retraining |
| `/agent/compliance/retrain/status` | GET | Retraining pipeline status |
| `/agent/config` | GET | Current LLM config |
| `/agent/config/model` | POST | Switch LLM provider (admin) |

## Deployment (Railway)

### Services

| Service | Description |
|---------|-------------|
| **Backend** | FastAPI app (`railway.toml` → `Dockerfile`) |
| **PostgreSQL** | Managed Postgres addon |
| **Redis** | Managed Redis addon |
| **ravishing-prosperity** | OTel Collector (`otel-collector/Dockerfile`) |

### Backend Environment Variables

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CORS_ORIGINS=*
JWT_SECRET_KEY=<secret>
GRAFANA_CLOUD_INSTANCE_ID=<id>
GRAFANA_CLOUD_API_TOKEN=<glc_token>
OTEL_SERVICE_NAME=fin-observability
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, SQLAlchemy, PostgreSQL, Redis |
| **ML** | scikit-learn (Isolation Forest), ONNX Runtime (PCA-Autoencoder), SHAP |
| **LLM** | LangChain (OpenAI / Anthropic / Google Gemini) |
| **Frontend** | Next.js 16, React 19, TailwindCSS, Recharts, TanStack Query |
| **Observability** | OpenTelemetry SDK, OTel Collector contrib, Grafana Cloud (Tempo + Prometheus) |
| **Infra** | Railway, Docker Compose, Pulumi IaC |
| **CI/CD** | GitHub Actions (pytest + Jest + Next.js build) |
| **Testing** | pytest (82 backend), Jest (2 frontend), load_test.py |

## License

Proprietary - All rights reserved
