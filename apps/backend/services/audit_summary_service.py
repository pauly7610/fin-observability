from typing import Dict, Any, List
import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def summarize_audit_logs(logs: str) -> dict:
    """Summarize a list of audit log entries, highlighting key events and anomalies, with risk, confidence, rationale, and recommendation."""
    if "anomaly" in logs.lower() or "error" in logs.lower():
        return {
            "risk_level": "high",
            "confidence": 0.98,
            "rationale": "Anomalies or errors detected in audit logs.",
            "recommendation": "Immediate review recommended.",
        }
    elif "login" in logs.lower() and "failed" in logs.lower():
        return {
            "risk_level": "medium",
            "confidence": 0.95,
            "rationale": "Multiple failed logins detected.",
            "recommendation": "Possible brute-force attempt. Investigate user accounts.",
        }
    else:
        return {
            "risk_level": "low",
            "confidence": 0.99,
            "rationale": "No critical events detected in audit logs.",
            "recommendation": "Log for record-keeping. No immediate action.",
        }


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
                return result
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Audit summary failed: {str(e)}")
                return {
                    "risk_level": "error",
                    "confidence": 0.0,
                    "rationale": f"Agent error: {str(e)}",
                    "recommendation": "Manual review required.",
                }
