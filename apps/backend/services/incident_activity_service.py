from sqlalchemy.orm import Session
from apps.backend.models import IncidentActivity
from datetime import datetime
from typing import Optional, Dict, Any

from .audit_trail_service import record_audit_event

_INCIDENT_EVENT_MAP = {
    "status_change": ("incident_status_change", ["SEC_17a4", "FINRA_4511"]),
    "assignment": ("incident_assignment", ["FINRA_4511"]),
    "comment": ("incident_comment", ["FINRA_4511"]),
    "agentic_action_started": ("incident_agentic_started", ["FINRA_4511"]),
    "agentic_action_finished": ("incident_agentic_finished", ["FINRA_4511"]),
}


def record_incident_activity(
    db: Session,
    incident_id: str,
    event_type: str,
    user_id: Optional[int] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    comment: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    timestamp: Optional[datetime] = None,
) -> IncidentActivity:
    """
    Create and persist an IncidentActivity record for the unified incident timeline/audit trail.

    Args:
        db: SQLAlchemy session.
        incident_id: The unique incident identifier.
        event_type: The type of event (e.g., 'status_change', 'assignment', 'comment').
        user_id: The user responsible for the event (optional).
        old_value: Previous value (optional).
        new_value: New value (optional).
        comment: Human-readable comment (optional).
        meta: Additional metadata (optional).
        timestamp: Timestamp of the event (optional, defaults to now).
    Returns:
        The created IncidentActivity object (persisted).
    """
    activity = IncidentActivity(
        incident_id=incident_id,
        event_type=event_type,
        user_id=user_id,
        old_value=old_value,
        new_value=new_value,
        comment=comment,
        meta=meta,
        timestamp=timestamp or datetime.utcnow(),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    # Record to unified audit trail
    mapped = _INCIDENT_EVENT_MAP.get(event_type)
    if mapped:
        audit_event_type, regulation_tags = mapped
        if audit_event_type == "incident_status_change" and new_value == "escalated":
            audit_event_type, regulation_tags = "incident_escalation", ["SEC_17a4"]
        summary = comment or (f"{old_value or ''} → {new_value or ''}" if (old_value or new_value) else event_type.replace("_", " ").title())
        try:
            record_audit_event(
                db=db,
                event_type=audit_event_type,
                entity_type="incident",
                entity_id=incident_id,
                actor_type="human" if user_id else "system",
                actor_id=user_id,
                summary=summary[:500] if summary else audit_event_type.replace("_", " ").title(),
                details={"old_value": old_value, "new_value": new_value, "comment": comment},
                regulation_tags=regulation_tags,
                meta=meta,
            )
        except Exception:
            pass  # Do not fail incident activity if audit trail write fails
    return activity


# --- Future extension: async/batch logging stub ---
async def record_incident_activity_async(
    db: Session,
    incident_id: str,
    event_type: str,
    user_id: Optional[int] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    comment: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    timestamp: Optional[datetime] = None,
) -> IncidentActivity:
    """
    Async stub for future high-throughput or streaming audit logging.
    Currently just calls the sync version.
    """
    # In a real async context, use an async DB session or queue for logging
    return record_incident_activity(
        db=db,
        incident_id=incident_id,
        event_type=event_type,
        user_id=user_id,
        old_value=old_value,
        new_value=new_value,
        comment=comment,
        meta=meta,
        timestamp=timestamp,
    )
