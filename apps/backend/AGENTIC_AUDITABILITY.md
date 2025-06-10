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

## Audit Logging

- All agentic and human actions are logged in `AgentActionAuditLog`.
- Each log entry captures the state transition, operator, timestamp, and full agentic context.
- SIEM/syslog events are emitted for critical actions.

---

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
