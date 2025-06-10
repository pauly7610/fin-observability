from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import AgentAction as AgentActionModel, AgentActionAuditLog
from ..database import get_db
from ..schemas import AgentAction, AgentActionAuditLog as AgentActionAuditLogSchema
from ..security import require_role
from datetime import datetime
import os
from apps.backend import siem

router = APIRouter(prefix="/agent/ops", tags=["chatops", "ops", "human-in-the-loop"])

@router.get("/actions", response_model=List[AgentAction])
async def list_agent_actions(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
) -> List[AgentAction]:
    siem.send_syslog_event(f"Ops: List agent actions (status={status})", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
    query = db.query(AgentActionModel)
    if status:
        query = query.filter(AgentActionModel.status == status)
    return query.order_by(AgentActionModel.created_at.desc()).all()

@router.get("/actions/{action_id}/history", response_model=List[AgentActionAuditLogSchema])
async def get_agent_action_history(
    action_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
):
    logs = db.query(AgentActionAuditLog).filter(AgentActionAuditLog.agent_action_id == action_id).order_by(AgentActionAuditLog.timestamp.asc()).all()
    return logs

def write_audit_log(db, agent_action_id, event_type, from_status=None, to_status=None, operator_id=None, comment=None, meta=None, ai_explanation=None, agent_input=None, agent_output=None, agent_version=None, actor_type=None, override_type=None, is_simulation=False):
    audit = AgentActionAuditLog(
        agent_action_id=agent_action_id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        operator_id=operator_id,
        comment=comment,
        meta=meta,
        ai_explanation=ai_explanation,
        agent_input=agent_input,
        agent_output=agent_output,
        agent_version=agent_version,
        actor_type=actor_type,
        override_type=override_type,
        is_simulation=is_simulation,
        timestamp=datetime.utcnow()
    )
    db.add(audit)
    db.commit()

@router.post("/actions/{action_id}/approve", response_model=AgentAction)
async def approve_agent_action(
    action_id: int,
    operator: str,
    comment: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
) -> AgentAction:
    siem.send_syslog_event(f"Ops: Approve agent action {action_id} by {operator}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
    action = db.query(AgentActionModel).filter(AgentActionModel.id == action_id).first()
    if not action or action.status != "pending":
        raise HTTPException(status_code=404, detail="Pending action not found")
    prev_status = action.status
    # Multi-party, role-based, and ordered approval logic
    if action.approvals is None:
        action.approvals = []
    user_id = user["id"] if isinstance(user, dict) and "id" in user else operator
    user_role = user["role"] if isinstance(user, dict) and "role" in user else None
    # Role-based approval
    if action.approval_roles and user_role and user_role not in action.approval_roles:
        raise HTTPException(status_code=403, detail=f"User role '{user_role}' not permitted to approve this action.")
    # Ordered approval
    if action.approval_order and len(action.approval_order) > 0:
        expected_id = action.approval_order[action.current_approval_index] if action.current_approval_index < len(action.approval_order) else None
        if str(user_id) != str(expected_id):
            raise HTTPException(status_code=403, detail=f"Approval must be performed by user {expected_id} at this step.")
        if user_id not in action.approvals:
            action.approvals.append(user_id)
        action.current_approval_index += 1
        # Only fully approve if all in order have approved
        if action.current_approval_index >= len(action.approval_order):
            action.status = "approved"
            action.is_fully_approved = True
            action.fully_approved_at = datetime.utcnow()
            action.approved_by = operator
            action.approved_at = datetime.utcnow()
            to_status = "approved"
        else:
            action.status = "pending"
            action.is_fully_approved = False
            action.fully_approved_at = None
            to_status = "pending"
    else:
        # Multi-party approval (unordered)
        if user_id not in action.approvals:
            action.approvals.append(user_id)
        if len(set(action.approvals)) >= (action.approvals_required or 1):
            action.status = "approved"
            action.is_fully_approved = True
            action.fully_approved_at = datetime.utcnow()
            action.approved_by = operator
            action.approved_at = datetime.utcnow()
            to_status = "approved"
        else:
            action.status = "pending"
            action.is_fully_approved = False
            action.fully_approved_at = None
            to_status = "pending"
    if comment:
        if not hasattr(action, 'ops_comments') or action.ops_comments is None:
            action.ops_comments = []
        action.ops_comments.append({"operator": operator, "comment": comment, "timestamp": datetime.utcnow().isoformat()})
    db.commit()
    db.refresh(action)
    write_audit_log(
        db, action.id, "approved",
        from_status=prev_status, to_status=to_status, operator_id=user_id, comment=comment,
        meta={"approvals": action.approvals, "approval_roles": action.approval_roles, "approval_order": action.approval_order, "current_approval_index": action.current_approval_index},
        ai_explanation=getattr(action, 'ai_explanation', None),
        agent_input=getattr(action, 'agent_input', None),
        agent_output=getattr(action, 'agent_output', None),
        agent_version=getattr(action, 'agent_version', None),
        actor_type="human",
        override_type="manual_override" if getattr(action, 'actor_type', None) == "agent" else None,
        is_simulation=getattr(action, 'is_simulation', False)
    )
    return action

@router.post("/actions/{action_id}/reject", response_model=AgentAction)
async def reject_agent_action(
    action_id: int,
    operator: str,
    comment: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
) -> AgentAction:
    """
    Reject a pending agent action with optional operator comment.
    """
    siem.send_syslog_event(
        f"Ops: Reject agent action {action_id} by {operator}",
        host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
        port=int(os.getenv("SIEM_SYSLOG_PORT", "514"))
    )
    action = db.query(AgentActionModel).filter(AgentActionModel.id == action_id).first()
    if not action or action.status != "pending":
        raise HTTPException(status_code=404, detail="Pending action not found")
    prev_status = action.status
    action.status = "rejected"
    action.approved_by = operator
    action.approved_at = datetime.utcnow()
    if comment:
        if not hasattr(action, 'ops_comments') or action.ops_comments is None:
            action.ops_comments = []
        action.ops_comments.append({
            "operator": operator,
            "comment": comment,
            "timestamp": datetime.utcnow().isoformat()
        })
    db.commit()
    db.refresh(action)
    write_audit_log(db, action.id, "rejected", from_status=prev_status, to_status="rejected", operator_id=user["id"] if isinstance(user, dict) and "id" in user else None, comment=comment)
    return action

@router.post("/actions/{action_id}/assign", response_model=AgentAction)
async def assign_agent_action(
    action_id: int,
    assignee_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
) -> AgentAction:
    action = db.query(AgentActionModel).filter(AgentActionModel.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Agent action not found")
    prev_assignee = action.assigned_to
    action.assigned_to = assignee_id
    db.commit()
    db.refresh(action)
    write_audit_log(db, action.id, "assigned", operator_id=user["id"] if isinstance(user, dict) and "id" in user else None, meta={"from": prev_assignee, "to": assignee_id})
    return action

@router.post("/actions/{action_id}/escalate", response_model=AgentAction)
async def escalate_agent_action(
    action_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
) -> AgentAction:
    action = db.query(AgentActionModel).filter(AgentActionModel.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Agent action not found")
    action.is_escalated = True
    action.escalated_at = datetime.utcnow()
    action.escalation_reason = reason
    db.commit()
    db.refresh(action)
    write_audit_log(db, action.id, "escalated", operator_id=user["id"] if isinstance(user, dict) and "id" in user else None, comment=reason)
    return action

@router.post("/actions/{action_id}/comment", response_model=AgentAction)
async def comment_agent_action(
    action_id: int,
    comment: str,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
) -> AgentAction:
    action = db.query(AgentActionModel).filter(AgentActionModel.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Agent action not found")
    # Optionally store comments in meta or a comments array
    if not action.meta:
        action.meta = {}
    if "comments" not in action.meta or action.meta["comments"] is None:
        action.meta["comments"] = []
    action.meta["comments"].append({
        "user": user["id"] if isinstance(user, dict) and "id" in user else None,
        "comment": comment,
        "timestamp": datetime.utcnow().isoformat()
    })
    db.commit()
    db.refresh(action)
    write_audit_log(db, action.id, "commented", operator_id=user["id"] if isinstance(user, dict) and "id" in user else None, comment=comment)
    return action

from sqlalchemy import func

@router.get("/actions/metrics")
async def agent_action_metrics(
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
):
    total_actions = db.query(func.count(AgentActionModel.id)).scalar()
    pending = db.query(func.count(AgentActionModel.id)).filter(AgentActionModel.status == "pending").scalar()
    approved = db.query(func.count(AgentActionModel.id)).filter(AgentActionModel.status == "approved").scalar()
    rejected = db.query(func.count(AgentActionModel.id)).filter(AgentActionModel.status == "rejected").scalar()
    escalated = db.query(func.count(AgentActionModel.id)).filter(AgentActionModel.is_escalated == True).scalar()
    avg_approval_time = db.query(func.avg(func.julianday(AgentActionModel.approved_at) - func.julianday(AgentActionModel.created_at))).filter(
        AgentActionModel.status == "approved",
        AgentActionModel.approved_at != None
    ).scalar()
    # Per-operator approval counts
    per_operator = db.query(AgentActionModel.approved_by, func.count(AgentActionModel.id)).filter(
        AgentActionModel.status == "approved"
    ).group_by(AgentActionModel.approved_by).all()
    return {
        "total": total_actions,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "escalated": escalated,
        "avg_approval_time_days": avg_approval_time,
        "per_operator_approvals": [
            {"operator": op, "count": count} for op, count in per_operator if op is not None
        ]
    }
