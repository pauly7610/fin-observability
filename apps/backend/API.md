# Backend API Reference

This document provides a concise reference for the main backend API endpoints. For full details and live testing, see the `/docs` (Swagger UI) endpoint on your running backend.

> **Live:** https://fin-observability-production.up.railway.app/docs

---

## Authentication

- **RBAC** enforced via `require_role` / `require_permission` dependencies on sensitive endpoints.
- Roles: `admin`, `compliance`, `analyst`, `viewer` (25 fine-grained permissions).
- Auth headers: `x-user-email` + `x-user-role`, or `Authorization: Bearer <token>`.
- Webhook auth: `X-Webhook-Key` header or `?key=` query param (set `WEBHOOK_API_KEY` env var).

---

## MCP Server (Model Context Protocol)

AI agents connect via MCP at `/mcp` (Streamable HTTP transport).

- **GET `/mcp/tools`** — List all available MCP tools with descriptions and parameters.
- **GET `/mcp/stats`** — Aggregated MCP usage statistics (calls, latency, errors per tool).

### MCP Tools (9 total)

| Tool | Description |
|------|-------------|
| `check_transaction_compliance` | Score a transaction — approve/review decision, anomaly score, risk factors |
| `explain_transaction` | SHAP-based feature importance for a prediction |
| `batch_check_compliance` | Score up to 10,000 transactions in one call |
| `analyze_portfolio` | Aggregate risk: distribution, top flagged, concentration warnings (up to 10K) |
| `ingest_transactions` | Push up to 10,000 transactions for scoring + storage |
| `get_compliance_metrics` | Real-time approval rates, confidence scores, model info |
| `list_incidents` | Browse incidents with status/severity filters |
| `get_drift_status` | PSI + KS test results and retrain recommendations |
| `get_model_leaderboard` | Model versions ranked by F1 score |

---

## Webhook & Streaming System

All webhook endpoints are prefixed with `/webhooks`. Auth via `X-Webhook-Key` header.

### Inbound Ingestion

- **POST `/webhooks/transactions`**
  - Ingest single or batch transactions (up to 10,000). Each is scored by the ML compliance engine and stored.
  - **Body:** Single object `{"amount": 5000, "type": "wire"}` or array `[{...}, {...}]`
  - **Returns:** `{ "ingested": N, "flagged": N, "total_amount": N, "results": [...] }`

- **GET `/webhooks/results`**
  - Retrieve previously scored results.
  - **Params:** `source` (webhook/mcp/api), `flagged_only` (bool), `limit` (max 200)

### SSE Real-Time Stream

- **GET `/webhooks/stream`**
  - Server-Sent Events feed of every compliance decision in real-time. Replays last 50 events on connect, then streams live with 30s keepalive.

- **GET `/webhooks/stream/status`**
  - Returns subscriber count and recent event count.

### Outbound Notifications (Callbacks)

- **POST `/webhooks/callbacks`**
  - Register a callback URL. Flagged transactions are POSTed with 3x retry + exponential backoff.
  - **Body:** `{ "url": "https://your-service.com/webhook" }`

- **DELETE `/webhooks/callbacks`**
  - Remove a callback URL. **Body:** `{ "url": "https://..." }`

- **GET `/webhooks/callbacks`**
  - List registered callbacks + recent delivery log.

- **GET `/webhooks/callbacks/dlq`**
  - Dead letter queue — failed deliveries that exhausted all retries.

### Scheduled Pull Ingestion

- **POST `/webhooks/pull/sources`**
  - Add an external API source for scheduled polling.
  - **Body:** `{ "name": "plaid", "url": "https://...", "headers": {...}, "interval_seconds": 300 }`

- **GET `/webhooks/pull/sources`**
  - List configured sources (headers redacted) + recent pull results.

- **POST `/webhooks/pull/trigger/{source_id}`**
  - Manually trigger a pull from a specific source.

- **DELETE `/webhooks/pull/sources/{source_id}`**
  - Remove a pull source.

### System Status

- **GET `/webhooks/status`**
  - Full overview: SSE subscribers, callback count, DLQ size, pull sources.

---

## ML & Compliance Endpoints

### Compliance Monitoring
- **POST `/agent/compliance/monitor`** — Score a transaction via the ML ensemble.
- **GET `/agent/compliance/status`** — Current compliance engine status.
- **GET `/agent/compliance/metrics`** — Approval rates, confidence scores, model info.
- **POST `/agent/compliance/explain`** — SHAP explainability for a transaction.
- **POST `/agent/compliance/ensemble`** — Ensemble scoring (IF + Autoencoder).

### Drift Detection & Retraining
- **GET `/agent/compliance/drift/status`** — PSI + KS test results.
- **POST `/agent/compliance/drift/check`** — Trigger a drift check.
- **POST `/agent/compliance/retrain/drift`** — Trigger drift-based retraining.
- **GET `/agent/compliance/retrain/status`** — Retraining pipeline status.

### Experiments & Evaluation
- **GET `/agent/compliance/experiments`** — A/B test results.
- **GET `/agent/compliance/eval/results`** — Evaluation results.
- **GET `/agent/compliance/eval/leaderboard`** — Model leaderboard by F1 score.

---

## Agentic Workflow

- **POST `/agent/triage`** — Triage an incident with agentic explainability.
- **POST `/agent/remediate`** — Run agentic remediation.
- **POST `/agent/automate_compliance`** — Automate compliance check.
- **POST `/agent/audit_summary`** — Summarize audit logs.

### Human Oversight
- **POST `/agent/actions/{action_id}/approve`** — Approve a pending agent action.
- **POST `/agent/actions/{action_id}/reject`** — Reject a pending agent action.

---

## Approval Workflow

- **GET `/approval/?status=pending|approved|rejected`** — List approval requests.
- **POST `/approval/{approval_id}/decision`** — Submit approval/rejection decision.

---

## Export & Compliance

- **GET `/export_metadata/`** — List export jobs and statuses.
- **POST `/export_metadata/verify_batch`** — Batch verify export hashes.
- **POST `/export_metadata/redeliver_batch`** — Re-deliver failed exports.
- **GET `/compliance/logs`** — List compliance logs.
- **POST `/compliance/logs`** — Create a compliance log.
- **POST `/compliance/logs/{log_id}/resolve`** — Resolve a compliance log.

---

## Incidents & Ops

- **GET `/incidents/`** — List incidents.
- **POST `/incidents/`** — Create a new incident.
- **POST `/incidents/{incident_id}/assign`** — Assign incident to user.
- **POST `/incidents/{incident_id}/escalate`** — Escalate incident.
- **POST `/incidents/{incident_id}/comment`** — Add comment to incident.

---

## RBAC & Auth

- **GET `/auth/roles`** — List available roles and permissions.
- **PUT `/auth/users/{id}/role`** — Update a user's role.
- **PUT `/auth/users/{id}/deactivate`** — Deactivate a user.
- **GET `/auth/me/permissions`** — Get current user's permissions.

---

## Users & System

- **GET `/users/`** — List users.
- **GET `/system_metrics/`** — Get system health/metrics.
- **GET `/health`** — Health check.

---

## OpenAPI/Swagger

- Full interactive docs: [/docs](https://fin-observability-production.up.railway.app/docs)
- Schema: [/openapi.json](https://fin-observability-production.up.railway.app/openapi.json)

---

For questions or to extend this reference, consult the `/docs` endpoint.
