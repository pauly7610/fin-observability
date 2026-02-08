from fastapi import APIRouter, HTTPException, Depends, Request
from apps.backend.rate_limit import limiter
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from ..services.agent_service import AgenticTriageService
from ..services.incident_remediation_service import IncidentRemediationService
from ..services.compliance_automation_service import ComplianceAutomationService
from ..services.audit_summary_service import AuditSummaryService
from ..services.llm_utils import get_llm_config, set_llm_config
from ..services.agentic_workflow_service import AgenticWorkflowService
from ..services.basel_compliance_service import BaselComplianceService
from ..services.metrics_service import get_metrics_service
from ..ml.anomaly_detector import get_detector
from ..security import require_role
from ..schemas import (
    AgentActionCreate,
    AgentActionUpdate,
    AgentAction,
    ComplianceMonitorTransaction,
    ComplianceDecisionResponse,
    ComplianceStatusResponse,
    AlternativeAction,
    AuditTrail,
)
from ..models import AgentAction as AgentActionModel
from ..database import get_db
import logging
import random
from datetime import datetime
from apps.backend import siem
import os
from apps.backend.main import get_logger
from opentelemetry import trace

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)
agent_service = AgenticTriageService()
remediation_service = IncidentRemediationService()
compliance_service = ComplianceAutomationService()
audit_summary_service = AuditSummaryService()
workflow_service = AgenticWorkflowService()
basel_service = BaselComplianceService()
tracer = trace.get_tracer(__name__)


@router.get("/compliance/lcr")
async def get_lcr_status(lookback_days: int = 30, db: Session = Depends(get_db)):
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
@limiter.limit("3/minute")  # LLM endpoint, strict limit
async def triage_incident(
    request: Request,
    incident: Dict[str, Any],
    db: Session = Depends(get_db)
    # user=Depends(require_role(["admin", "compliance", "analyst"]))
):
    """Run agentic triage on an incident/anomaly and submit for approval."""
    siem.send_syslog_event(
        event="Agent: Triage incident",
        host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
        port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
        extra={
            "incident_id": incident.get("incident_id"),
            "user": "test-user",
        },
    )
    try:
        import json as _json
        result = agent_service.triage_incident(incident)
        agent_action = AgentActionModel(
            incident_id=incident.get("incident_id", "unknown"),
            action="triage",
            agent_result=_json.dumps(result) if isinstance(result, dict) else str(result),
            status="pending",
            submitted_by=None,
            created_at=datetime.utcnow(),
            meta=incident,
            ai_explanation=(
                result.get("rationale") if isinstance(result, dict) else None
            ),
            agent_input=incident,
            agent_output=result if isinstance(result, dict) else {"result": result},
            agent_version=agent_service.__class__.__name__,
            actor_type="agent",
            is_simulation=incident.get("is_simulation", False),
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
        get_logger(__name__).error("Agentic triage endpoint failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions", response_model=List[AgentAction])
@limiter.limit("30/minute")  # Listing endpoint, higher limit
async def list_agent_actions(
    request: Request,
    status: str = None,
    db: Session = Depends(get_db),
):
    """List agent actions, optionally filtered by status."""
    siem.send_syslog_event(
        f"Agent: List agent actions (status={status})",
        host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
        port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    )
    try:
        query = db.query(AgentActionModel)
        if status:
            query = query.filter(AgentActionModel.status == status)
        actions = query.order_by(AgentActionModel.created_at.desc()).all()
        return actions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actions/{action_id}/approve", response_model=AgentAction)
@limiter.limit("10/minute")  # Approval endpoint, moderate limit
async def approve_agent_action(
    request: Request,
    action_id: int,
    approved_by: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"])),
):
    """Approve a pending agent action."""
    siem.send_syslog_event(
        event="Agent: Approve agent action",
        host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
        port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
        extra={
            "action_id": action_id,
            "approved_by": approved_by,
            "user": str(user.get("id") if isinstance(user, dict) else user),
        },
    )
    try:
        action = (
            db.query(AgentActionModel).filter(AgentActionModel.id == action_id).first()
        )
        if not action or action.status != "pending":
            raise HTTPException(status_code=404, detail="Pending action not found")
        action.status = "approved"
        action.approved_by = approved_by
        action.approved_at = datetime.utcnow()
        action.override_type = (
            "manual_override" if action.actor_type == "agent" else None
        )
        action.actor_type = "human"
        db.commit()
        db.refresh(action)
        # Increment compliance action metric
        from apps.backend.main import compliance_action_counter

        compliance_action_counter.add(
            1,
            {
                "type": "approve",
                "status": "approved",
                "user": str(user.get("id") if isinstance(user, dict) else user),
            },
        )
        return action
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actions/{action_id}/reject", response_model=AgentAction)
async def reject_agent_action(
    action_id: int,
    approved_by: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"])),
):
    """Reject a pending agent action."""
    siem.send_syslog_event(
        event="Agent: Reject agent action",
        host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
        port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
        extra={
            "action_id": action_id,
            "approved_by": approved_by,
            "user": str(user.get("id") if isinstance(user, dict) else user),
        },
    )
    try:
        action = (
            db.query(AgentActionModel).filter(AgentActionModel.id == action_id).first()
        )
        if not action or action.status != "pending":
            raise HTTPException(status_code=404, detail="Pending action not found")
        action.status = "rejected"
        action.approved_by = approved_by
        action.approved_at = datetime.utcnow()
        action.override_type = (
            "manual_override" if action.actor_type == "agent" else None
        )
        action.actor_type = "human"
        db.commit()
        db.refresh(action)
        # Increment compliance action metric
        from apps.backend.main import compliance_action_counter

        compliance_action_counter.add(
            1,
            {
                "type": "reject",
                "status": "rejected",
                "user": str(user.get("id") if isinstance(user, dict) else user),
            },
        )
        return action
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remediate")
async def remediate_incident(
    incident: Dict[str, Any],
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """Run agentic remediation on an incident/anomaly and submit for approval."""
    siem.send_syslog_event(
        event="Agent: Remediate incident",
        host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
        port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
        extra={
            "incident_id": incident.get("incident_id"),
            "user": str(user.get("id") if isinstance(user, dict) else user),
        },
    )
    from apps.backend.approval import require_approval

    user_id = getattr(user, "id", None) if hasattr(user, "id") else None
    approved, approval_req = require_approval(
        db=db,
        resource_type="agentic_remediation",
        resource_id=str(incident.get("incident_id", "unknown")),
        user_id=user_id,
        reason="Agentic remediation action",
        meta=incident,
    )
    if not approved:
        return {
            "detail": "Remediation action requires approval",
            "approval_request_id": approval_req.id,
            "status": approval_req.status.value,
        }
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
            ai_explanation=(
                result.get("rationale") if isinstance(result, dict) else None
            ),
            agent_input=incident,
            agent_output=result if isinstance(result, dict) else {"result": result},
            agent_version=remediation_service.__class__.__name__,
            actor_type="agent",
            is_simulation=incident.get("is_simulation", False),
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
        # Increment compliance action metric
        from apps.backend.main import compliance_action_counter

        compliance_action_counter.add(
            1,
            {
                "type": "remediate",
                "status": "pending",
                "user": str(user.get("id") if isinstance(user, dict) else user),
            },
        )
        return response
    except Exception as e:
        get_logger(__name__).error("Agentic remediation endpoint failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance")
async def automate_compliance(
    transaction: Dict[str, Any],
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """Run agentic compliance automation on a transaction/event and submit for approval."""
    siem.send_syslog_event(
        event="Agent: Automate compliance",
        host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
        port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
        extra={
            "transaction_id": transaction.get("transaction_id"),
            "user": str(user.get("id") if isinstance(user, dict) else user),
        },
    )
    from apps.backend.approval import require_approval

    user_id = getattr(user, "id", None) if hasattr(user, "id") else None
    approved, approval_req = require_approval(
        db=db,
        resource_type="agentic_compliance",
        resource_id=str(transaction.get("transaction_id", "unknown")),
        user_id=user_id,
        reason="Agentic compliance automation action",
        meta=transaction,
    )
    if not approved:
        return {
            "detail": "Compliance automation requires approval",
            "approval_request_id": approval_req.id,
            "status": approval_req.status.value,
        }
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
            ai_explanation=(
                result.get("rationale") if isinstance(result, dict) else None
            ),
            agent_input=transaction,
            agent_output=result if isinstance(result, dict) else {"result": result},
            agent_version=compliance_service.__class__.__name__,
            actor_type="agent",
            is_simulation=transaction.get("is_simulation", False),
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
        # Increment compliance action metric
        from apps.backend.main import compliance_action_counter

        compliance_action_counter.add(
            1,
            {
                "type": "compliance",
                "status": "pending",
                "user": str(user.get("id") if isinstance(user, dict) else user),
            },
        )
        return response
    except Exception as e:
        get_logger(__name__).error(
            "Agentic compliance automation endpoint failed", error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit_summary")
async def summarize_audit(
    logs: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"])),
):
    """Run agentic audit log summarization and submit for approval."""
    siem.send_syslog_event(
        event="Agent: Summarize audit logs",
        host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
        port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
        extra={"user": str(user.get("id") if isinstance(user, dict) else user)},
    )
    from apps.backend.approval import require_approval

    user_id = getattr(user, "id", None) if hasattr(user, "id") else None
    approved, approval_req = require_approval(
        db=db,
        resource_type="agentic_audit_summary",
        resource_id=f"audit_summary_{user_id}_{len(logs)}",
        user_id=user_id,
        reason="Agentic audit log summarization",
        meta={"logs_count": len(logs)},
    )
    if not approved:
        return {
            "detail": "Audit summarization requires approval",
            "approval_request_id": approval_req.id,
            "status": approval_req.status.value,
        }
    try:
        result = audit_summary_service.summarize_audit(logs)
        agent_action = AgentActionModel(
            incident_id="audit_summary",  # or derive from logs if available
            action="audit_summary",
            agent_result=result,
            status="pending",
            submitted_by=(
                user["id"] if isinstance(user, dict) and "id" in user else None
            ),
            created_at=datetime.utcnow(),
            meta={"logs": logs},
            ai_explanation=(
                result.get("rationale") if isinstance(result, dict) else None
            ),
            agent_input={"logs": logs},
            agent_output=result if isinstance(result, dict) else {"result": result},
            agent_version=audit_summary_service.__class__.__name__,
            actor_type="agent",
            is_simulation=False,
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
        # Increment compliance action metric
        from apps.backend.main import compliance_action_counter

        compliance_action_counter.add(
            1,
            {
                "type": "audit_summary",
                "status": "pending",
                "user": str(user.get("id") if isinstance(user, dict) else user),
            },
        )
        return response
    except Exception as e:
        get_logger(__name__).error(
            "Agentic audit summarization endpoint failed", error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/monitor", response_model=ComplianceDecisionResponse)
@limiter.limit("10/minute")
async def monitor_transaction_compliance(
    request: Request,
    txn: ComplianceMonitorTransaction,
    db: Session = Depends(get_db),
):
    """
    FINRA 4511 compliant transaction monitoring with agent orchestration.
    
    This endpoint:
    1. Runs anomaly detection using Isolation Forest ML model
    2. Checks compliance rules (FINRA, SEC)
    3. Makes approval/block/review decision with reasoning
    4. Logs full audit trail and tracks metrics
    
    Returns decision with confidence scores, alternatives, and feature analysis.
    """
    with tracer.start_as_current_span("agent.compliance.monitor") as span:
        span.set_attribute("transaction_id", txn.id)
        span.set_attribute("amount", txn.amount)
        span.set_attribute("type", txn.type)
        
        siem.send_syslog_event(
            event="Agent: Compliance monitor transaction",
            host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
            port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
            extra={"transaction_id": txn.id, "amount": txn.amount},
        )
        
        try:
            # Step 1: Calculate anomaly score using ML model
            detector = get_detector()
            anomaly_score, feature_details = detector.predict(
                amount=txn.amount,
                timestamp=txn.timestamp,
                txn_type=txn.type
            )
            span.set_attribute("anomaly_score", anomaly_score)
            span.set_attribute("model_version", feature_details.get("model_version", "unknown"))
            
            # Step 2: Check compliance rules
            compliance_violation = _check_compliance_rules(txn)
            
            # Build risk factors string for reasoning
            risk_factors = feature_details.get("risk_factors", [])
            risk_str = "; ".join(risk_factors) if risk_factors else "None identified"
            
            # Step 3: Make decision
            if compliance_violation:
                decision = ComplianceDecisionResponse(
                    action="block",
                    confidence=95.0,
                    reasoning=f"Regulatory violation: {compliance_violation['description']}",
                    alternatives=[],
                    audit_trail=AuditTrail(
                        regulation="FINRA_4511",
                        timestamp=datetime.utcnow(),
                        agent="ComplianceChecker"
                    )
                )
            elif anomaly_score > 0.7:
                decision = ComplianceDecisionResponse(
                    action="manual_review",
                    confidence=85.0,
                    reasoning=f"High anomaly score ({anomaly_score:.3f}) requires human review. Risk factors: {risk_str}. Model: IsolationForest v{feature_details.get('model_version', '2.0.0')}",
                    alternatives=[
                        AlternativeAction(
                            action="approve",
                            confidence=0.1,
                            reasoning="Could be legitimate large transaction"
                        ),
                        AlternativeAction(
                            action="block",
                            confidence=0.05,
                            reasoning="Too risky to auto-approve"
                        )
                    ],
                    audit_trail=AuditTrail(
                        regulation="SEC_17a4",
                        timestamp=datetime.utcnow(),
                        agent="AnomalyDetector"
                    )
                )
            elif anomaly_score > 0.4:
                decision = ComplianceDecisionResponse(
                    action="approve",
                    confidence=75.0,
                    reasoning=f"Transaction approved with elevated monitoring. Anomaly score: {anomaly_score:.3f}. Risk factors: {risk_str}",
                    alternatives=[
                        AlternativeAction(
                            action="manual_review",
                            confidence=0.2,
                            reasoning="Borderline score may warrant review"
                        )
                    ],
                    audit_trail=AuditTrail(
                        regulation="FINRA_4511",
                        timestamp=datetime.utcnow(),
                        agent="ComplianceChecker"
                    )
                )
            else:
                decision = ComplianceDecisionResponse(
                    action="approve",
                    confidence=90.0,
                    reasoning=f"Transaction passed all compliance checks. Anomaly score: {anomaly_score:.3f} (within normal parameters).",
                    alternatives=[],
                    audit_trail=AuditTrail(
                        regulation="FINRA_4511",
                        timestamp=datetime.utcnow(),
                        agent="ComplianceChecker"
                    )
                )
            
            span.set_attribute("decision", decision.action)
            span.set_attribute("confidence", decision.confidence)
            
            # Track metrics in Redis
            metrics_service = get_metrics_service()
            metrics_service.increment_transaction(decision.action, decision.confidence)
            
            # Increment OpenTelemetry compliance action metric
            from apps.backend.main import compliance_action_counter
            compliance_action_counter.add(
                1,
                {"type": "compliance_monitor", "action": decision.action},
            )
            
            return decision
            
        except Exception as e:
            span.record_exception(e)
            get_logger(__name__).error("Compliance monitor endpoint failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/status", response_model=ComplianceStatusResponse)
async def get_compliance_agent_status():
    """
    Health check endpoint for compliance agent.
    """
    detector = get_detector()
    model_info = detector.get_model_info()
    
    return ComplianceStatusResponse(
        status="operational",
        agent="FinancialComplianceAgent",
        version=model_info.get("version", "2.0.0"),
        regulations=["FINRA_4511", "SEC_17a4"],
        features=[
            "isolation_forest_ml",
            "compliance_rules",
            "audit_trails",
            "human_in_the_loop",
            "redis_metrics"
        ]
    )


@router.get("/compliance/metrics")
async def get_compliance_metrics():
    """
    Get real-time compliance monitoring metrics from Redis.
    
    Returns:
        - Total transactions processed
        - Approval/block/review rates
        - Average confidence score
        - Confidence percentiles (p50, p90, p99)
    """
    metrics_service = get_metrics_service()
    metrics = metrics_service.get_metrics()
    
    # Add model info
    detector = get_detector()
    model_info = detector.get_model_info()
    metrics["model"] = model_info
    
    return metrics


@router.post("/compliance/metrics/reset")
async def reset_compliance_metrics(
    user=Depends(require_role(["admin"]))
):
    """
    Admin-only: Reset all compliance metrics counters.
    """
    metrics_service = get_metrics_service()
    result = metrics_service.reset_metrics()
    return result


@router.post("/compliance/feedback")
async def submit_compliance_feedback(
    request: Request,
    transaction_id: str,
    predicted_action: str,
    actual_action: str,
    confidence: float = None,
    anomaly_score: float = None,
    notes: str = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """
    Submit feedback on a compliance decision for precision/recall tracking.

    Analysts mark whether the model's prediction was correct.
    """
    from ..models import ComplianceFeedback

    is_correct = predicted_action == actual_action
    feedback = ComplianceFeedback(
        transaction_id=transaction_id,
        predicted_action=predicted_action,
        actual_action=actual_action,
        is_correct=is_correct,
        confidence=confidence,
        anomaly_score=anomaly_score,
        reviewer_id=getattr(user, "id", None),
        notes=notes,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {
        "id": feedback.id,
        "transaction_id": transaction_id,
        "predicted_action": predicted_action,
        "actual_action": actual_action,
        "is_correct": is_correct,
    }


@router.get("/compliance/metrics/evaluation")
async def get_model_evaluation(
    days: int = 30,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """
    Get precision, recall, F1, and confusion matrix from analyst feedback.
    Requires at least 10 feedback samples.
    """
    from ..ml.evaluation import ModelEvaluator

    evaluator = ModelEvaluator()
    return evaluator.compute_metrics(db, days=days)


@router.get("/compliance/metrics/calibration")
async def get_confidence_calibration(
    days: int = 30,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """
    Get confidence calibration data: are high-confidence predictions more accurate?
    """
    from ..ml.evaluation import ModelEvaluator

    evaluator = ModelEvaluator()
    return evaluator.compute_confidence_calibration(db, days=days)


@router.get("/compliance/metrics/confusion")
async def get_confusion_matrix(
    days: int = 30,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """
    Get just the confusion matrix from feedback data.
    """
    from ..ml.evaluation import ModelEvaluator

    evaluator = ModelEvaluator()
    result = evaluator.compute_metrics(db, days=days)
    if result.get("status") != "ok":
        return result
    return {
        "confusion_matrix": result["confusion_matrix"],
        "total_feedback": result["total_feedback"],
        "accuracy": result["accuracy"],
    }


@router.post("/compliance/retrain")
@limiter.limit("1/minute")
async def retrain_compliance_model(
    request: Request,
    user=Depends(require_role(["admin"])),
):
    """
    Admin-only: Retrain the anomaly detection model from the bundled dataset.
    Bumps model version automatically.
    """
    detector = get_detector()
    result = detector.retrain_from_csv()
    return result


@router.post("/compliance/retrain/scheduled")
@limiter.limit("1/minute")
async def trigger_scheduled_retrain(
    request: Request,
    user=Depends(require_role(["admin"])),
):
    """
    Admin-only: Manually trigger the automated retraining pipeline.
    Same as the scheduled job but on-demand.
    """
    from ..ml.retraining_pipeline import get_retraining_pipeline

    pipeline = get_retraining_pipeline()
    return pipeline.run()


@router.get("/compliance/retrain/status")
async def get_retrain_status(
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """Get the status of the automated retraining pipeline."""
    from ..ml.retraining_pipeline import get_retraining_pipeline

    pipeline = get_retraining_pipeline()
    return pipeline.get_status()


@router.post("/compliance/explain")
async def explain_compliance_decision(
    request: Request,
    transaction: dict,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """
    Explain a compliance decision using SHAP values.
    Shows which features contributed most to the anomaly score.
    """
    from ..ml.explainability import explain_prediction
    from dateutil.parser import parse as parse_date

    detector = get_detector()
    ts = transaction.get("timestamp")
    if isinstance(ts, str):
        ts = parse_date(ts)
    elif ts is None:
        ts = datetime.utcnow()

    result = explain_prediction(
        detector,
        amount=float(transaction.get("amount", 0)),
        timestamp=ts,
        txn_type=transaction.get("type", "ach"),
    )
    return result


@router.post("/compliance/explain-batch")
async def explain_compliance_batch(
    request: Request,
    transactions: list,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """
    Get aggregate feature importance across a batch of transactions.
    Returns mean absolute SHAP values per feature.
    """
    from ..ml.explainability import explain_batch

    detector = get_detector()
    result = explain_batch(detector, transactions)
    return result


@router.post("/compliance/ensemble")
async def ensemble_compliance_check(
    request: Request,
    transaction: dict,
    transaction_history: list = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """
    Run ensemble anomaly detection combining Isolation Forest + sequence model.
    Optionally provide transaction_history for sequence-based analysis.
    """
    from ..ml.ensemble import get_ensemble_detector
    from dateutil.parser import parse as parse_date

    ensemble = get_ensemble_detector()
    ts = transaction.get("timestamp")
    if isinstance(ts, str):
        ts = parse_date(ts)
    elif ts is None:
        ts = datetime.utcnow()

    score, details = ensemble.predict(
        amount=float(transaction.get("amount", 0)),
        timestamp=ts,
        txn_type=transaction.get("type", "ach"),
        transaction_history=transaction_history,
    )
    return {
        "score": score,
        "details": details,
    }


@router.get("/compliance/model/ensemble")
async def get_ensemble_info(
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """
    Get ensemble model metadata including individual model scores and weights.
    """
    from ..ml.ensemble import get_ensemble_detector

    ensemble = get_ensemble_detector()
    return ensemble.get_model_info()


# --- A/B Testing Endpoints ---

@router.post("/compliance/experiments")
async def create_experiment(
    request: Request,
    name: str,
    model_a: str = "isolation_forest",
    model_b: str = "ensemble",
    traffic_split: int = 50,
    user=Depends(require_role(["admin"])),
):
    """
    Admin-only: Create a new A/B test experiment between model variants.
    traffic_split = % of traffic routed to model_a (rest goes to model_b).
    """
    from ..ml.ab_testing import get_ab_manager

    manager = get_ab_manager()
    return manager.create_experiment(name, model_a, model_b, traffic_split)


@router.get("/compliance/experiments")
async def list_experiments(
    active_only: bool = True,
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """List all A/B test experiments."""
    from ..ml.ab_testing import get_ab_manager

    manager = get_ab_manager()
    return manager.list_experiments(active_only=active_only)


@router.get("/compliance/experiments/{experiment_id}/results")
async def get_experiment_results(
    experiment_id: str,
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """Get A/B test results with statistical significance testing."""
    from ..ml.ab_testing import get_ab_manager

    manager = get_ab_manager()
    return manager.get_results(experiment_id)


@router.post("/compliance/experiments/{experiment_id}/promote")
async def promote_experiment_winner(
    experiment_id: str,
    user=Depends(require_role(["admin"])),
):
    """Admin-only: Promote the winning model variant and close the experiment."""
    from ..ml.ab_testing import get_ab_manager

    manager = get_ab_manager()
    return manager.promote_winner(experiment_id)


# --- Evaluation / Audit Trail Endpoints ---

@router.post("/compliance/eval/submit")
async def submit_eval_batch(
    request: Request,
    predictions: list,
    model_version: str = None,
    user=Depends(require_role(["admin", "compliance"])),
):
    """
    Submit a batch of predictions with ground truth for evaluation.
    Each item: {transaction_id, predicted_action, actual_action}
    """
    from ..services.evalai_service import get_evalai_service

    service = get_evalai_service()
    return service.submit_batch(predictions, model_version=model_version)


@router.get("/compliance/eval/results")
async def get_eval_results(
    limit: int = 10,
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """Get recent evaluation results."""
    from ..services.evalai_service import get_evalai_service

    service = get_evalai_service()
    return service.get_results(limit=limit)


@router.get("/compliance/eval/leaderboard")
async def get_eval_leaderboard(
    user=Depends(require_role(["admin", "compliance", "analyst"])),
):
    """Get leaderboard of model versions ranked by F1 score."""
    from ..services.evalai_service import get_evalai_service

    service = get_evalai_service()
    return service.get_leaderboard()


@router.get("/compliance/eval/audit-trail")
async def get_eval_audit_trail(
    model_version: str = None,
    user=Depends(require_role(["admin", "compliance"])),
):
    """Get full audit trail of evaluations, optionally filtered by model version."""
    from ..services.evalai_service import get_evalai_service

    service = get_evalai_service()
    return service.get_audit_trail(model_version=model_version)


@router.post("/compliance/test-batch")
@limiter.limit("2/minute")
async def run_compliance_test_batch(
    request: Request,
    count: int = 100,
):
    """
    Generate and test synthetic transactions for validation.
    
    Args:
        count: Number of transactions to generate (default 100, max 500)
    
    Distribution:
        - 70% normal: $100-$5000, business hours, weekdays
        - 20% suspicious: $10k-$50k, off-hours or weekends
        - 10% violations: $100k+, any time
    
    Returns:
        Aggregated results and individual transaction details.
    """
    count = min(count, 500)  # Cap at 500
    
    results = {
        "total": count,
        "approved": 0,
        "blocked": 0,
        "manual_review": 0,
        "avg_confidence": 0.0,
        "transactions": []
    }
    
    confidences = []
    detector = get_detector()
    metrics_service = get_metrics_service()
    
    for i in range(count):
        rand = random.random()
        
        if rand < 0.7:
            # Normal transaction
            amount = random.randint(100, 5000)
            hour = random.randint(9, 17)
            day = random.randint(0, 4)  # Weekday
            txn_type = random.choice(["ach", "internal", "wire"])
        elif rand < 0.9:
            # Suspicious transaction
            amount = random.randint(10000, 50000)
            hour = random.choice([random.randint(0, 5), random.randint(22, 23)])
            day = random.randint(0, 6)
            txn_type = random.choice(["wire", "ach"])
        else:
            # Violation transaction
            amount = random.randint(100000, 200000)
            hour = random.randint(0, 23)
            day = random.randint(0, 6)
            txn_type = "wire"
        
        # Create timestamp for the transaction
        now = datetime.utcnow()
        timestamp = now.replace(
            hour=hour,
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )
        # Adjust day of week (this is simplified - just for testing)
        
        # Get anomaly score
        anomaly_score, feature_details = detector.predict(
            amount=amount,
            timestamp=timestamp,
            txn_type=txn_type
        )
        
        # Check compliance rules
        compliance_violation = None
        if amount > 100000:
            compliance_violation = {
                "rule": "FINRA_4511_LARGE_TRANSACTION",
                "description": "Transactions over $100,000 require manual compliance review"
            }
        
        # Determine action
        if compliance_violation:
            action = "blocked"
            confidence = 95.0
        elif anomaly_score > 0.7:
            action = "manual_review"
            confidence = 85.0
        elif anomaly_score > 0.4:
            action = "approved"
            confidence = 75.0
        else:
            action = "approved"
            confidence = 90.0
        
        results[action] += 1
        confidences.append(confidence)
        
        # Track in metrics
        metrics_service.increment_transaction(action, confidence)
        
        # Add to results (limit detail to first 20)
        if len(results["transactions"]) < 20:
            results["transactions"].append({
                "id": f"test_{i}",
                "amount": amount,
                "type": txn_type,
                "hour": hour,
                "anomaly_score": round(anomaly_score, 3),
                "action": action,
                "confidence": confidence
            })
    
    results["avg_confidence"] = round(sum(confidences) / len(confidences), 2)
    results["approval_rate"] = round(results["approved"] / count * 100, 2)
    results["block_rate"] = round(results["blocked"] / count * 100, 2)
    results["manual_review_rate"] = round(results["manual_review"] / count * 100, 2)
    
    return results


def _calculate_anomaly_score(txn: ComplianceMonitorTransaction) -> float:
    """
    Calculate anomaly score using heuristics.
    Replace with actual ML model call for production.
    """
    score = 0.0
    
    # Large amount check
    if txn.amount > 50000:
        score += 0.4
    elif txn.amount > 10000:
        score += 0.2
    
    # Time-based check
    hour = txn.timestamp.hour
    if hour < 6 or hour > 22:  # Off-hours
        score += 0.3
    
    # Wire transfer check
    if txn.type == "wire" and txn.amount > 10000:
        score += 0.2
    
    return min(score, 1.0)


def _check_compliance_rules(txn: ComplianceMonitorTransaction) -> dict | None:
    """
    Check FINRA 4511 and SEC 17a-4 compliance rules.
    """
    # Rule: Extremely large transactions require manual review
    if txn.amount > 100000:
        return {
            "rule": "FINRA_4511_LARGE_TRANSACTION",
            "description": "Transactions over $100,000 require manual compliance review"
        }
    
    return None


# --- LLM Configuration Endpoints ---

@router.get("/config")
async def get_agent_config():
    """
    Get current LLM configuration including provider, model, and available options.
    """
    return get_llm_config()


@router.post("/config/model")
async def update_agent_model(
    provider: str = None,
    model: str = None,
    user=Depends(require_role(["admin"])),
):
    """
    Admin-only: Update the LLM provider and/or model at runtime.
    Changes take effect immediately for all subsequent agent calls.
    """
    try:
        return set_llm_config(provider=provider, model=model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
