from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import AgentAction as AgentActionModel
from ..database import get_db
from ..security import require_role
from datetime import datetime
import csv
from fastapi.responses import StreamingResponse
from io import StringIO

router = APIRouter(prefix="/audit", tags=["audit", "export"])

@router.get("/actions", response_model=List[dict])
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
    siem.send_syslog_event(f"Agent actions listed", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
    return [a.__dict__ for a in actions]

@router.get("/actions/export")
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
        siem.send_syslog_event(f"Agent actions manually exported, hash: {last_hash}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=agent_actions.csv"})
    else:
        siem.send_syslog_event(f"Agent actions manually exported (JSON)", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
        return [a.__dict__ for a in actions]
