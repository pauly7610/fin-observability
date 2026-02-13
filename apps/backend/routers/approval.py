from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from ..approval import ApprovalRequest, ApprovalStatus
from .users import get_db, get_current_user

router = APIRouter()


@router.post("/approval/", response_model=None)
def submit_approval(
    resource_type: str,
    resource_id: str,
    reason: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    req = ApprovalRequest(
        resource_type=resource_type,
        resource_id=resource_id,
        reason=reason,
        requested_by=user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    try:
        from ..services.audit_trail_service import record_audit_event
        record_audit_event(
            db=db,
            event_type="approval_requested",
            entity_type="approval",
            entity_id=str(req.id),
            actor_type="human",
            actor_id=user.id,
            summary=f"Approval requested for {resource_type}/{resource_id}",
            details={"reason": reason},
            regulation_tags=["FINRA_4511"],
        )
    except Exception:
        pass
    return {"id": req.id, "resource_type": req.resource_type, "resource_id": req.resource_id, "status": req.status.value, "reason": req.reason}


@router.get("/approval/")
def list_approvals(
    status: Optional[ApprovalStatus] = None, db: Session = Depends(get_db)
):
    query = db.query(ApprovalRequest)
    if status:
        query = query.filter(ApprovalRequest.status == status)
    return query.order_by(ApprovalRequest.created_at.desc()).all()


@router.post("/approval/{approval_id}/decision")
def decide_approval(
    approval_id: int,
    decision: str,
    decision_reason: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    req = db.query(ApprovalRequest).filter_by(id=approval_id).first()
    if not req or req.status != ApprovalStatus.pending:
        raise HTTPException(404, "Approval request not found or already decided")
    if decision not in ApprovalStatus.__members__:
        raise HTTPException(400, "Invalid decision")
    req.status = ApprovalStatus[decision]
    req.decision_by = user.id
    req.decision_reason = decision_reason
    req.decided_at = datetime.utcnow()
    db.commit()
    db.refresh(req)
    try:
        from ..models import AuditTrailEntry
        from ..services.audit_trail_service import record_audit_event
        parent = (
            db.query(AuditTrailEntry)
            .filter(
                AuditTrailEntry.event_type == "approval_requested",
                AuditTrailEntry.entity_type == "approval",
                AuditTrailEntry.entity_id == str(req.id),
            )
            .order_by(AuditTrailEntry.timestamp.desc())
            .first()
        )
        record_audit_event(
            db=db,
            event_type="approval_decided",
            entity_type="approval",
            entity_id=str(req.id),
            actor_type="human",
            actor_id=user.id,
            summary=f"Approval {decision} for {req.resource_type}/{req.resource_id}",
            details={"decision": decision, "reason": decision_reason},
            regulation_tags=["SEC_17a4", "FINRA_4511"],
            parent_audit_id=parent.id if parent else None,
        )
    except Exception:
        pass
    return req
