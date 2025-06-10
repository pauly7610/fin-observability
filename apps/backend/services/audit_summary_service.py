from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import Any
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from langchain_core.tools import tool
from typing import Dict, Any, List
import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

@tool
def summarize_audit_logs(logs: str) -> dict:
    """Summarize a list of audit log entries, highlighting key events and anomalies, with risk, confidence, rationale, and recommendation."""
    if "anomaly" in logs.lower() or "error" in logs.lower():
        return {
            "risk_level": "high",
            "confidence": 0.98,
            "rationale": "Anomalies or errors detected in audit logs.",
            "recommendation": "Immediate review recommended."
        }
    elif "login" in logs.lower() and "failed" in logs.lower():
        return {
            "risk_level": "medium",
            "confidence": 0.95,
            "rationale": "Multiple failed logins detected.",
            "recommendation": "Possible brute-force attempt. Investigate user accounts."
        }
    else:
        return {
            "risk_level": "low",
            "confidence": 0.99,
            "rationale": "No critical events detected in audit logs.",
            "recommendation": "Log for record-keeping. No immediate action."
        }

@tool
def recommend_audit_action(summary: str) -> dict:
    """Recommend follow-up actions based on the audit log summary, with risk, confidence, rationale, and recommendation."""
    if "anomaly" in summary or "error" in summary:
        return {
            "risk_level": "high",
            "confidence": 0.97,
            "rationale": "Escalation required due to anomalies/errors.",
            "recommendation": "Escalate to compliance and security teams."
        }
    elif "failed login" in summary:
        return {
            "risk_level": "medium",
            "confidence": 0.93,
            "rationale": "Potential brute-force attack detected.",
            "recommendation": "Initiate user account lockout and notify admin."
        }
    else:
        return {
            "risk_level": "low",
            "confidence": 0.99,
            "rationale": "No immediate action required.",
            "recommendation": "Log for record-keeping."
        }

class AuditSummaryService:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)
        self.tools = [summarize_audit_logs, recommend_audit_action]
        self.agent = create_react_agent(self.llm, self.tools)
        from pydantic import BaseModel

class AuditSummaryService:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)
        self.tools = [summarize_audit_logs, recommend_audit_action]
        self.agent = create_react_agent(self.llm, self.tools)
        class AuditSummaryState(BaseModel):
            input: str
            output: Any = None
        workflow = StateGraph(AuditSummaryState)
        workflow.add_node("agent", self.agent)
        workflow.set_entry_point("agent")
        workflow.set_finish_point("agent")
        self.workflow = workflow.compile()

    def summarize_audit(self, logs: List[Dict[str, Any]], user_id: str = None) -> dict:
        # Convert logs to a string summary for the agent
        logs_str = "\n".join([str(log) for log in logs])
        prompt = (
            "Given the following audit logs, summarize key events and recommend actions using the recommend_audit_action tool. "
            f"Logs: {logs_str}"
        )
        with tracer.start_as_current_span("agent.summarize_audit") as span:
            span.set_attribute("audit.log_count", len(logs))
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
                logger.error(f"Audit summary failed: {str(e)}")
                return {
                    "risk_level": "error",
                    "confidence": 0.0,
                    "rationale": f"Agent error: {str(e)}",
                    "recommendation": "Manual review required."
                }
