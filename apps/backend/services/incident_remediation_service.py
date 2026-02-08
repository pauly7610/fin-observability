from typing import Dict, Any, Optional
import logging
from pydantic import BaseModel, Field
from opentelemetry import trace

from .llm_utils import structured_llm_call, get_llm_config

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

REMEDIATION_SYSTEM_PROMPT = """You are a financial incident remediation specialist. Given an incident description, recommend specific remediation steps.

You must assess:
1. Risk level (high, medium, or low)
2. Your confidence in the recommendation (0.0 to 1.0)
3. A rationale explaining why this remediation is appropriate
4. Specific, actionable remediation steps

Consider: service dependencies, blast radius, rollback procedures, regulatory notification requirements, and customer impact mitigation."""


class RemediationResult(BaseModel):
    """Structured output schema for incident remediation."""
    risk_level: str = Field(description="Risk level: 'high', 'medium', or 'low'")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    rationale: str = Field(description="Explanation of the remediation recommendation")
    recommendation: str = Field(description="Specific remediation steps to take")


def recommend_remediation(incident: str) -> dict:
    """Recommend remediation steps using LLM with keyword heuristic fallback."""
    # Try LLM first
    llm_result = structured_llm_call(
        system_prompt=REMEDIATION_SYSTEM_PROMPT,
        user_input=f"Recommend remediation for this incident:\n\n{incident}",
        output_schema=RemediationResult,
    )
    if llm_result is not None:
        result = llm_result.model_dump()
        result["source"] = "llm"
        result["model"] = get_llm_config().get("model")
        return result

    # Keyword heuristic fallback
    text = incident.lower()
    if any(word in text for word in ["breach", "fraud", "loss", "critical"]):
        result = {
            "risk_level": "high",
            "confidence": 0.99,
            "rationale": "Critical incident keywords detected. Escalation required.",
            "recommendation": "Escalate to security team and initiate incident response protocol.",
        }
    elif any(word in text for word in ["timeout", "delay", "error"]):
        result = {
            "risk_level": "medium",
            "confidence": 0.95,
            "rationale": "Service errors/timeouts detected. Engineering action needed.",
            "recommendation": "Notify engineering, restart affected service, monitor for recurrence.",
        }
    elif any(word in text for word in ["warning", "minor"]):
        result = {
            "risk_level": "low",
            "confidence": 0.98,
            "rationale": "Minor warning or non-critical issue detected.",
            "recommendation": "Log and monitor. No immediate action required.",
        }
    else:
        result = {
            "risk_level": "medium",
            "confidence": 0.7,
            "rationale": "Unrecognized pattern. Manual review recommended.",
            "recommendation": "Review manually.",
        }
    result["source"] = "heuristic"
    result["model"] = None
    return result


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
                span.set_attribute("result.source", result.get("source", "unknown"))
                return result
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Incident remediation failed: {str(e)}")
                return {
                    "risk_level": "error",
                    "confidence": 0.0,
                    "rationale": f"Agent error: {str(e)}",
                    "recommendation": "Manual review required.",
                    "source": "error",
                    "model": None,
                }
