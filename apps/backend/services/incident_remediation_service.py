from typing import Dict, Any
import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def recommend_remediation(incident: str) -> dict:
    """Given incident details, recommend remediation steps, risk, confidence, and rationale."""
    text = incident.lower()
    if any(word in text for word in ["breach", "fraud", "loss", "critical"]):
        return {
            "risk_level": "high",
            "confidence": 0.99,
            "rationale": "Critical incident keywords detected. Escalation required.",
            "recommendation": "Escalate to security team and initiate incident response protocol.",
        }
    elif any(word in text for word in ["timeout", "delay", "error"]):
        return {
            "risk_level": "medium",
            "confidence": 0.95,
            "rationale": "Service errors/timeouts detected. Engineering action needed.",
            "recommendation": "Notify engineering, restart affected service, monitor for recurrence.",
        }
    elif any(word in text for word in ["warning", "minor"]):
        return {
            "risk_level": "low",
            "confidence": 0.98,
            "rationale": "Minor warning or non-critical issue detected.",
            "recommendation": "Log and monitor. No immediate action required.",
        }
    else:
        return {
            "risk_level": "medium",
            "confidence": 0.7,
            "rationale": "Unrecognized pattern. Manual review recommended.",
            "recommendation": "Review manually.",
        }


class IncidentRemediationService:
    def remediate_incident(self, incident: Dict[str, Any], user_id: str = None) -> dict:
        incident_id = incident.get("incident_id", "unknown")
        incident_str = str(incident)
        with tracer.start_as_current_span("agent.remediate_incident") as span:
            span.set_attribute("incident.id", incident_id)
            if user_id is not None:
                span.set_attribute("user.id", user_id)
            span.set_attribute("input_size", len(incident_str))
            try:
                result = recommend_remediation(incident_str)
                span.set_attribute("result.risk_level", result.get("risk_level", "unknown"))
                return result
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Incident remediation failed: {str(e)}")
                return {
                    "risk_level": "error",
                    "confidence": 0.0,
                    "rationale": f"Agent error: {str(e)}",
                    "recommendation": "Manual review required.",
                }
