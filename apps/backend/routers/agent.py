from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from ..services.agent_service import AgenticTriageService
from ..services.incident_remediation_service import IncidentRemediationService
from ..services.compliance_automation_service import ComplianceAutomationService
from ..services.audit_summary_service import AuditSummaryService
from ..services.agentic_workflow_service import AgenticWorkflowService
from ..services.basel_compliance_service import BaselComplianceService
from ..security import require_role
from ..schemas import AgentActionCreate, AgentActionUpdate, AgentAction
from ..models import AgentAction as AgentActionModel
from ..database import get_db
import logging
from datetime import datetime

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)
agent_service = AgenticTriageService()
remediation_service = IncidentRemediationService()
compliance_service = ComplianceAutomationService()
audit_summary_service = AuditSummaryService()
workflow_service = AgenticWorkflowService()
basel_service = BaselComplianceService()

@router.get("/compliance/lcr")
async def get_lcr_status(
    lookback_days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get Basel III Liquidity Coverage Ratio (LCR) compliance status.
    """
    try:
        result = basel_service.calculate_lcr(db, lookback_days=lookback_days)
        return result
    except Exception as e:
        logger.error(f"Error calculating LCR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/triage")
async def triage_incident(incident: Dict[str, Any], db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance", "analyst"]))):
    """Run agentic triage on an incident/anomaly and submit for approval."""
    siem.send_syslog_event(f"Agent: Triage incident {incident.get('incident_id')}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
    try:
        result = agent_service.triage_incident(incident)
        # Submit agent action for approval
        agent_action = AgentActionModel(
            incident_id=incident.get("incident_id", "unknown"),
            action="triage",
            agent_result=result,
            status="pending",
            submitted_by=incident.get("submitted_by"),
            created_at=datetime.utcnow(),
            meta=incident,
            ai_explanation=result.get("rationale") if isinstance(result, dict) else None,
            agent_input=incident,
            agent_output=result if isinstance(result, dict) else {"result": result},
            agent_version=agent_service.__class__.__name__,
            actor_type="agent",
            is_simulation=incident.get("is_simulation", False)
        )
        db.add(agent_action)
        db.commit()
        db.refresh(agent_action)
        response = {"result": result, "action_id": agent_action.id}
        if isinstance(result, dict):
            if "rationale" in result:
                response["rationale"] = result["rationale"]
            if "recommendation" in result:
                response["recommendation"] = result["recommendation"]
        return response
    except Exception as e:
        logger.error(f"Agentic triage endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/actions", response_model=List[AgentAction])
async def list_agent_actions(status: str = None, db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance"]))):
    """List agent actions, optionally filtered by status."""
    siem.send_syslog_event(f"Agent: List agent actions (status={status})", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
    query = db.query(AgentActionModel)
    if status:
        query = query.filter(AgentActionModel.status == status)
    return query.order_by(AgentActionModel.created_at.desc()).all()

@router.post("/actions/{action_id}/approve", response_model=AgentAction)
async def approve_agent_action(action_id: int, approved_by: int, db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance"]))):
    """Approve a pending agent action."""
    siem.send_syslog_event(f"Agent: Approve agent action {action_id} by {approved_by}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
    action = db.query(AgentActionModel).filter(AgentActionModel.id == action_id).first()
    if not action or action.status != "pending":
        raise HTTPException(status_code=404, detail="Pending action not found")
    action.status = "approved"
    action.approved_by = approved_by
    action.approved_at = datetime.utcnow()
    action.override_type = "manual_override" if action.actor_type == "agent" else None
    action.actor_type = "human"
    db.commit()
    db.refresh(action)
    return action

@router.post("/actions/{action_id}/reject", response_model=AgentAction)
async def reject_agent_action(action_id: int, approved_by: int, db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance"]))):
    """Reject a pending agent action."""
    siem.send_syslog_event(f"Agent: Reject agent action {action_id} by {approved_by}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
    action = db.query(AgentActionModel).filter(AgentActionModel.id == action_id).first()
    if not action or action.status != "pending":
        raise HTTPException(status_code=404, detail="Pending action not found")
    action.status = "rejected"
    action.approved_by = approved_by
    action.approved_at = datetime.utcnow()
    action.override_type = "manual_override" if action.actor_type == "agent" else None
    action.actor_type = "human"
    db.commit()
    db.refresh(action)
    return action

@router.post("/remediate")
async def remediate_incident(incident: Dict[str, Any], db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance", "analyst"]))):
    """Run agentic remediation on an incident/anomaly and submit for approval."""
    siem.send_syslog_event(f"Agent: Remediate incident {incident.get('incident_id')}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
    try:
        result = remediation_service.remediate_incident(incident)
        # Submit agent action for approval
        agent_action = AgentActionModel(
            incident_id=incident.get("incident_id", "unknown"),
            action="remediate",
            agent_result=result,
            status="pending",
            submitted_by=incident.get("submitted_by"),
            created_at=datetime.utcnow(),
            meta=incident,
            ai_explanation=result.get("rationale") if isinstance(result, dict) else None,
            agent_input=incident,
            agent_output=result if isinstance(result, dict) else {"result": result},
            agent_version=remediation_service.__class__.__name__,
            actor_type="agent",
            is_simulation=incident.get("is_simulation", False)
        )
        db.add(agent_action)
        db.commit()
        db.refresh(agent_action)
        response = {"result": result, "action_id": agent_action.id}
        if isinstance(result, dict):
            if "rationale" in result:
                response["rationale"] = result["rationale"]
            if "recommendation" in result:
                response["recommendation"] = result["recommendation"]
        return response
    except Exception as e:
        logger.error(f"Agentic remediation endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compliance")
async def automate_compliance(transaction: Dict[str, Any], db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance", "analyst"]))):
    """Run agentic compliance automation on a transaction/event and submit for approval."""
    siem.send_syslog_event(f"Agent: Automate compliance for transaction {transaction.get('transaction_id')}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
    try:
        result = compliance_service.automate_compliance(transaction)
        agent_action = AgentActionModel(
            incident_id=transaction.get("incident_id", "unknown"),
            action="automate_compliance",
            agent_result=result,
            status="pending",
            submitted_by=transaction.get("submitted_by"),
            created_at=datetime.utcnow(),
            meta=transaction,
            ai_explanation=result.get("rationale") if isinstance(result, dict) else None,
            agent_input=transaction,
            agent_output=result if isinstance(result, dict) else {"result": result},
            agent_version=compliance_service.__class__.__name__,
            actor_type="agent",
            is_simulation=transaction.get("is_simulation", False)
        )
        db.add(agent_action)
        db.commit()
        db.refresh(agent_action)
        response = {"result": result, "action_id": agent_action.id}
        if isinstance(result, dict):
            if "rationale" in result:
                response["rationale"] = result["rationale"]
            if "recommendation" in result:
                response["recommendation"] = result["recommendation"]
        return response
    except Exception as e:
        logger.error(f"Agentic compliance endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/audit_summary")
async def summarize_audit(logs: List[Dict[str, Any]], db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance"]))):
    """Run agentic audit log summarization and submit for approval."""
    siem.send_syslog_event(f"Agent: Summarize audit logs", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
    try:
        result = audit_summary_service.summarize_audit(logs)
        agent_action = AgentActionModel(
            incident_id="audit_summary",  # or derive from logs if available
            action="audit_summary",
            agent_result=result,
            status="pending",
            submitted_by=user["id"] if isinstance(user, dict) and "id" in user else None,
            created_at=datetime.utcnow(),
            meta={"logs": logs},
            ai_explanation=result.get("rationale") if isinstance(result, dict) else None,
            agent_input={"logs": logs},
            agent_output=result if isinstance(result, dict) else {"result": result},
            agent_version=audit_summary_service.__class__.__name__,
            actor_type="agent",
            is_simulation=False
        )
        db.add(agent_action)
        db.commit()
        db.refresh(agent_action)
        response = {"result": result, "action_id": agent_action.id}
        if isinstance(result, dict):
            if "rationale" in result:
                response["rationale"] = result["rationale"]
            if "recommendation" in result:
                response["recommendation"] = result["recommendation"]
        return response
    except Exception as e:
        logger.error(f"Agentic audit summary endpoint failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
