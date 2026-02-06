Financial AI Observability Platform

## Overview

This monorepo contains the full-stack implementation of a Financial AI Observability platform designed to provide real-time anomaly detection, compliance monitoring, and agentic AI-driven automation for financial services clients.

## Features

- Real-time anomaly detection using Isolation Forest and KNN models
- Compliance monitoring with SEC 17a-4 and FINRA 4511 audit trails
- **Financial Compliance Agent** - AI-powered transaction monitoring with governance/audit trails
- Agentic AI capabilities for incident triage, remediation, compliance automation, and audit summarization (works without OpenAI key via heuristic fallback)
- OpenTelemetry instrumentation compatible with ITRS Geneos platform
- Kafka streaming stubs for event ingestion
- Next.js frontend with real-time dashboard and compliance badges

## 🚀 Quick Start

### Prerequisites

- Node.js 20+ and npm 9+
- Python 3.9+
- PostgreSQL 13+
- Redis (for caching)

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
   npm install
   ```

2. **Start the development server**:

   ```bash
   npm run dev --workspace=apps/frontend
   ```

3. **Open your browser** to: http://localhost:3000

## Project Structure

```
fin-ai-observability/
├── apps/
│   ├── frontend/      # Next.js 16.1.6 (App Router, Turbopack)
│   └── backend/       # FastAPI 0.111.0
├── packages/
│   ├── agentic-core/  # LangChain 0.3.x, OpenAI
│   ├── shared-types/  # TypeScript 5.5.x
│   └── telemetry/    # OpenTelemetry Python/JS
└── docs/              # Project documentation
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
- **Testing**: `pytest apps/backend/tests/ -v`
- **Note**: LLM services (triage, remediation, compliance, audit) work without an `OPENAI_API_KEY` using keyword-matching heuristics

### Frontend Development

- **Environment Variables**: Copy `apps/frontend/env.example` to `apps/frontend/.env.local` and update values
- **Linting**: `npm run lint`
- **Testing**: `npm test`
- **Install types**: `@types/node`, `@types/react`, `@types/react-dom` are in devDependencies — run `npm install` to resolve TS errors

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
- **OpenTelemetry Tracing:** Backend is instrumented for OpenTelemetry. To enable local tracing, run:

  ```sh
  docker run --name otel-collector -p 4317:4317 -p 4318:4318 -p 55681:55681 otel/opentelemetry-collector:latest
  ```

  This will allow traces and metrics to be exported from the backend. See backend logs for exporter status.

### Troubleshooting

- **WebSocket 403 Errors:** Ensure backend `/ws/incidents` and `/ws/compliance` endpoints call `await websocket.accept()` and have no permission checks for local testing.
- **API 404s on `/api/systems`:** Make sure the Next.js rewrite rule is present and restart the frontend dev server after changes.
- **Frontend `.map` Errors:** The backend now returns `{ systems: [...] }` for `/api/systems`. Use `data.systems.map(...)` in the frontend.
- **OpenTelemetry Exporter Errors:** If you see `StatusCode.UNAVAILABLE`, ensure the collector is running as above.
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
```

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
- 43 passing tests (integration, unit, ML model)
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

### Phase 4: Future
- [ ] Deploy to Railway (public URL)
- [ ] Real production dataset integration
- [ ] Deep learning LSTM with ONNX Runtime inference
- [ ] SHAP waterfall charts in frontend (recharts)
- [ ] Automated retraining pipeline on schedule
