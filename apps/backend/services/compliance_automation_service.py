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
def check_compliance(transaction: str) -> dict:
    """Check if a transaction or event violates compliance rules, with risk, confidence, rationale, and recommendation."""
    text = transaction.lower()
    if any(word in text for word in ["sanction", "blocked", "prohibited", "blacklist"]):
        return {
            "risk_level": "high",
            "confidence": 0.99,
            "rationale": "Potential violation of sanctions or prohibited list.",
            "recommendation": "Flag for compliance review."
        }
    elif any(word in text for word in ["large cash", "unusual transfer", "offshore"]):
        return {
            "risk_level": "medium",
            "confidence": 0.95,
            "rationale": "Unusual transfer or offshore activity detected.",
            "recommendation": "Escalate for enhanced due diligence."
        }
    elif any(word in text for word in ["approved", "ok", "cleared"]):
        return {
            "risk_level": "low",
            "confidence": 0.99,
            "rationale": "Transaction is approved/cleared.",
            "recommendation": "Approve. No compliance issue detected."
        }
    else:
        return {
            "risk_level": "low",
            "confidence": 0.95,
            "rationale": "No immediate compliance issue detected.",
            "recommendation": "Monitor."
        }

@tool
def recommend_compliance_action(transaction: str) -> dict:
    """Recommend a compliance action based on transaction details, with risk, confidence, rationale, and recommendation."""
    text = transaction.lower()
    if "flag" in text or "escalate" in text:
        return {
            "risk_level": "medium",
            "confidence": 0.9,
            "rationale": "Flag/escalate detected in transaction details.",
            "recommendation": "Notify compliance officer and require manual review."
        }
    elif "approve" in text:
        return {
            "risk_level": "low",
            "confidence": 0.99,
            "rationale": "Transaction is approved.",
            "recommendation": "Auto-approve."
        }
    else:
        return {
            "risk_level": "low",
            "confidence": 0.95,
            "rationale": "No compliance action required.",
            "recommendation": "Monitor transaction."
        }

class ComplianceAutomationService:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)
        self.tools = [check_compliance, recommend_compliance_action]
        self.agent = create_react_agent(self.llm, self.tools)
        from pydantic import BaseModel
        class ComplianceState(BaseModel):
            input: str
            output: Any = None
        workflow = StateGraph(ComplianceState)
        workflow.add_node("agent", self.agent)
        workflow.set_entry_point("agent")
        workflow.set_finish_point("agent")
        self.workflow = workflow.compile()

    def automate_compliance(self, transaction: Dict[str, Any], user_id: str = None) -> dict:
        prompt = (
            "Given the following transaction or event, check for compliance issues using the check_compliance tool, "
            "and recommend a compliance action using the recommend_compliance_action tool. "
            f"Transaction: {transaction}"
        )
        transaction_id = transaction.get('transaction_id', 'unknown')
        with tracer.start_as_current_span("agent.automate_compliance") as span:
            span.set_attribute("transaction.id", transaction_id)
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
                get_logger(__name__).error("Compliance automation failed", error=str(e))
                return {
                    "risk_level": "error",
                    "confidence": 0.0,
                    "rationale": f"Agent error: {str(e)}",
                    "recommendation": "Manual review required."
                }
