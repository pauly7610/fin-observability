# Backend API Reference

This document provides a concise reference for the main backend API endpoints, request/response formats, and authentication required to wire up the frontend. For full details and live testing, see the `/docs` (Swagger UI) endpoint on your running backend.

---

## Authentication
- **RBAC** enforced via `require_role` dependency on sensitive endpoints.
- Most endpoints require an authenticated user with one of: `admin`, `compliance`, `analyst` roles.
- Auth is typically handled via session/cookie or bearer token (see backend implementation).

---

## Core Endpoints

### Agentic Workflow
- **POST `/agent/triage`**
  - Triage an incident with agentic explainability and audit fields.
  - **Body:** `{ "incident": { ... } }`
  - **Returns:** `{ "risk_level": ..., "confidence": ..., "rationale": ..., "recommendation": ... }`

- **POST `/agent/remediate`**
  - Run agentic remediation on an incident.
  - **Body:** `{ "incident": { ... } }`
  - **Returns:** `{ ... }` (remediation result)

- **POST `/agent/automate_compliance`**
  - Automate compliance check on a transaction/event.
  - **Body:** `{ "transaction": { ... } }`
  - **Returns:** `{ ... }` (compliance result)

- **POST `/agent/audit_summary`**
  - Summarize audit logs with agentic explainability.
  - **Body:** `{ "logs": [ ... ] }`
  - **Returns:** `{ ... }` (summary)

---

### Human Oversight
- **POST `/agent/actions/{action_id}/approve`**
  - Approve a pending agent action.
  - **Body:** `{ "operator": "username", "comment": "..." }`
  - **Returns:** `AgentAction` object

- **POST `/agent/actions/{action_id}/reject`**
  - Reject a pending agent action.
  - **Body:** `{ "operator": "username", "comment": "..." }`
  - **Returns:** `AgentAction` object

---

### Export & Compliance
- **GET `/export_metadata/`**
  - List export jobs and statuses.
- **POST `/export_metadata/verify_batch`**
  - Batch verify export hashes.
- **POST `/export_metadata/redeliver_batch`**
  - Re-deliver failed exports.
- **GET `/compliance/logs`**
  - List compliance logs.
- **POST `/compliance/logs`**
  - Create a compliance log.
- **POST `/compliance/logs/{log_id}/resolve`**
  - Resolve a compliance log.

---

### Incidents & Ops
- **GET `/incidents/`**
  - List incidents.
- **POST `/incidents/`**
  - Create a new incident.
- **POST `/incidents/{incident_id}/assign`**
  - Assign incident to user.
- **POST `/incidents/{incident_id}/escalate`**
  - Escalate incident.
- **POST `/incidents/{incident_id}/comment`**
  - Add comment to incident.

---

### Users & System
- **GET `/users/`**
  - List users.
- **GET `/system_metrics/`**
  - Get system health/metrics.

---

## Common Response Fields
- Most responses are JSON objects with status, data, and (for agentic endpoints) detailed audit fields:
  - `ai_explanation`, `agent_input`, `agent_output`, `agent_version`, `actor_type`, `is_simulation`, `override_type`, etc.

---

## OpenAPI/Swagger
- Full interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Schema: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## Notes for Frontend Integration
- All endpoints accept/return JSON.
- Use proper authentication headers/cookies for protected endpoints.
- For agentic actions, display `ai_explanation`, `rationale`, `recommendation`, and audit fields for transparency.
- For export/compliance, handle batch operations and status codes.
- See backend `/docs` for up-to-date request/response schemas and try-it-out.

---

For questions or to extend this reference, see the backend maintainers or consult the `/docs` endpoint.
