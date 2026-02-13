# Agentic Auditability & Compliance Documentation

## Purpose

This document details the agentic auditability enhancements and compliance features in the backend. It is intended for developers, auditors, and compliance officers.

---

## Agentic Audit Fields

Every `AgentAction` and `AgentActionAuditLog` record includes:

- **ai_explanation**: Reasoning or explanation from the agent/AI for the action taken.
- **agent_input**: The full input payload provided to the agent/AI.
- **agent_output**: The complete output (including recommendations, confidence, rationale, etc.).
- **agent_version**: The version or identifier of the agent/AI/model.
- **actor_type**: Indicates the actor ('agent', 'human', or 'system').
- **override_type**: Type of override, e.g., 'ai_override', 'manual_override'.
- **is_simulation**: Boolean flag for simulation/test actions.

These fields are critical for:

- **Explainability**: Understanding why and how an agentic decision was made.
- **Traceability**: Tracking every override, escalation, or human intervention.
- **Attribution**: Distinguishing between agentic, human, and system actors.
- **Audit/Compliance**: Satisfying regulatory and operational transparency requirements.

---

## Unified Audit Trail (`audit_trail` table)

- A canonical, append-only `audit_trail` table records every auditable event.
- Event types: `incident_status_change`, `agent_action_proposed`, `agent_action_approved`, `transaction_scored`, `compliance_monitor_decision`, `export_initiated`, `approval_decided`, etc.
- Each entry includes: `event_type`, `entity_type`, `entity_id`, `actor_type`, `summary`, `regulation_tags` (SEC_17a4, FINRA_4511).
- API: `GET /api/audit_trail` (with filters: entity_type, event_type, regulation_tag, start, end); `GET /api/audit_trail/export?format=csv|json`. Export responses include `X-Content-SHA256` header (SHA-256 of body) for WORM-compliant verification.
- Recording points: incident activity, agent ops, compliance monitor, transaction scoring, exports, approvals.

## PII Sanitization

- **Before storage:** `details` and `meta` are sanitized via `hash_pii_in_dict` when `PII_HASH_ENABLED=true`.
- **Detection:** Field-name match (known PII fields) plus value-based regex (email, SSN, credit card, phone, IP) so unknown fields like `{"unknown_field": "john@example.com"}` are hashed.
- **Allowlist:** Fields such as `amount`, `id`, `transaction_id`, `confidence`, `anomaly_score`, `status`, `action`, `decision`, `timestamp`, `model_version` are never hashed.
- **Idempotency:** Values already prefixed with `pii:` are not double-hashed.
- **Env:** `PII_HASH_SALT` (deterministic hashing), `PII_HASH_ENABLED` (default true).

## Retention Policy

- **Retention period:** 7 years for compliance-relevant events, per SEC 17a-4.
- **Criteria:** Entries with `regulation_tags` including `SEC_17a4` or `FINRA_4511` are subject to retention. All `entity_type` values (incident, agent_action, transaction, export, compliance_log, approval) are in scope.
- **Env-driven retention:** `AUDIT_RETENTION_YEARS` (default 7) configures the retention window.
- **Archival script:** Run `python scripts/archive_audit_trail.py` to delete entries older than retention. Use `--dry-run` to report count without deleting. Schedule via cron for periodic archival.

## Audit Logging

- All agentic and human actions are logged in `AgentActionAuditLog`.
- Each log entry captures the state transition, operator, timestamp, and full
  agentic context.
- SIEM/syslog events are emitted for critical actions.

---

## Approval Workflow & Audit Trail Integration

- All approval requests and decisions are recorded in the audit trail for full
  compliance and traceability.
- Each approval or rejection decision logs the decider, timestamp, and decision
  reason (if provided).
- Approval actions are surfaced in both the backend and frontend audit UIs,
  highlighted for easy compliance review.
- SIEM/syslog integration ensures all approval events are available for
  external monitoring and audit.

## Example: Agentic Action Lifecycle

1. **Agent/AI proposes an action**
   - Fields: `actor_type='agent'`, `ai_explanation`, `agent_input`, `agent_output`, `agent_version`, `is_simulation` as appropriate.
2. **Human reviews and overrides**
   - Fields: `actor_type='human'`, `override_type='manual_override'`.
3. **Every step is audit-logged**
   - `AgentActionAuditLog` records all state changes with full agentic context.

---

## Export Metadata & Verification

- Every export is tracked in `ExportMetadata` with:
  - Hash, signature, delivery/verification status, and full lifecycle timestamps.
- Batch verification and re-delivery endpoints allow compliance teams to verify export integrity and trigger re-delivery as needed.

---

## Security & RBAC

- All sensitive endpoints require `admin` or `compliance` role.
- All actions and overrides are attributed to a user or agent.

---

## Database Migration

- Alembic migrations ensure schema is always up to date with audit fields.
- See `alembic/` for migration scripts.

---

## References

- See `README.md` for backend setup and API usage.
- See `schemas.py` and `models.py` for field definitions.
- See `routers/agent.py` and `routers/ops.py` for endpoint logic.

---

## Contact

For compliance or audit questions, contact the backend engineering team or compliance lead.
