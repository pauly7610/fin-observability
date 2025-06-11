from sqlalchemy.orm import Session
from apps.backend.models import IncidentActivity
from datetime import datetime
from typing import Optional, Dict, Any


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
