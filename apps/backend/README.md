# Fin Observability Backend

## Overview
This backend powers the compliance, auditability, and agentic workflows for the Fin Observability platform. It is built with FastAPI, SQLAlchemy, and Postgres, and is designed for financial services and compliance-critical environments.

---

## Features

### 1. Agentic Workflows
- **Multi-party, role-based, and sequential approval** for actions
- **Automated escalation** of overdue items
- **Assignment, commenting, and audit logging** for all agent actions
- **Full agentic explainability**: All agent/AI actions log input, output, version, explanation, actor type, and simulation/test mode
- **Override tracking**: Human overrides of agentic recommendations are explicitly logged

### 2. Export, Compliance, and Audit
- **ExportMetadata**: Every export (manual or scheduled) is tracked with hash, signature, delivery, and verification status
- **Batch verification** and **re-delivery** endpoints
- **Audit logs**: Every significant event is logged in `AgentActionAuditLog` with full context and agentic fields
- **SIEM/syslog integration** for real-time monitoring

### 3. Security & Compliance
- **RBAC** enforced on all sensitive endpoints
- **Cryptographic hash chain** and digital signatures for exports
- **Environment-variable driven secrets** (see `.env`)

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
