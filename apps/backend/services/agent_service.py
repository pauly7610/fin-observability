from typing import Dict, Any, Optional
import logging
from pydantic import BaseModel, Field
from opentelemetry import trace

from .llm_utils import structured_llm_call, get_llm_config

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

TRIAGE_SYSTEM_PROMPT = """You are a financial incident triage specialist. Analyze the incident description and classify its severity.

You must assess:
1. Risk level (high, medium, or low)
2. Your confidence in the assessment (0.0 to 1.0)
3. A clear rationale explaining your reasoning
4. A recommended next action

Consider financial domain factors: regulatory impact, customer exposure, data breach potential, fraud indicators, and operational disruption."""


class TriageResult(BaseModel):
    """Structured output schema for incident triage."""
    risk_level: str = Field(description="Risk level: 'high', 'medium', or 'low'")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    rationale: str = Field(description="Explanation of the risk assessment")
    recommendation: Optional[str] = Field(default=None, description="Recommended next action")


def classify_incident(incident: str) -> dict:
    """Classifies the severity of an incident using LLM with keyword heuristic fallback."""
    # Try LLM first
    llm_result = structured_llm_call(
        system_prompt=TRIAGE_SYSTEM_PROMPT,
        user_input=f"Classify this incident:\n\n{incident}",
        output_schema=TriageResult,
    )
    if llm_result is not None:
        result = llm_result.model_dump()
        result["source"] = "llm"
        result["model"] = get_llm_config().get("model")
        return result

    # Keyword heuristic fallback
    text = incident.lower()
    if any(word in text for word in ["urgent", "critical", "breach", "fraud", "loss"]):
        result = {
            "risk_level": "high",
            "confidence": 0.99,
            "rationale": "Incident contains keywords indicating a high-risk event (e.g., urgent, breach, fraud).",
        }
    elif any(word in text for word in ["warning", "delay", "error", "timeout"]):
        result = {
            "risk_level": "medium",
            "confidence": 0.95,
            "rationale": "Incident contains warning or error indicators, suggesting medium risk.",
        }
    else:
        result = {
            "risk_level": "low",
            "confidence": 0.99,
            "rationale": "No high-risk or warning keywords detected; likely low risk.",
        }
    result["source"] = "heuristic"
    result["model"] = None
    return result


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
                span.set_attribute("result.source", result.get("source", "unknown"))
                return result
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Agentic triage failed: {str(e)}")
                return {
                    "risk_level": "error",
                    "confidence": 0.0,
                    "rationale": f"Agent error: {str(e)}",
                    "recommendation": "Manual review required.",
                    "source": "error",
                    "model": None,
                }
