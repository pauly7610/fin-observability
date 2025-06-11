# Backend Architecture Overview

## System Overview
The backend is a modular, trading operations automation platform for real-time financial observability, agentic workflows, and export auditability. It is built with FastAPI, SQLAlchemy, Alembic, and Postgres, and is designed for extensibility, security, and high-frequency trading desk support.

---

## Major Components

### 1. API Layer (FastAPI Routers)
- `routers/agent.py`: Agentic workflow endpoints (triage, remediation, automation, audit summarization)
- `routers/ops.py`: Human-in-the-loop ops (approval, rejection, assignment, escalation, comments, metrics)
- `routers/export_metadata.py`: Export lifecycle, batch verification, and redelivery
- RBAC enforced on all sensitive endpoints

### 2. Models & Schemas
- `models.py`: SQLAlchemy ORM models for users, agent actions, audit logs, exports, incidents, etc.
- `schemas.py`: Pydantic schemas for API validation and serialization

### 3. Services
- `services/agent_service.py`: Agentic triage and explainability logic
- `services/incident_remediation_service.py`: Automated remediation workflows
- `services/compliance_automation_service.py`: Automated compliance checks
- `services/audit_summary_service.py`: Audit log summarization

### 4. Audit & Export
- `AgentActionAuditLog`: Every agentic or human action is audit-logged with full agentic context
- `ExportMetadata`: Tracks export hash, signature, delivery, verification, and lifecycle
- SIEM/syslog integration for real-time monitoring

### 5. Scheduling & Automation
- `scheduled_exports.py`: Automated/scheduled export jobs
- Background tasks for escalation, export delivery, and verification

### 6. Database & Migrations
- Postgres database
- Alembic for migrations (`alembic/`)

---

## Data Flow Example: Agentic Action
1. **Incident detected** (via API or scheduled job)
2. **Agentic triage** (`/agent/triage`) runs explainability logic, logs input/output/version
3. **Action submitted for approval** (multi-party, RBAC-enforced)
4. **Human approves/rejects** via `/agent/ops/actions/{id}/approve|reject`, triggering audit log
5. **Export or compliance workflow** may be triggered, tracked in `ExportMetadata`

---

## Security & Compliance
- All sensitive actions require `admin` or `compliance` role
- All agentic actions and overrides are fully attributed and audit-logged
- Hash chain and digital signature for export integrity

---

## Extensibility
- Add new agentic workflows by extending services and routers
- Add new export types or compliance checks in `export_metadata.py` and services

---

## References
- See `README.md` for setup and API usage
- See `AGENTIC_AUDITABILITY.md` for audit field details
- See code in `routers/`, `services/`, and `models.py`

---

## Contact
For architecture or extension questions, contact the backend engineering team lead.
