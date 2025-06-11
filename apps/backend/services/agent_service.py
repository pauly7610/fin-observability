from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from typing import Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


# Define tools using @tool decorator for LangGraph compatibility
@tool
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


@tool
def echo(input_str: str) -> str:
    """Echoes the input."""
    return input_str


class TriageState(BaseModel):
    input: str
    output: Any = None


class AgenticTriageService:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)
        self.tools = [classify_incident, echo]

    def triage_incident(self, incident: Dict[str, Any]) -> dict:
        prompt = (
            "Given the following incident or anomaly, classify its severity using the classify_incident tool, "
            "and recommend remediation steps using the recommend_remediation tool. "
            f"Incident: {incident}"
        )
        incident_id = incident.get("incident_id", "unknown")
        with tracer.start_as_current_span("agent.triage_incident") as span:
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
                        "recommendation": output,
                    }
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Agentic triage failed: {str(e)}")
                return {
                    "risk_level": "error",
                    "confidence": 0.0,
                    "rationale": f"Agent error: {str(e)}",
                    "recommendation": "Manual review required.",
                }
