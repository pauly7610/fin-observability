from fastapi import APIRouter, HTTPException, Depends
from slowapi.decorator import limiter as rate_limiter
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
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("agent.get_lcr_status") as span:
        span.set_attribute("lookback_days", lookback_days)
        try:
            result = basel_service.calculate_lcr(db, lookback_days=lookback_days)
            span.set_attribute("result_keys", list(result.keys()) if isinstance(result, dict) else str(type(result)))
            return result
        except Exception as e:
            span.record_exception(e)
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, str(e)))
            logger.error(f"Error calculating LCR: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/triage")
@rate_limiter("3/minute")  # LLM endpoint, strict limit
async def triage_incident(incident: Dict[str, Any], db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance", "analyst"]))):
    """Run agentic triage on an incident/anomaly and submit for approval."""
    siem.send_syslog_event(
    event="Agent: Triage incident",
    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    extra={"incident_id": incident.get('incident_id'), "user": str(user.get('id') if isinstance(user, dict) else user)}
)
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("agent.triage_incident") as span:
        span.set_attribute("incident_id", incident.get("incident_id"))
        span.set_attribute("submitted_by", incident.get("submitted_by"))
        try:
            result = agent_service.triage_incident(incident)
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
            span.set_attribute("action_id", agent_action.id)
            # Increment compliance action metric
            from apps.backend.main import compliance_action_counter
            compliance_action_counter.add(1, {"type": "triage", "status": "pending", "user": str(user.get('id') if isinstance(user, dict) else user)})
            return response
        except Exception as e:
            span.record_exception(e)
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, str(e)))
            get_logger(__name__).error("Agentic triage endpoint failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/actions", response_model=List[AgentAction])
@rate_limiter("30/minute")  # Listing endpoint, higher limit
async def list_agent_actions(status: str = None, db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance"]))):
    """List agent actions, optionally filtered by status."""
    siem.send_syslog_event(f"Agent: List agent actions (status={status})", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("agent.list_agent_actions") as span:
        span.set_attribute("status", status)
        query = db.query(AgentActionModel)
        if status:
            query = query.filter(AgentActionModel.status == status)
        actions = query.order_by(AgentActionModel.created_at.desc()).all()
        span.set_attribute("action_count", len(actions))
        return actions

@router.post("/actions/{action_id}/approve", response_model=AgentAction)
@rate_limiter("10/minute")  # Approval endpoint, moderate limit
async def approve_agent_action(action_id: int, approved_by: int, db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance"]))):
    """Approve a pending agent action."""
    siem.send_syslog_event(
    event="Agent: Approve agent action",
    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    extra={"action_id": action_id, "approved_by": approved_by, "user": str(user.get('id') if isinstance(user, dict) else user)}
)
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("agent.approve_agent_action") as span:
        span.set_attribute("action_id", action_id)
        span.set_attribute("approved_by", approved_by)
        action = db.query(AgentActionModel).filter(AgentActionModel.id == action_id).first()
        if not action or action.status != "pending":
            span.set_status(trace.status.Status(trace.status.StatusCode.ERROR, "Pending action not found"))
            raise HTTPException(status_code=404, detail="Pending action not found")
        action.status = "approved"
        action.approved_by = approved_by
        action.approved_at = datetime.utcnow()
        action.override_type = "manual_override" if action.actor_type == "agent" else None
        action.actor_type = "human"
        db.commit()
        db.refresh(action)
        # Increment compliance action metric
        from apps.backend.main import compliance_action_counter
        compliance_action_counter.add(1, {"type": "approve", "status": "approved", "user": str(user.get('id') if isinstance(user, dict) else user)})
        return action

@router.post("/actions/{action_id}/reject", response_model=AgentAction)
async def reject_agent_action(action_id: int, approved_by: int, db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance"]))):
    """Reject a pending agent action."""
    siem.send_syslog_event(
    event="Agent: Reject agent action",
    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    extra={"action_id": action_id, "approved_by": approved_by, "user": str(user.get('id') if isinstance(user, dict) else user)}
)
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("agent.reject_agent_action") as span:
        span.set_attribute("action_id", action_id)
        span.set_attribute("approved_by", approved_by)
        action = db.query(AgentActionModel).filter(AgentActionModel.id == action_id).first()
        if not action or action.status != "pending":
            span.set_status(trace.status.Status(trace.status.StatusCode.ERROR, "Pending action not found"))
            raise HTTPException(status_code=404, detail="Pending action not found")
        action.status = "rejected"
        action.approved_by = approved_by
        action.approved_at = datetime.utcnow()
        action.override_type = "manual_override" if action.actor_type == "agent" else None
        action.actor_type = "human"
        db.commit()
        db.refresh(action)
        # Increment compliance action metric
        from apps.backend.main import compliance_action_counter
        compliance_action_counter.add(1, {"type": "reject", "status": "rejected", "user": str(user.get('id') if isinstance(user, dict) else user)})
        return action

@router.post("/remediate")
async def remediate_incident(incident: Dict[str, Any], db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance", "analyst"]))):
    """Run agentic remediation on an incident/anomaly and submit for approval."""
    siem.send_syslog_event(
    event="Agent: Remediate incident",
    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    extra={"incident_id": incident.get('incident_id'), "user": str(user.get('id') if isinstance(user, dict) else user)}
)
    from apps.backend.approval import require_approval
    user_id = getattr(user, 'id', None) if hasattr(user, 'id') else None
    approved, approval_req = require_approval(
        db=db,
        resource_type="agentic_remediation",
        resource_id=str(incident.get("incident_id", "unknown")),
        user_id=user_id,
        reason="Agentic remediation action",
        meta=incident
    )
    if not approved:
        return {"detail": "Remediation action requires approval", "approval_request_id": approval_req.id, "status": approval_req.status.value}
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("agent.remediate_incident") as span:
        span.set_attribute("incident_id", incident.get("incident_id"))
        span.set_attribute("submitted_by", incident.get("submitted_by"))
        try:
            result = remediation_service.remediate_incident(incident)
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
            span.set_attribute("action_id", agent_action.id)
            # Increment compliance action metric
            from apps.backend.main import compliance_action_counter
            compliance_action_counter.add(1, {"type": "remediate", "status": "pending", "user": str(user.get('id') if isinstance(user, dict) else user)})
            return response
        except Exception as e:
            span.record_exception(e)
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, str(e)))
            get_logger(__name__).error("Agentic remediation endpoint failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/compliance")
async def automate_compliance(transaction: Dict[str, Any], db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance", "analyst"]))):
    """Run agentic compliance automation on a transaction/event and submit for approval."""
    siem.send_syslog_event(
    event="Agent: Automate compliance",
    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    extra={"transaction_id": transaction.get('transaction_id'), "user": str(user.get('id') if isinstance(user, dict) else user)}
)
    from apps.backend.approval import require_approval
    user_id = getattr(user, 'id', None) if hasattr(user, 'id') else None
    approved, approval_req = require_approval(
        db=db,
        resource_type="agentic_compliance",
        resource_id=str(transaction.get("transaction_id", "unknown")),
        user_id=user_id,
        reason="Agentic compliance automation action",
        meta=transaction
    )
    if not approved:
        return {"detail": "Compliance automation requires approval", "approval_request_id": approval_req.id, "status": approval_req.status.value}
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("agent.automate_compliance") as span:
        span.set_attribute("transaction_id", transaction.get("transaction_id"))
        span.set_attribute("submitted_by", transaction.get("submitted_by"))
        try:
            result = compliance_service.automate_compliance(transaction)
            agent_action = AgentActionModel(
                incident_id=transaction.get("transaction_id", "unknown"),
                action="compliance",
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
            span.set_attribute("action_id", agent_action.id)
            # Increment compliance action metric
            from apps.backend.main import compliance_action_counter
            compliance_action_counter.add(1, {"type": "compliance", "status": "pending", "user": str(user.get('id') if isinstance(user, dict) else user)})
            return response
        except Exception as e:
            span.record_exception(e)
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, str(e)))
            get_logger(__name__).error("Agentic compliance automation endpoint failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/audit_summary")
async def summarize_audit(logs: List[Dict[str, Any]], db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance"]))):
    """Run agentic audit log summarization and submit for approval."""
    siem.send_syslog_event(
    event="Agent: Summarize audit logs",
    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    extra={"user": str(user.get('id') if isinstance(user, dict) else user)}
)
    from apps.backend.approval import require_approval
    user_id = getattr(user, 'id', None) if hasattr(user, 'id') else None
    approved, approval_req = require_approval(
        db=db,
        resource_type="agentic_audit_summary",
        resource_id=f"audit_summary_{user_id}_{len(logs)}",
        user_id=user_id,
        reason="Agentic audit log summarization",
        meta={"logs_count": len(logs)}
    )
    if not approved:
        return {"detail": "Audit summarization requires approval", "approval_request_id": approval_req.id, "status": approval_req.status.value}
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("agent.summarize_audit") as span:
        span.set_attribute("logs_count", len(logs))
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
            span.set_attribute("action_id", agent_action.id)
            # Increment compliance action metric
            from apps.backend.main import compliance_action_counter
            compliance_action_counter.add(1, {"type": "audit_summary", "status": "pending", "user": str(user.get('id') if isinstance(user, dict) else user)})
            return response
        except Exception as e:
            span.record_exception(e)
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, str(e)))
            get_logger(__name__).error("Agentic audit summarization endpoint failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
