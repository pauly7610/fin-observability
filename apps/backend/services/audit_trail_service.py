"""
Central audit trail service for compliance (SEC 17a-4, FINRA 4511).
Every auditable event records here via record_audit_event.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models import AuditTrailEntry
from ..pii_utils import PII_HASH_ENABLED, hash_pii_in_dict

_logger = logging.getLogger(__name__)


def record_audit_event(
    db: Session,
    event_type: str,
    entity_type: str,
    entity_id: Optional[str],
    actor_type: str,
    summary: str,
    actor_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    regulation_tags: Optional[List[str]] = None,
    parent_audit_id: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
    timestamp: Optional[datetime] = None,
) -> AuditTrailEntry:
    """
    Append an audit trail entry. Append-only; no UPDATE/DELETE.

    Args:
        db: SQLAlchemy session.
        event_type: Canonical event type (e.g. compliance_monitor_decision).
        entity_type: incident, agent_action, transaction, export, compliance_log, approval.
        entity_id: ID of the entity (incident_id, transaction_id, etc.).
        actor_type: agent, human, or system.
        summary: One-line human-readable summary.
        actor_id: User ID when actor_type=human; None for agent/system.
        details: Full context (ai_explanation, risk_factors, etc.).
        regulation_tags: e.g. ["SEC_17a4", "FINRA_4511"].
        parent_audit_id: Optional; links to prior event for traceability.
        meta: Extensible metadata.
        timestamp: Event time; defaults to now.

    Returns:
        The created AuditTrailEntry, or None on failure.
    """
    details_to_store = details
    meta_to_store = meta
    if PII_HASH_ENABLED:
        if details is not None:
            details_to_store, _ = hash_pii_in_dict(details)
        if meta is not None:
            meta_to_store, _ = hash_pii_in_dict(meta)

    try:
        entry = AuditTrailEntry(
            timestamp=timestamp or datetime.utcnow(),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_type=actor_type,
            actor_id=actor_id,
            summary=summary,
            details=details_to_store,
            regulation_tags=regulation_tags or [],
            parent_audit_id=parent_audit_id,
            meta=meta_to_store,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    except Exception as e:
        db.rollback()
        _logger.error(
            "audit_trail_write_failed",
            extra={
                "event_type": event_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "error": str(e),
            },
        )
        try:
            from ..telemetry import audit_trail_write_failures_counter
            if audit_trail_write_failures_counter is not None:
                audit_trail_write_failures_counter.add(
                    1,
                    {"event_type": event_type, "entity_type": entity_type or "unknown"},
                )
        except Exception:
            pass
        return None
