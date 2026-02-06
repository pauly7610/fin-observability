Financial AI Observability Platform

## Overview

This monorepo contains the full-stack implementation of a Financial AI Observability platform designed to provide real-time anomaly detection, compliance monitoring, and agentic AI-driven automation for financial services clients.

## Features

- Real-time anomaly detection using Isolation Forest and KNN models
- Compliance monitoring with SEC 17a-4 and FINRA 4511 audit trails
- **Financial Compliance Agent** - AI-powered transaction monitoring with governance/audit trails
- Agentic AI capabilities with LangChain for incident triage and remediation
- OpenTelemetry instrumentation compatible with ITRS Geneos platform
- Kafka streaming stubs for event ingestion
- Next.js frontend with real-time dashboard and compliance badges

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm 9+
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

1. **Install Node.js dependencies**:

   ```bash
   cd apps/frontend
   npm install
   ```

2. **Start the development server**:

   ```bash
   npm run dev
   ```

3. **Open your browser** to: http://localhost:3000

## Project Structure

```
fin-ai-observability/
├── apps/
│   ├── frontend/      # Next.js 14.2.1 (App Router)
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

- **Environment Variables**: Copy `.env.example` to `.env` and update values
- **Migrations**: `alembic upgrade head`
- **Testing**: `pytest`

### Frontend Development

- **Environment Variables**: Update `.env.local` as needed
- **Linting**: `npm run lint`
- **Testing**: `npm test`

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

## Getting Started

Prerequisites
Node.js 20.x

Python 3.12.x

PostgreSQL 15.x

Installation
bash
pnpm install
Running the Development Environment
bash
pnpm dev
Testing
Backend tests with pytest

Frontend tests with Jest and React Testing Library

Contributing
Please see CONTRIBUTING.md for guidelines.

License
MIT

## Recent Integration & Development Updates (2024-06)

### Major Improvements

- **REST & WebSocket Endpoints:** Added and rewired endpoints for agentic actions, compliance, and incidents. WebSocket endpoints now support real-time updates for incidents and compliance.
- **Frontend-Backend Integration:** Updated all frontend hooks and types to match backend API shapes. Improved error handling and type safety with Zod and TypeScript.
- **Proxy/Rewrite Setup:** Next.js frontend now proxies `/api/*` requests to the backend using a rewrite rule in `next.config.js` for seamless local development.
- **Test Data:** Backend endpoints return mock/test data if the database is empty, improving frontend development experience.
- **Authentication Relaxed for Testing:** Key endpoints (incidents, agentic actions) have relaxed authentication for local testing. Re-enable RBAC for production.
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
- **Anomaly Detection** - Heuristic-based scoring for suspicious transactions
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
