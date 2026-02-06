from typing import Dict, Any
import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def classify_incident(incident: str) -> dict:
    """Classifies the severity of an incident as low, medium, or high based on its description, with confidence and rationale."""
    text = incident.lower()
    if any(word in text for word in ["urgent", "critical", "breach", "fraud", "loss"]):
        return {
            "risk_level": "high",
            "confidence": 0.99,
            "rationale": "Incident contains keywords indicating a high-risk event (e.g., urgent, breach, fraud).",
        }
    elif any(word in text for word in ["warning", "delay", "error", "timeout"]):
        return {
            "risk_level": "medium",
            "confidence": 0.95,
            "rationale": "Incident contains warning or error indicators, suggesting medium risk.",
        }
    else:
        return {
            "risk_level": "low",
            "confidence": 0.99,
            "rationale": "No high-risk or warning keywords detected; likely low risk.",
        }


class AgenticTriageService:
    def triage_incident(self, incident: Dict[str, Any]) -> dict:
        incident_id = incident.get("incident_id", "unknown")
        user_id = incident.get("user_id")
        incident_str = str(incident)
        with tracer.start_as_current_span("agent.triage_incident") as span:
            span.set_attribute("incident.id", incident_id)
            if user_id is not None:
                span.set_attribute("user.id", str(user_id))
            span.set_attribute("input_size", len(incident_str))
            try:
                result = classify_incident(incident_str)
                span.set_attribute("result.risk_level", result.get("risk_level", "unknown"))
                return result
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Agentic triage failed: {str(e)}")
                return {
                    "risk_level": "error",
                    "confidence": 0.0,
                    "rationale": f"Agent error: {str(e)}",
                    "recommendation": "Manual review required.",
                }
