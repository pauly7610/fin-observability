import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from .agent_service import AgenticTriageService
from .incident_remediation_service import IncidentRemediationService
from .compliance_automation_service import ComplianceAutomationService
from .audit_summary_service import AuditSummaryService
from ..models import AgentAction, Incident

STAGES = ["triage", "remediate", "compliance", "audit_summary"]


class AgenticWorkflowService:
    def __init__(self):
        self.triage = AgenticTriageService()
        self.remediate = IncidentRemediationService()
        self.compliance = ComplianceAutomationService()
        self.audit = AuditSummaryService()

    def start_workflow(
        self, incident: Dict[str, Any], db: Session, submitted_by: Optional[int] = None
    ) -> Dict[str, Any]:
        workflow_id = f"{incident.get('incident_id', str(uuid.uuid4()))}-{int(datetime.utcnow().timestamp())}"
        # Start with triage
        triage_result = self.triage.triage_incident(incident)
        auto_approved = (
            triage_result.get("risk_level") == "low"
            and triage_result.get("confidence", 0.0) >= 0.95
        )
        triage_action = AgentAction(
            workflow_id=workflow_id,
            parent_action_id=None,
            incident_id=incident.get("incident_id", "unknown"),
            action="triage",
            agent_result=triage_result,
            status="approved" if auto_approved else "pending",
            auto_approved=auto_approved,
            submitted_by=submitted_by,
            created_at=datetime.utcnow(),
            meta=incident,
        )
        db.add(triage_action)
        db.commit()
        db.refresh(triage_action)
        if auto_approved:
            # Immediately advance to next stage recursively
            return self._auto_advance_workflow(workflow_id, triage_action, db)
        return {
            "workflow_id": workflow_id,
            "current_stage": "triage",
            "action_id": triage_action.id,
            "status": "pending",
            "next": "approve triage to proceed",
        }

    def _auto_advance_workflow(
        self, workflow_id: str, last_action: AgentAction, db: Session
    ) -> Dict[str, Any]:
        # Find next stage
        try:
            idx = STAGES.index(last_action.action)
        except ValueError:
            return {"error": f"Unknown stage '{last_action.action}'."}
        if idx + 1 >= len(STAGES):
            return {
                "workflow_id": workflow_id,
                "status": "complete",
                "message": "Workflow finished (auto-approved).",
            }
        next_stage = STAGES[idx + 1]
        incident_id = last_action.incident_id
        meta = last_action.meta or {}
        # Run next agent
        if next_stage == "remediate":
            result = self.remediate.remediate_incident(meta)
        elif next_stage == "compliance":
            result = self.compliance.automate_compliance(meta)
        elif next_stage == "audit_summary":
            logs = [
                a.meta
                for a in db.query(AgentAction)
                .filter(AgentAction.workflow_id == workflow_id)
                .order_by(AgentAction.created_at)
                .all()
            ]
            result = self.audit.summarize_audit(logs)
        else:
            return {"error": f"Unknown next stage '{next_stage}'."}
        auto_approved = (
            result.get("risk_level") == "low" and result.get("confidence", 0.0) >= 0.95
        )
        next_action = AgentAction(
            workflow_id=workflow_id,
            parent_action_id=last_action.id,
            incident_id=incident_id,
            action=next_stage,
            agent_result=result,
            status="approved" if auto_approved else "pending",
            auto_approved=auto_approved,
            submitted_by=None,
            created_at=datetime.utcnow(),
            meta=meta,
        )
        db.add(next_action)
        db.commit()
        db.refresh(next_action)
        if auto_approved:
            # Recursively advance
            return self._auto_advance_workflow(workflow_id, next_action, db)
        return {
            "workflow_id": workflow_id,
            "current_stage": next_stage,
            "action_id": next_action.id,
            "status": "pending",
            "next": f"approve {next_stage} to proceed",
        }

    def advance_workflow(
        self, workflow_id: str, db: Session, approved_by: Optional[int] = None
    ) -> Dict[str, Any]:
        # Find the latest approved action for this workflow
        actions = (
            db.query(AgentAction)
            .filter(AgentAction.workflow_id == workflow_id)
            .order_by(AgentAction.created_at)
            .all()
        )
        if not actions:
            return {"error": "No actions found for workflow."}
        last_action = actions[-1]
        if last_action.status != "approved":
            return {"error": f"Current stage '{last_action.action}' not yet approved."}
        # Determine next stage
        try:
            idx = STAGES.index(last_action.action)
        except ValueError:
            return {"error": f"Unknown stage '{last_action.action}'."}
        if idx + 1 >= len(STAGES):
            return {
                "workflow_id": workflow_id,
                "status": "complete",
                "message": "Workflow finished.",
            }
        next_stage = STAGES[idx + 1]
        incident_id = last_action.incident_id
        meta = last_action.meta or {}
        # Run next agent
        if next_stage == "remediate":
            result = self.remediate.remediate_incident(meta)
        elif next_stage == "compliance":
            result = self.compliance.automate_compliance(meta)
        elif next_stage == "audit_summary":
            logs = [a.meta for a in actions]
            result = self.audit.summarize_audit(logs)
        else:
            return {"error": f"Unknown next stage '{next_stage}'."}
        auto_approved = (
            result.get("risk_level") == "low" and result.get("confidence", 0.0) >= 0.95
        )
        next_action = AgentAction(
            workflow_id=workflow_id,
            parent_action_id=last_action.id,
            incident_id=incident_id,
            action=next_stage,
            agent_result=result,
            status="approved" if auto_approved else "pending",
            auto_approved=auto_approved,
            submitted_by=None,
            created_at=datetime.utcnow(),
            meta=meta,
        )
        db.add(next_action)
        db.commit()
        db.refresh(next_action)
        if auto_approved:
            # Recursively advance
            return self._auto_advance_workflow(workflow_id, next_action, db)
        return {
            "workflow_id": workflow_id,
            "current_stage": next_stage,
            "action_id": next_action.id,
            "status": "pending",
            "next": f"approve {next_stage} to proceed",
        }

    def get_workflow_status(self, workflow_id: str, db: Session) -> Dict[str, Any]:
        actions = (
            db.query(AgentAction)
            .filter(AgentAction.workflow_id == workflow_id)
            .order_by(AgentAction.created_at)
            .all()
        )
        if not actions:
            return {"error": "No actions found for workflow."}
        history = [
            {
                "stage": a.action,
                "status": a.status,
                "result": a.agent_result,
                "action_id": a.id,
                "approved_by": a.approved_by,
                "approved_at": a.approved_at,
                "created_at": a.created_at,
                "parent_action_id": a.parent_action_id,
            }
            for a in actions
        ]
        return {
            "workflow_id": workflow_id,
            "history": history,
            "current_stage": actions[-1].action,
            "current_status": actions[-1].status,
        }
