from typing import Dict, Any
import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def check_compliance(transaction: str) -> dict:
    """Check if a transaction or event violates compliance rules, with risk, confidence, rationale, and recommendation."""
    text = transaction.lower()
    if any(word in text for word in ["sanction", "blocked", "prohibited", "blacklist"]):
        return {
            "risk_level": "high",
            "confidence": 0.99,
            "rationale": "Potential violation of sanctions or prohibited list.",
            "recommendation": "Flag for compliance review.",
        }
    elif any(word in text for word in ["large cash", "unusual transfer", "offshore"]):
        return {
            "risk_level": "medium",
            "confidence": 0.95,
            "rationale": "Unusual transfer or offshore activity detected.",
            "recommendation": "Escalate for enhanced due diligence.",
        }
    elif any(word in text for word in ["approved", "ok", "cleared"]):
        return {
            "risk_level": "low",
            "confidence": 0.99,
            "rationale": "Transaction is approved/cleared.",
            "recommendation": "Approve. No compliance issue detected.",
        }
    else:
        return {
            "risk_level": "low",
            "confidence": 0.95,
            "rationale": "No immediate compliance issue detected.",
            "recommendation": "Monitor.",
        }


class ComplianceAutomationService:
    def automate_compliance(
        self, transaction: Dict[str, Any], user_id: str = None
    ) -> dict:
        transaction_id = transaction.get("transaction_id", "unknown")
        transaction_str = str(transaction)
        with tracer.start_as_current_span("agent.automate_compliance") as span:
            span.set_attribute("transaction.id", transaction_id)
            if user_id is not None:
                span.set_attribute("user.id", user_id)
            span.set_attribute("input_size", len(transaction_str))
            try:
                result = check_compliance(transaction_str)
                span.set_attribute("result.risk_level", result.get("risk_level", "unknown"))
                return result
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Compliance automation failed: {str(e)}")
                return {
                    "risk_level": "error",
                    "confidence": 0.0,
                    "rationale": f"Agent error: {str(e)}",
                    "recommendation": "Manual review required.",
                }
