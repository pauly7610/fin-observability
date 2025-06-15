# Fin Observability Backend

## 🚨 How to Start the Backend (Avoid Import Errors)

**To avoid `ModuleNotFoundError: No module named 'apps'`, always start the backend from the project root, NOT from the `apps/backend` directory.**

**Correct way:**

```bash
uvicorn apps.backend.main:app --reload
```

Run this command from your project root directory:

```
c:\Users\PaulC\Downloads\development\fin-observability
```

**Why?**

- The backend uses imports like `from apps.backend.routers import ...`.
- If you start from `apps/backend`, Python cannot find the `apps` package.
- Starting from the root ensures the `apps` package is discoverable.

**If you run from the wrong directory, you'll see:**

```
ModuleNotFoundError: No module named 'apps'
```

---

> **⚠️ NOTE: This backend uses the new LangChain 0.3.x+ ecosystem (langchain-core, langchain-community, langchain-openai, etc.).**
>
> - All code and dependencies must be compatible with LangChain 0.3.x+.
> - Legacy LangChain code (0.2.x and below) will not work and must be refactored.
> - If you need to run legacy agentic ops, use a separate Python environment with the old dependencies.

## Overview

This backend powers the trading operations automation, incident triage, remediation, and agentic workflows for the Fin Observability platform. Built with FastAPI, SQLAlchemy, and Postgres, it is designed for real-time trading operations, trading desk support, and financial automation, with compliance and auditability as supporting features.

---

## Features

### 1. Trading Ops AI Automation

- **Incident triage and remediation** for trading desk operations
- **Automated trading workflow approvals and escalations**
- **Assignment, commenting, and audit logging** for all trading ops actions
- **Agentic explainability**: All agent/AI actions log input, output, version, explanation, actor type, and simulation/test mode
- **Override tracking**: Human overrides of agentic recommendations are explicitly logged

### 2. Export, Compliance, and Audit (Supporting)

- **ExportMetadata**: Every export (manual or scheduled) is tracked with hash, signature, delivery, and verification status
- **Batch verification** and **re-delivery** endpoints
- **Audit logs**: Every significant event is logged in `AgentActionAuditLog` with full context and agentic fields
- **SIEM/syslog integration** for real-time monitoring

### 3. Security & Compliance (Supporting)

- **RBAC** enforced on all sensitive endpoints
- **Cryptographic hash chain** and digital signatures for exports
- **Environment-variable driven secrets** (see `.env`)

---

## Trading Operations Use Cases

- **Incident Management:** Automated detection, triage, and remediation of trading incidents (e.g., trade breaks, failed settlements, system outages).
- **Ops Approvals:** Multi-party, role-based approval workflows for trading actions and escalations.
- **Desk Workflow Automation:** Automate trading desk tasks, escalate overdue items, and track all actions for audit and transparency.
- **Real-time Monitoring:** SIEM/syslog integration for live trading event monitoring and alerting.

Compliance and auditability are fully supported, but the platform's core is trading ops automation and agentic operational intelligence.

---

## Directory Structure

- `main.py` — FastAPI app entrypoint
- `models.py` — SQLAlchemy ORM models
- `schemas.py` — Pydantic schemas
- `routers/` — API endpoints (users, transactions, agent, ops, export, etc.)
- `scheduled_exports.py` — Automated/scheduled export logic
- `services/` — Agentic/AI, compliance, and workflow services
- `alembic/` — Database migrations (Alembic)
- `.env` — Environment variables

---

## Approval Workflow (Sensitive Actions & Exports)

### Overview

Sensitive backend actions (agentic triage, remediation, compliance automation, audit summarization, and all major exports) are gated by an explicit approval workflow. This enforces compliance and auditability, requiring privileged users to approve actions before execution.

### Which Endpoints Require Approval?

- `/agent/triage` — Agentic triage (approval required)
- `/agent/remediate` — Agentic remediation (approval required)
- `/agent/compliance` — Agentic compliance automation (approval required)
- `/agent/audit_summary` — Agentic audit summarization (approval required)
- `/incidents/export` — Export incidents (approval required)
- `/transactions/export` — Export transactions (approval required)
- `/compliance/logs/export` — Export compliance logs (approval required)
- `/users/export` — Export users (approval required)

### How It Works

- When a user requests a sensitive action or export, the backend checks for an approved `ApprovalRequest` for that resource/user.
- If not approved, a new approval request is created and the action is blocked until approved by an authorized user (`admin`, `compliance`, or `analyst` roles).
- Once approved, the action proceeds as normal.

### Approval API Endpoints

- `GET /approval/?status=pending|approved|rejected` — List approval requests, filterable by status.
- `POST /approval/{approval_id}/decision` — Submit an approval or rejection decision with an optional reason.
- All approval actions are RBAC-gated and fully audit-logged.

### Audit Trail & Compliance

- Every approval request and decision is logged in the audit trail (`AgentActionAuditLog`), including decision reasons and timestamps.
- SIEM/syslog events are emitted for all approval and rejection actions.
- The audit trail is surfaced both in the backend and in the frontend UI for transparency.

### Frontend Integration

- The frontend provides a dedicated Approvals dashboard, contextual approval status/actions on resource detail pages, and sidebar notifications for pending approvals.
- Approval actions are only visible to authorized roles, with clear feedback and notification UX.
- Batch approval/rejection is supported in the Approvals dashboard for power users.

### Extensibility

- The workflow supports future multi-step or multi-role approvals, and is designed for extensibility and compliance-critical environments.

---

- All approval actions are logged for audit and SIEM monitoring.

### Approval API Endpoints

- `POST /approval/` — Submit a new approval request
- `GET /approval/` — List approval requests (with optional status filter)
- `POST /approval/{approval_id}/decision` — Approve or reject a pending approval

### Example Approval Request Flow

1. User attempts to export incidents via `/incidents/export`.
2. If no approval exists, backend responds:
   ```json
   {
     "detail": "Export requires approval",
     "approval_request_id": 42,
     "status": "pending"
   }
   ```
3. Admin/compliance user reviews and approves via `POST /approval/{approval_id}/decision`.
4. User can now re-attempt the export, which will succeed.

### Frontend Integration

- Approval tasks are surfaced in the sidebar (`TaskSidebar`) and dashboard.
- Approval requests and history are visible in detail pages and a dedicated approvals UI.
- Users with appropriate roles can approve/reject/escalate requests directly from the UI.
- All approval-related API calls are handled via the shared `apiRequest` utility.

---

## API Endpoints

### Agentic Operations

- `/agent/triage` — Agentic triage for incidents
- `/agent/remediate` — Agentic remediation for incidents
- `/agent/automate_compliance` — Automated compliance for transactions
- `/agent/ops/actions/{id}/approve|reject` — Approval/rejection with full audit

### Export & Audit

- `/exports/` — Export metadata CRUD
- `/exports/batch_verify` — Batch verification of export integrity
- `/exports/{id}/redeliver` — Re-delivery of exports
- `/agent/ops/actions/metrics` — Operational metrics

---

## Agentic Auditability Fields

All agentic actions and audit logs include:

- `ai_explanation`: Reasoning/explanation from agent/AI
- `agent_input`: Input provided to the agent/AI
- `agent_output`: Full output from agent/AI
- `agent_version`: Version of agent/AI/model
- `actor_type`: 'human', 'agent', or 'system'
- `override_type`: e.g., 'ai_override', 'manual_override'
- `is_simulation`: True if this was a simulation/test

---

## Database Migrations

- Uses Alembic for migrations
- To create a migration: `alembic revision --autogenerate -m "<message>"`
- To apply migrations: `alembic upgrade head`

---

## Environment Variables

See `.env` for all configuration, including:

- Database connection (Postgres)
- SMTP/email for exports
- AWS/S3 for export delivery
- Signing key vault integration
- SIEM/syslog host/port

---

## Running the Backend

1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` with your secrets and settings
3. Run database migrations: `alembic upgrade head`
4. Start the server: `uvicorn main:app --reload`

---

## Contributing

- PRs welcome! Please ensure all new endpoints are RBAC-protected and audit-logged.
- For agentic/AI features, always log input, output, and version.

---

## License

MIT

## Recent Integration & Tracing Setup (2024-06)

### OpenTelemetry Tracing

- The backend is instrumented for OpenTelemetry tracing and metrics.
- To enable local collection, run:
  ```sh
  docker run --name otel-collector -p 4317:4317 -p 4318:4318 -p 55681:55681 otel/opentelemetry-collector:latest
  ```
- The backend will export traces and metrics to the collector. Check backend logs for exporter status.
- You can customize the collector to export to Jaeger, Zipkin, or other backends as needed.

### New & Updated Endpoints

- **WebSocket:** `/ws/incidents` and `/ws/compliance` now support real-time updates for incidents and compliance.
- **REST:** `/api/systems` returns system health data for the frontend dashboard.
- **Relaxed Authentication:** Key endpoints have relaxed RBAC for local testing. Re-enable for production.
- **Test Data:** Endpoints return mock data if the database is empty, improving frontend development.

### Local Development & Troubleshooting

- **WebSocket 403:** Ensure all WebSocket endpoints call `await websocket.accept()` and have no permission checks for local testing.
- **Tracing Exporter Errors:** If you see `StatusCode.UNAVAILABLE`, ensure the collector is running as above.
- **API 404s:** Make sure frontend rewrites/proxy rules are set up for `/api/*` routes.
- **DeprecationWarnings:** If you see `util._extend` warnings, update dependencies with `npm update`.
