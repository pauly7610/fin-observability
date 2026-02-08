from typing import Dict, Any, Optional
import logging
from pydantic import BaseModel, Field
from opentelemetry import trace

from .llm_utils import structured_llm_call, get_llm_config

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

COMPLIANCE_SYSTEM_PROMPT = """You are a FINRA 4511 and SEC 17a-4 compliance specialist. Analyze the transaction or event for regulatory compliance violations.

You must assess:
1. Risk level (high, medium, or low)
2. Your confidence in the assessment (0.0 to 1.0)
3. A rationale citing specific regulations or compliance concerns
4. A recommended action (flag, escalate, approve, or monitor)

Consider: sanctions screening, AML/KYC requirements, transaction reporting thresholds, unusual activity patterns, and record retention obligations."""


class ComplianceResult(BaseModel):
    """Structured output schema for compliance automation."""
    risk_level: str = Field(description="Risk level: 'high', 'medium', or 'low'")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    rationale: str = Field(description="Explanation citing specific compliance concerns")
    recommendation: str = Field(description="Recommended compliance action")


def check_compliance(transaction: str) -> dict:
    """Check compliance using LLM with keyword heuristic fallback."""
    # Try LLM first
    llm_result = structured_llm_call(
        system_prompt=COMPLIANCE_SYSTEM_PROMPT,
        user_input=f"Check compliance for this transaction/event:\n\n{transaction}",
        output_schema=ComplianceResult,
    )
    if llm_result is not None:
        result = llm_result.model_dump()
        result["source"] = "llm"
        result["model"] = get_llm_config().get("model")
        return result

    # Keyword heuristic fallback
    text = transaction.lower()
    if any(word in text for word in ["sanction", "blocked", "prohibited", "blacklist"]):
        result = {
            "risk_level": "high",
            "confidence": 0.99,
            "rationale": "Potential violation of sanctions or prohibited list.",
            "recommendation": "Flag for compliance review.",
        }
    elif any(word in text for word in ["large cash", "unusual transfer", "offshore"]):
        result = {
            "risk_level": "medium",
            "confidence": 0.95,
            "rationale": "Unusual transfer or offshore activity detected.",
            "recommendation": "Escalate for enhanced due diligence.",
        }
    elif any(word in text for word in ["approved", "ok", "cleared"]):
        result = {
            "risk_level": "low",
            "confidence": 0.99,
            "rationale": "Transaction is approved/cleared.",
            "recommendation": "Approve. No compliance issue detected.",
        }
    else:
        result = {
            "risk_level": "low",
            "confidence": 0.95,
            "rationale": "No immediate compliance issue detected.",
            "recommendation": "Monitor.",
        }
    result["source"] = "heuristic"
    result["model"] = None
    return result


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
                span.set_attribute("result.source", result.get("source", "unknown"))
                return result
            except Exception as e:
                span.record_exception(e)
                logger.error(f"Compliance automation failed: {str(e)}")
                return {
                    "risk_level": "error",
                    "confidence": 0.0,
                    "rationale": f"Agent error: {str(e)}",
                    "recommendation": "Manual review required.",
                    "source": "error",
                    "model": None,
                }
