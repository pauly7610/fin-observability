from fastapi import APIRouter, Depends, HTTPException, Request
from apps.backend.rate_limit import limiter
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from ..services.agent_service import AgenticTriageService
from ..services.incident_remediation_service import IncidentRemediationService
from ..services.compliance_automation_service import ComplianceAutomationService
from ..services.audit_summary_service import AuditSummaryService
from ..models import AgentAction as AgentActionModel
from ..database import get_db
from ..security import require_role
from datetime import datetime

router = APIRouter(
    prefix="/agent/ops/trigger", tags=["chatops", "ops", "human-in-the-loop"]
)

triage_service = AgenticTriageService()
remediation_service = IncidentRemediationService()
compliance_service = ComplianceAutomationService()
audit_service = AuditSummaryService()


@router.post("/triage")
@limiter.limit("3/minute")  # LLM endpoint, strict limit
async def trigger_triage(
    request: Request,
    incident: Dict[str, Any],
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "analyst", "compliance"])),
):
    siem.send_syslog_event(
        f"Ops Trigger: Manual triage triggered for incident {incident.get('incident_id')}",
        host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
        port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    )
    result = triage_service.triage_incident(incident)
    agent_action = AgentActionModel(
        incident_id=incident.get("incident_id", "unknown"),
        action="triage",
        agent_result=result,
        status="pending",
        submitted_by=user.id,
        created_at=datetime.utcnow(),
        meta=incident,
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


@router.post("/remediate")
@limiter.limit("3/minute")  # LLM endpoint, strict limit
async def trigger_remediation(
    request: Request,
    incident: Dict[str, Any],
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "analyst", "compliance"])),
):
    siem.send_syslog_event(
        f"Ops Trigger: Manual remediation triggered for incident {incident.get('incident_id')}",
        host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
        port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    )
    result = remediation_service.remediate_incident(incident)
    agent_action = AgentActionModel(
        incident_id=incident.get("incident_id", "unknown"),
        action="remediate",
        agent_result=result,
        status="pending",
        submitted_by=user.id,
        created_at=datetime.utcnow(),
        meta=incident,
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


@router.post("/compliance")
@limiter.limit("3/minute")  # LLM endpoint, strict limit
async def trigger_compliance(
    request: Request,
    transaction: Dict[str, Any],
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"])),
):
    siem.send_syslog_event(
        f"Ops Trigger: Manual compliance triggered for transaction {transaction.get('transaction_id')}",
        host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
        port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    )
    result = compliance_service.automate_compliance(transaction)
    agent_action = AgentActionModel(
        incident_id=transaction.get("incident_id", "unknown"),
        action="compliance",
        agent_result=result,
        status="pending",
        submitted_by=user.id,
        created_at=datetime.utcnow(),
        meta=transaction,
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


@router.post("/audit_summary")
async def trigger_audit_summary(
    logs: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"])),
):
    siem.send_syslog_event(
        f"Ops Trigger: Manual audit summary triggered",
        host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
        port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    )
    result = audit_service.summarize_audit(logs)
    agent_action = AgentActionModel(
        incident_id="audit_summary",
        action="audit_summary",
        agent_result=result,
        status="pending",
        submitted_by=user.id,
        created_at=datetime.utcnow(),
        meta={"logs": logs},
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
