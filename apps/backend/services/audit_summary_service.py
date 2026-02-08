from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel, Field
from opentelemetry import trace

from .llm_utils import structured_llm_call, get_llm_config

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

AUDIT_SYSTEM_PROMPT = """You are a financial audit analyst. Summarize the provided audit log entries, highlighting key events, anomalies, and potential security concerns.

You must provide:
1. Risk level (high, medium, or low)
2. Your confidence in the assessment (0.0 to 1.0)
3. A rationale summarizing the key findings from the logs
4. A recommended action based on the findings

Consider: failed authentication attempts, privilege escalation, data access patterns, anomalous activity timing, and regulatory reporting triggers."""


class AuditResult(BaseModel):
    """Structured output schema for audit summary."""
    risk_level: str = Field(description="Risk level: 'high', 'medium', or 'low'")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    rationale: str = Field(description="Summary of key findings from the audit logs")
    recommendation: str = Field(description="Recommended action based on findings")


def summarize_audit_logs(logs: str) -> dict:
    """Summarize audit logs using LLM with keyword heuristic fallback."""
    # Try LLM first
    llm_result = structured_llm_call(
        system_prompt=AUDIT_SYSTEM_PROMPT,
        user_input=f"Summarize these audit log entries:\n\n{logs}",
        output_schema=AuditResult,
    )
    if llm_result is not None:
        result = llm_result.model_dump()
        result["source"] = "llm"
        result["model"] = get_llm_config().get("model")
        return result

    # Keyword heuristic fallback
    if "anomaly" in logs.lower() or "error" in logs.lower():
        result = {
            "risk_level": "high",
            "confidence": 0.98,
            "rationale": "Anomalies or errors detected in audit logs.",
            "recommendation": "Immediate review recommended.",
        }
    elif "login" in logs.lower() and "failed" in logs.lower():
        result = {
            "risk_level": "medium",
            "confidence": 0.95,
            "rationale": "Multiple failed logins detected.",
            "recommendation": "Possible brute-force attempt. Investigate user accounts.",
        }
    else:
        result = {
            "risk_level": "low",
            "confidence": 0.99,
            "rationale": "No critical events detected in audit logs.",
            "recommendation": "Log for record-keeping. No immediate action.",
        }
    result["source"] = "heuristic"
    result["model"] = None
    return result


class AuditSummaryService:
    def summarize_audit(self, logs: List[Dict[str, Any]], user_id: str = None) -> dict:
        logs_str = "\n".join([str(log) for log in logs])
        with tracer.start_as_current_span("agent.summarize_audit") as span:
            span.set_attribute("audit.log_count", len(logs))
            if user_id is not None:
                span.set_attribute("user.id", user_id)
            span.set_attribute("input_size", len(logs_str))
            try:
                result = summarize_audit_logs(logs_str)
                span.set_attribute("result.risk_level", result.get("risk_level", "unknown"))
                span.set_attribute("result.source", result.get("source", "unknown"))
                return result
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Audit summary failed: {str(e)}")
                return {
                    "risk_level": "error",
                    "confidence": 0.0,
                    "rationale": f"Agent error: {str(e)}",
                    "recommendation": "Manual review required.",
                    "source": "error",
                    "model": None,
                }
