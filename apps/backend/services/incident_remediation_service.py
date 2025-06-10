from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import Any
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from langchain_core.tools import tool
from typing import Dict, Any
import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

@tool
def recommend_remediation(incident: str) -> dict:
    """Given incident details, recommend remediation steps, risk, confidence, and rationale."""
    text = incident.lower()
    if any(word in text for word in ["breach", "fraud", "loss", "critical"]):
        return {
            "risk_level": "high",
            "confidence": 0.99,
            "rationale": "Critical incident keywords detected. Escalation required.",
            "recommendation": "Escalate to security team and initiate incident response protocol."
        }
    elif any(word in text for word in ["timeout", "delay", "error"]):
        return {
            "risk_level": "medium",
            "confidence": 0.95,
            "rationale": "Service errors/timeouts detected. Engineering action needed.",
            "recommendation": "Notify engineering, restart affected service, monitor for recurrence."
        }
    elif any(word in text for word in ["warning", "minor"]):
        return {
            "risk_level": "low",
            "confidence": 0.98,
            "rationale": "Minor warning or non-critical issue detected.",
            "recommendation": "Log and monitor. No immediate action required."
        }
    else:
        return {
            "risk_level": "medium",
            "confidence": 0.7,
            "rationale": "Unrecognized pattern. Manual review recommended.",
            "recommendation": "Review manually."
        }

@tool
def classify_incident(incident: str) -> dict:
    """Classifies the severity of an incident as low, medium, or high with confidence and rationale."""
    text = incident.lower()
    if any(word in text for word in ["urgent", "critical", "breach", "fraud", "loss"]):
        return {
            "risk_level": "high",
            "confidence": 0.99,
            "rationale": "Incident contains urgent/critical/fraud keywords."
        }
    elif any(word in text for word in ["warning", "delay", "error", "timeout"]):
        return {
            "risk_level": "medium",
            "confidence": 0.95,
            "rationale": "Incident contains warning or error indicators."
        }
    else:
        return {
            "risk_level": "low",
            "confidence": 0.99,
            "rationale": "No high-risk or warning keywords detected; likely low risk."
        }

class IncidentRemediationService:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)
        self.tools = [recommend_remediation, classify_incident]
        self.agent = create_react_agent(self.llm, self.tools)
        from pydantic import BaseModel
        class RemediationState(BaseModel):
            input: str
            output: Any = None
        workflow = StateGraph(RemediationState)
        workflow.add_node("agent", self.agent)
        workflow.set_entry_point("agent")
        workflow.set_finish_point("agent")
        self.workflow = workflow.compile()

    def remediate_incident(self, incident: Dict[str, Any], user_id: str = None) -> dict:
        prompt = (
            "Given the following incident, classify its severity using the classify_incident tool, "
            "and recommend remediation steps using the recommend_remediation tool. "
            f"Incident: {incident}"
        )
        incident_id = incident.get('incident_id', 'unknown')
        with tracer.start_as_current_span("agent.remediate_incident") as span:
            span.set_attribute("incident.id", incident_id)
            if user_id is not None:
                span.set_attribute("user.id", user_id)
            span.set_attribute("llm.input_size", len(str(prompt)))
            try:
                result = self.workflow.invoke({"input": prompt})
                output = result.get("output", str(result))
                if isinstance(output, dict):
                    span.set_attribute("llm.result_type", "dict")
                    return output
                else:
                    span.set_attribute("llm.result_type", "unstructured")
                    return {
                        "risk_level": "unknown",
                        "confidence": 0.0,
                        "rationale": "Agent returned unstructured output.",
                        "recommendation": output
                    }
            except Exception as e:
                span.record_exception(e)
                from apps.backend.main import get_logger
                get_logger(__name__).error("Incident remediation failed", error=str(e))
                return {
                    "risk_level": "error",
                    "confidence": 0.0,
                    "rationale": f"Agent error: {str(e)}",
                    "recommendation": "Manual review required."
                }
