from fastapi import APIRouter, Depends, HTTPException, Request, Query, Body
import logging
from apps.backend.rate_limit import limiter
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import Incident as IncidentModel
from ..database import get_db
from ..security import require_role
from datetime import datetime
import csv
from fastapi.responses import StreamingResponse
from io import StringIO
import os
from apps.backend import siem, crypto_utils
from apps.backend.scheduled_exports import hash_chain_csv
from opentelemetry import trace
import json
from apps.backend.broadcast import incident_broadcaster
tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents", "export"])


# --- Agentic API (for IncidentTriageAgent) ---
@router.post("/analyze")
async def analyze_incident(
    body: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "analyst", "compliance", "viewer"])),
):
    """Analyze incident and return severity/impact/risk. Used by IncidentTriageAgent."""
    from apps.backend.services.agent_service import AgenticTriageService
    incident = body.get("incident", body)
    result = AgenticTriageService().triage_incident(incident)
    return {"result": result, "severity": result.get("risk_level"), "impact_areas": ["transactions", "compliance"], "risk_score": result.get("confidence", 0)}


@router.post("/similar")
async def get_similar_incidents(
    body: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "analyst", "compliance", "viewer"])),
):
    """Find similar incidents by type/desk/severity. Used by IncidentTriageAgent."""
    incident = body.get("incident", body)
    limit = body.get("limit", 5)
    query = db.query(IncidentModel)
    if incident.get("type"):
        query = query.filter(IncidentModel.type == incident["type"])
    if incident.get("desk"):
        query = query.filter(IncidentModel.desk == incident["desk"])
    if incident.get("severity"):
        query = query.filter(IncidentModel.severity == incident["severity"])
    incidents = query.order_by(IncidentModel.created_at.desc()).limit(limit).all()
    return {"similar": [_incident_to_dict(inc) for inc in incidents]}


@router.post("/remediation")
async def suggest_remediation(
    body: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "analyst", "compliance", "viewer"])),
):
    """Suggest remediation steps. Used by IncidentTriageAgent."""
    from apps.backend.services.incident_remediation_service import IncidentRemediationService
    incident = body.get("incident", body)
    result = IncidentRemediationService().remediate_incident(incident)
    steps = []
    if result.get("recommendation"):
        steps.append({"step": 1, "action": result["recommendation"], "priority": result.get("risk_level", "high"), "estimated_time": "15 minutes"})
    return {"result": result, "steps": steps if steps else [{"step": 1, "action": "Manual review required", "priority": "high", "estimated_time": "N/A"}]}


@router.get("/{incident_id}/agentic/suggestions")
async def get_agentic_suggestions(incident_id: str, db: Session = Depends(get_db), user=Depends(require_role(["admin", "analyst", "compliance", "viewer"]))):
    from apps.backend.models import Incident as IncidentModel
    from apps.backend.services.agentic_service import get_agentic_suggestions
    incident = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    # Convert to dict for agentic_service
    incident_dict = {c.name: getattr(incident, c.name) for c in IncidentModel.__table__.columns}
    return get_agentic_suggestions(incident_dict)

@router.post("/{incident_id}/agentic/execute")
async def execute_agentic_action(incident_id: str, action_type: str, parameters: dict = None, db: Session = Depends(get_db), user=Depends(require_role(["admin", "analyst"]))):
    from apps.backend.services.agentic_service import execute_agentic_action
    from apps.backend.services.incident_activity_service import record_incident_activity
    # Trigger agentic action (simulate)
    task_id = execute_agentic_action(incident_id, action_type, parameters)
    # Record timeline event for agentic action started
    record_incident_activity(
        db=db,
        incident_id=incident_id,
        event_type="agentic_action_started",
        user_id=getattr(user, 'id', None),
        comment=f"Agentic action '{action_type}' started.",
        meta={"task_id": task_id, "parameters": parameters}
    )
    return {"task_id": task_id, "status": "running"}

@router.patch("/{incident_id}/status")
async def update_incident_status(
    incident_id: str,
    body: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "analyst", "compliance"])),
):
    """Update incident status. Used by IncidentTriageAgent."""
    from apps.backend.services.incident_activity_service import record_incident_activity
    incident = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    new_status = body.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Missing 'status' in body")
    old_status = incident.status
    incident.status = new_status
    if new_status == "resolved":
        incident.resolved_at = datetime.utcnow()
    incident.updated_at = datetime.utcnow()
    db.commit()
    record_incident_activity(
        db=db,
        incident_id=incident_id,
        event_type="status_change",
        user_id=getattr(user, "id", None),
        old_value=old_status,
        new_value=new_status,
        comment=body.get("notes"),
    )
    return {"incident_id": incident_id, "status": new_status, "updated_at": incident.updated_at.isoformat(), "notes": body.get("notes")}


@router.get("/{incident_id}/agentic/status/{task_id}")
async def get_agentic_action_status(incident_id: str, task_id: str, db: Session = Depends(get_db), user=Depends(require_role(["admin", "analyst", "compliance", "viewer"]))):
    from apps.backend.services.agentic_service import get_agentic_action_status
    from apps.backend.services.incident_activity_service import record_incident_activity
    status = get_agentic_action_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Agentic action not found")
    # If just finished, log to timeline
    if status["status"] == "succeeded" and not status.get("timeline_logged"):
        record_incident_activity(
            db=db,
            incident_id=incident_id,
            event_type="agentic_action_finished",
            user_id=None,  # System
            comment=f"Agentic action '{status['action_type']}' finished.",
            meta={"task_id": task_id, "result": status["result"]}
        )
        status["timeline_logged"] = True
    return status

@router.get("/{incident_id}/timeline")
async def get_incident_timeline(
    incident_id: str,
    offset: int = Query(0, ge=0, description="Pagination offset (default 0)"),
    limit: int = Query(50, ge=1, le=200, description="Max results per page (default 50, max 200)"),
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "analyst", "compliance"]))
):
    """
    Return a unified, chronological timeline of all actions and comments for an incident.
    Supports offset/limit pagination for high-velocity ops.
    """
    from apps.backend.models import IncidentActivity
    total = db.query(IncidentActivity).filter(IncidentActivity.incident_id == incident_id).count()
    activities = (
        db.query(IncidentActivity)
        .filter(IncidentActivity.incident_id == incident_id)
        .order_by(IncidentActivity.timestamp.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": [
            {
                "id": a.id,
                "event_type": a.event_type,
                "user_id": a.user_id,
                "old_value": a.old_value,
                "new_value": a.new_value,
                "comment": a.comment,
                "meta": a.meta,
                "timestamp": a.timestamp,
            }
            for a in activities
        ]
    }

# --- Notification ---
def notify_ops_team(incident):
    """Notify ops team via Slack/webhook for high-priority incidents."""
    from apps.backend.services.notification_service import send_incident_notification
    send_incident_notification(incident)

# --- Enhanced GET /incidents ---
def _incident_to_dict(inc):
    """Convert Incident ORM to JSON-serializable dict."""
    d = {}
    for c in IncidentModel.__table__.columns:
        val = getattr(inc, c.name)
        if hasattr(val, "isoformat"):
            d[c.name] = val.isoformat() if val else None
        else:
            d[c.name] = val
    return d


@router.get("/")
async def list_incidents(
    type: Optional[str] = None,
    desk: Optional[str] = None,
    trader: Optional[str] = None,
    priority: Optional[int] = None,
    root_cause: Optional[str] = None,
    detection_method: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    assigned_to: Optional[int] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance", "analyst", "viewer"])),
):
    """List incidents with optional filters. Returns { incidents: [...] }."""
    try:
        query = db.query(IncidentModel)
        if type:
            query = query.filter(IncidentModel.type == type)
        if desk:
            query = query.filter(IncidentModel.desk == desk)
        if trader:
            query = query.filter(IncidentModel.trader == trader)
        if priority is not None:
            query = query.filter(IncidentModel.priority == priority)
        if root_cause:
            query = query.filter(IncidentModel.root_cause == root_cause)
        if detection_method:
            query = query.filter(IncidentModel.detection_method == detection_method)
        if status:
            query = query.filter(IncidentModel.status == status)
        if severity:
            query = query.filter(IncidentModel.severity == severity)
        if assigned_to:
            query = query.filter(IncidentModel.assigned_to == assigned_to)
        if start:
            from dateutil.parser import parse
            query = query.filter(IncidentModel.created_at >= parse(start))
        if end:
            from dateutil.parser import parse
            query = query.filter(IncidentModel.created_at <= parse(end))
        incidents = query.order_by(IncidentModel.created_at.desc()).all()
        return {"incidents": [_incident_to_dict(inc) for inc in incidents]}
    except Exception as e:
        logger.error(f"Database query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- 1-Click Ops Actions ---

from fastapi import Body

@router.post("/bulk/resolve")
async def bulk_resolve_incidents(
    incident_ids: List[str] = Body(..., embed=True, description="List of incident IDs to resolve."),
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "analyst"]))
):
    """
    Bulk resolve incidents. Marks all as resolved, logs each, broadcasts updates.
    """
    from apps.backend.services.incident_activity_service import record_incident_activity
    results = []
    for incident_id in incident_ids:
        incident = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
        if not incident or incident.status == "resolved":
            results.append({"incident_id": incident_id, "status": "skipped"})
            continue
        old_status = incident.status
        incident.status = "resolved"
        incident.resolved_at = datetime.utcnow()
        db.commit()
        record_incident_activity(
            db=db,
            incident_id=incident_id,
            event_type="status_change",
            user_id=getattr(user, 'id', None),
            old_value=old_status,
            new_value="resolved"
        )
        import asyncio
        asyncio.create_task(incident_broadcaster.broadcast(json.dumps({c.name: getattr(incident, c.name) for c in IncidentModel.__table__.columns})))
        results.append({"incident_id": incident_id, "status": "resolved"})
    return {"results": results}

@router.post("/bulk/escalate")
async def bulk_escalate_incidents(
    incident_ids: List[str] = Body(..., embed=True, description="List of incident IDs to escalate."),
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "analyst"]))
):
    """
    Bulk escalate incidents. Marks all as escalated, logs each, broadcasts updates.
    """
    from apps.backend.services.incident_activity_service import record_incident_activity
    results = []
    for incident_id in incident_ids:
        incident = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
        if not incident or incident.status == "escalated":
            results.append({"incident_id": incident_id, "status": "skipped"})
            continue
        old_status = incident.status
        incident.status = "escalated"
        db.commit()
        record_incident_activity(
            db=db,
            incident_id=incident_id,
            event_type="status_change",
            user_id=getattr(user, 'id', None),
            old_value=old_status,
            new_value="escalated"
        )
        import asyncio
        asyncio.create_task(incident_broadcaster.broadcast(json.dumps({c.name: getattr(incident, c.name) for c in IncidentModel.__table__.columns})))
        results.append({"incident_id": incident_id, "status": "escalated"})
    return {"results": results}

@router.post("/bulk/assign")
async def bulk_assign_incidents(
    incident_ids: List[str] = Body(..., embed=True, description="List of incident IDs to assign."),
    assigned_to: int = Body(..., embed=True, description="User ID to assign to."),
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "analyst"]))
):
    """
    Bulk assign incidents to a user. Logs each, broadcasts updates.
    """
    from apps.backend.services.incident_activity_service import record_incident_activity
    results = []
    for incident_id in incident_ids:
        incident = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
        if not incident:
            results.append({"incident_id": incident_id, "status": "skipped"})
            continue
        old_assigned = getattr(incident, "assigned_to", None)
        incident.assigned_to = assigned_to
        db.commit()
        record_incident_activity(
            db=db,
            incident_id=incident_id,
            event_type="assignment",
            user_id=getattr(user, 'id', None),
            old_value=str(old_assigned),
            new_value=str(assigned_to)
        )
        import asyncio
        asyncio.create_task(incident_broadcaster.broadcast(json.dumps({c.name: getattr(incident, c.name) for c in IncidentModel.__table__.columns})))
        results.append({"incident_id": incident_id, "status": "assigned", "assigned_to": assigned_to})
    return {"results": results}

@router.post("/bulk/triage")
async def bulk_triage_incidents(
    incident_ids: List[str] = Body(..., embed=True, description="List of incident IDs to triage."),
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "analyst"]))
):
    """
    Bulk triage incidents (stub: marks as 'triaged', logs, broadcasts). Extend as needed.
    """
    from apps.backend.services.incident_activity_service import record_incident_activity
    results = []
    for incident_id in incident_ids:
        incident = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
        if not incident or getattr(incident, "status", None) == "triaged":
            results.append({"incident_id": incident_id, "status": "skipped"})
            continue
        old_status = incident.status
        incident.status = "triaged"
        db.commit()
        record_incident_activity(
            db=db,
            incident_id=incident_id,
            event_type="status_change",
            user_id=getattr(user, 'id', None),
            old_value=old_status,
            new_value="triaged"
        )
        import asyncio
        asyncio.create_task(incident_broadcaster.broadcast(json.dumps({c.name: getattr(incident, c.name) for c in IncidentModel.__table__.columns})))
        results.append({"incident_id": incident_id, "status": "triaged"})
    return {"results": results}

@router.post("/{incident_id}/resolve")
async def resolve_incident(incident_id: str, db: Session = Depends(get_db), user=Depends(require_role(["admin", "analyst"]))):
    from apps.backend.services.incident_activity_service import record_incident_activity
    incident = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    old_status = incident.status
    incident.status = "resolved"
    incident.resolved_at = datetime.utcnow()
    db.commit()
    # Record activity
    record_incident_activity(
        db=db,
        incident_id=incident_id,
        event_type="status_change",
        user_id=getattr(user, 'id', None),
        old_value=old_status,
        new_value="resolved"
    )
    # Broadcast update
    import asyncio
    asyncio.create_task(incident_broadcaster.broadcast(json.dumps({c.name: getattr(incident, c.name) for c in IncidentModel.__table__.columns})))
    return {"detail": "Incident resolved", "incident_id": incident_id}

@router.post("/{incident_id}/escalate")
async def escalate_incident(incident_id: str, db: Session = Depends(get_db), user=Depends(require_role(["admin", "analyst"]))):
    from apps.backend.services.incident_activity_service import record_incident_activity
    incident = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    old_status = incident.status
    incident.status = "escalated"
    db.commit()
    # Record activity
    record_incident_activity(
        db=db,
        incident_id=incident_id,
        event_type="status_change",
        user_id=getattr(user, 'id', None),
        old_value=old_status,
        new_value="escalated"
    )
    # Broadcast update
    import asyncio
    asyncio.create_task(incident_broadcaster.broadcast(json.dumps({c.name: getattr(incident, c.name) for c in IncidentModel.__table__.columns})))
    notify_ops_team(incident)
    return {"detail": "Incident escalated", "incident_id": incident_id}

@router.post("/{incident_id}/assign")
async def assign_incident(incident_id: str, assigned_to: int, db: Session = Depends(get_db), user=Depends(require_role(["admin", "analyst"]))):
    from apps.backend.services.incident_activity_service import record_incident_activity
    incident = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    old_assigned = incident.assigned_to
    incident.assigned_to = assigned_to
    db.commit()
    # Record activity
    record_incident_activity(
        db=db,
        incident_id=incident_id,
        event_type="assignment",
        user_id=getattr(user, 'id', None),
        old_value=str(old_assigned) if old_assigned is not None else None,
        new_value=str(assigned_to)
    )
    # Broadcast update
    import asyncio
    asyncio.create_task(incident_broadcaster.broadcast(json.dumps({c.name: getattr(incident, c.name) for c in IncidentModel.__table__.columns})))
    return {"detail": "Incident assigned", "incident_id": incident_id, "assigned_to": assigned_to}

@router.post("/{incident_id}/comment")
async def comment_incident(incident_id: str, comment: str, db: Session = Depends(get_db), user=Depends(require_role(["admin", "analyst"]))):
    from apps.backend.services.incident_activity_service import record_incident_activity
    incident = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    # Record comment as an IncidentActivity
    record_incident_activity(
        db=db,
        incident_id=incident_id,
        event_type='comment',
        user_id=getattr(user, 'id', None),
        comment=comment
    )
    # Broadcast update for real-time UI
    import asyncio
    asyncio.create_task(incident_broadcaster.broadcast(json.dumps({c.name: getattr(incident, c.name) for c in IncidentModel.__table__.columns})))
    return {"detail": "Comment added", "incident_id": incident_id}

# --- Export Incidents Endpoint (Restored) ---
@router.get("/export")
@limiter.limit("15/minute")  # Export endpoint, moderate limit
async def export_incidents(request: Request,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    assigned_to: Optional[int] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    format: str = "csv",
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
):
    """
    Export incidents as CSV or JSON for audit/review. SIEM event and digital signature included.
    """
    user_id = getattr(user, 'id', None) if hasattr(user, 'id') else None
    # Approval workflow integration
    from apps.backend.approval import require_approval
    approved, approval_req = require_approval(
        db=db,
        resource_type="incident_export",
        resource_id=f"incidents_{status}_{severity}_{assigned_to}_{start}_{end}",
        user_id=user_id,
        reason="Export incidents for audit/review",
        meta={"status": status, "severity": severity, "assigned_to": assigned_to, "start": start, "end": end}
    )
    if not approved:
        # Block export, return approval pending info
        return {"detail": "Export requires approval", "approval_request_id": approval_req.id, "status": approval_req.status.value}
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("export.incidents") as span:
        span.set_attribute("user.id", user_id)
        span.set_attribute("export.format", format)
        span.set_attribute("status", status)
        span.set_attribute("severity", severity)
        span.set_attribute("assigned_to", assigned_to)
        span.set_attribute("start", str(start) if start else None)
        span.set_attribute("end", str(end) if end else None)
        try:
            query = db.query(IncidentModel)
            if status:
                query = query.filter(IncidentModel.status == status)
            if severity:
                query = query.filter(IncidentModel.severity == severity)
            if assigned_to:
                query = query.filter(IncidentModel.assigned_to == assigned_to)
            if start:
                from dateutil.parser import parse
                query = query.filter(IncidentModel.created_at >= parse(start))
            if end:
                from dateutil.parser import parse
                query = query.filter(IncidentModel.created_at <= parse(end))
            incidents = query.order_by(IncidentModel.created_at.desc()).all()
            span.set_attribute("export.record_count", len(incidents))
            if format == "csv":
                import csv
                from fastapi.responses import StreamingResponse
                from io import StringIO
                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=[c.name for c in IncidentModel.__table__.columns])
                writer.writeheader()
                for inc in incidents:
                    writer.writerow({c.name: getattr(inc, c.name) for c in IncidentModel.__table__.columns})
                output.seek(0)
                import os
                from apps.backend import siem
                siem.send_syslog_event(
                    event="Incidents exported as CSV",
                    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
                    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
                    extra={"count": len(incidents), "user": str(getattr(user, "id", None) or user)},
                )
                return StreamingResponse(
                    iter([output.getvalue()]),
                    media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=incidents.csv"},
                )
        except Exception as e:
            span.record_exception(e)
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))
