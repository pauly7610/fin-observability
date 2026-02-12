from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..security import require_role
from ..models import Incident as IncidentModel, IncidentActivity
from datetime import datetime, timedelta

router = APIRouter(prefix="/ops_metrics", tags=["ops_metrics"])


@router.get("/mttr")
async def get_mttr(
    days: int = 7,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "analyst", "viewer"])),
):
    """
    Mean Time To Resolve (MTTR) for incidents resolved in the last N days.
    """
    since = datetime.utcnow() - timedelta(days=days)
    incidents = (
        db.query(IncidentModel)
        .filter(IncidentModel.resolved_at != None, IncidentModel.resolved_at >= since)
        .all()
    )
    if not incidents:
        return {"mttr_hours": None, "resolved_count": 0}
    total_time = sum(
        [
            (i.resolved_at - i.created_at).total_seconds()
            for i in incidents
            if i.created_at and i.resolved_at
        ]
    )
    mttr_hours = total_time / 3600 / len(incidents)
    return {"mttr_hours": round(mttr_hours, 2), "resolved_count": len(incidents)}


@router.get("/agentic_action_rate")
async def agentic_action_rate(
    days: int = 7,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "analyst", "viewer"])),
):
    """
    Count of agentic actions (timeline events) in the last N days.
    """
    since = datetime.utcnow() - timedelta(days=days)
    count = (
        db.query(IncidentActivity)
        .filter(
            IncidentActivity.event_type.like("agentic_action%"),
            IncidentActivity.timestamp >= since,
        )
        .count()
    )
    return {"agentic_action_count": count, "days": days}


@router.get("/sla_compliance")
async def sla_compliance(
    sla_hours: int = 4,
    days: int = 7,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "analyst", "viewer"])),
):
    """
    SLA compliance: percent of incidents resolved within SLA in last N days.
    """
    since = datetime.utcnow() - timedelta(days=days)
    incidents = (
        db.query(IncidentModel)
        .filter(IncidentModel.resolved_at != None, IncidentModel.resolved_at >= since)
        .all()
    )
    if not incidents:
        return {"sla_compliance_pct": None, "resolved_count": 0}
    within_sla = [
        i
        for i in incidents
        if i.created_at
        and i.resolved_at
        and (i.resolved_at - i.created_at).total_seconds() <= sla_hours * 3600
    ]
    pct = 100 * len(within_sla) / len(incidents)
    return {
        "sla_compliance_pct": round(pct, 2),
        "resolved_count": len(incidents),
        "sla_hours": sla_hours,
    }
