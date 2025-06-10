import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from apps.backend.models import AgentAction, AgentActionAuditLog
from apps.backend.database import get_db

ESCALATION_HOURS = int(os.getenv("AGENT_ACTION_ESCALATION_HOURS", "24"))

def escalate_overdue_agent_actions(db: Session):
    now = datetime.utcnow()
    threshold = now - timedelta(hours=ESCALATION_HOURS)
    overdue_actions = db.query(AgentAction).filter(
        AgentAction.status == "pending",
        AgentAction.is_escalated == False,
        AgentAction.created_at < threshold
    ).all()
    for action in overdue_actions:
        action.is_escalated = True
        action.escalated_at = now
        action.escalation_reason = f"Auto-escalated after {ESCALATION_HOURS} hours pending."
        audit = AgentActionAuditLog(
            agent_action_id=action.id,
            event_type="auto_escalated",
            from_status="pending",
            to_status="pending",
            operator_id=None,
            comment=action.escalation_reason,
            timestamp=now
        )
        db.add(audit)
    db.commit()
    return len(overdue_actions)
