from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from ..approval import ApprovalRequest, ApprovalStatus
from .users import get_db, get_current_user

router = APIRouter()

@router.post("/approval/", response_model=None)
def submit_approval(resource_type: str, resource_id: str, reason: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    req = ApprovalRequest(
        resource_type=resource_type,
        resource_id=resource_id,
        reason=reason,
        requested_by=user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

@router.get("/approval/")
def list_approvals(status: Optional[ApprovalStatus] = None, db: Session = Depends(get_db)):
    query = db.query(ApprovalRequest)
    if status:
        query = query.filter(ApprovalRequest.status == status)
    return query.order_by(ApprovalRequest.created_at.desc()).all()

@router.post("/approval/{approval_id}/decision")
def decide_approval(approval_id: int, decision: str, decision_reason: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
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
    return req
