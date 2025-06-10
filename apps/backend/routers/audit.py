from fastapi import APIRouter, Depends, HTTPException
from slowapi.decorator import limiter as rate_limiter
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import AgentAction as AgentActionModel
from ..database import get_db
from ..security import require_role
from datetime import datetime
import csv
from fastapi.responses import StreamingResponse
from io import StringIO
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

router = APIRouter(prefix="/audit", tags=["audit", "export"])

@router.get("/actions", response_model=List[dict])
@rate_limiter("30/minute")  # Listing endpoint, higher limit
async def list_agent_actions(
    status: Optional[str] = None,
    action: Optional[str] = None,
    submitted_by: Optional[int] = None,
    approved_by: Optional[int] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
):
    """
    List agent actions with rich filtering for audit/review.
    """
    with tracer.start_as_current_span("audit.list_agent_actions") as span:
        span.set_attribute("user.id", getattr(user, 'id', None))
        span.set_attribute("status", status)
        span.set_attribute("action", action)
        span.set_attribute("submitted_by", submitted_by)
        span.set_attribute("approved_by", approved_by)
        span.set_attribute("start", str(start) if start else None)
        span.set_attribute("end", str(end) if end else None)
        try:
            query = db.query(AgentActionModel)
            if status:
                query = query.filter(AgentActionModel.status == status)
            if action:
                query = query.filter(AgentActionModel.action == action)
            if submitted_by:
                query = query.filter(AgentActionModel.submitted_by == submitted_by)
            if approved_by:
                query = query.filter(AgentActionModel.approved_by == approved_by)
            if start:
                query = query.filter(AgentActionModel.created_at >= start)
            if end:
                query = query.filter(AgentActionModel.created_at <= end)
            actions = query.order_by(AgentActionModel.created_at.desc()).all()
            span.set_attribute("results.count", len(actions))
            siem.send_syslog_event(
    event="Agent actions listed",
    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    extra={"user": str(user.get('id') if hasattr(user, 'id') else user)}
)
            return [a.__dict__ for a in actions]
        except Exception as e:
            span.record_exception(e)
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise

@router.get("/actions/export")
@rate_limiter("15/minute")  # Export endpoint, moderate limit
async def export_agent_actions(
    status: Optional[str] = None,
    action: Optional[str] = None,
    submitted_by: Optional[int] = None,
    approved_by: Optional[int] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    format: str = "csv",
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
):
    """
    Export agent actions as CSV or JSON for audit/review. SIEM event and digital signature included.
    """
    user_id = getattr(user, 'id', None) if hasattr(user, 'id') else None
    with tracer.start_as_current_span("export.agent_actions") as span:
        span.set_attribute("user.id", user_id)
        span.set_attribute("export.format", format)
        span.set_attribute("status", status)
        span.set_attribute("action", action)
        span.set_attribute("submitted_by", submitted_by)
        span.set_attribute("approved_by", approved_by)
        span.set_attribute("start", str(start) if start else None)
        span.set_attribute("end", str(end) if end else None)
        try:
            query = db.query(AgentActionModel)
            if status:
                query = query.filter(AgentActionModel.status == status)
            if action:
                query = query.filter(AgentActionModel.action == action)
            if submitted_by:
                query = query.filter(AgentActionModel.submitted_by == submitted_by)
            if approved_by:
                query = query.filter(AgentActionModel.approved_by == approved_by)
            if start:
                query = query.filter(AgentActionModel.created_at >= start)
            if end:
                query = query.filter(AgentActionModel.created_at <= end)
            actions = query.order_by(AgentActionModel.created_at.desc()).all()
            span.set_attribute("export.record_count", len(actions))
            if format == "csv":
                fieldnames = [c.name for c in AgentActionModel.__table__.columns]
                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for action in actions:
                    writer.writerow({fn: getattr(action, fn) for fn in fieldnames})
                output.seek(0)
                # Hash chain and sign for manual export
                from apps.backend.scheduled_exports import hash_chain_csv
                last_hash = hash_chain_csv(output.getvalue())
                signature = crypto_utils.sign_data(last_hash.encode())
                span.set_attribute("export.hash", last_hash)
                span.set_attribute("export.signature", signature.hex() if hasattr(signature, 'hex') else str(signature))
                siem.send_syslog_event(f"Agent actions manually exported, hash: {last_hash}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
                return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=agent_actions.csv"})
            else:
                siem.send_syslog_event(
    event="Agent actions manually exported (JSON)",
    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    extra={"user": str(user.get('id') if hasattr(user, 'id') else user)}
)
                return [a.__dict__ for a in actions]
        except Exception as e:
            span.record_exception(e)
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
