from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
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
            "rationale": "Incident contains keywords indicating a high-risk event (e.g., urgent, breach, fraud)."
        }
    elif any(word in text for word in ["warning", "delay", "error", "timeout"]):
        return {
            "risk_level": "medium",
            "confidence": 0.95,
            "rationale": "Incident contains warning or error indicators, suggesting medium risk."
        }
    else:
        return {
            "risk_level": "low",
            "confidence": 0.99,
            "rationale": "No high-risk or warning keywords detected; likely low risk."
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
        self.agent = create_react_agent(self.llm, self.tools)
        # Build a simple LangGraph workflow
        workflow = StateGraph(TriageState)
        workflow.add_node("agent", self.agent)
        workflow.set_entry_point("agent")
        workflow.set_finish_point("agent")
        self.workflow = workflow.compile()

    def triage_incident(self, incident: Dict[str, Any]) -> dict:
        prompt = (
            "Given the following incident, classify its severity using the classify_incident tool, "
            "and provide a recommended triage action. "
            f"Incident: {incident}"
        )
        try:
            result = self.workflow.invoke({"input": prompt})
            output = result.get("output", str(result))
            # If output is a string, wrap it in a dict; otherwise, expect dict from classify_incident
            if isinstance(output, dict):
                recommendation = f"Recommended triage action for risk level '{output['risk_level']}': escalate if medium/high, monitor if low."
                output["recommendation"] = recommendation
                return output
            else:
                return {
                    "risk_level": "unknown",
                    "confidence": 0.0,
                    "rationale": "Agent returned unstructured output.",
                    "recommendation": output
                }
        except Exception as e:
            logger.error(f"Agentic triage failed: {str(e)}")
            return {
                "risk_level": "error",
                "confidence": 0.0,
                "rationale": f"Agent error: {str(e)}",
                "recommendation": "Manual review required."
            }
