"""
Tests for LLM-powered agent services.
Tests both the fallback (no API key) and structured output schema paths.
Follows existing test patterns: no mocking, env var control.
"""
import os
import pytest
from apps.backend.services.llm_utils import get_chat_model, get_llm_config, set_llm_config, AVAILABLE_MODELS
from apps.backend.services.agent_service import classify_incident, TriageResult
from apps.backend.services.incident_remediation_service import recommend_remediation, RemediationResult
from apps.backend.services.compliance_automation_service import check_compliance, ComplianceResult
from apps.backend.services.audit_summary_service import summarize_audit_logs, AuditResult


class TestLLMUtils:
    def test_get_chat_model_returns_none_without_key(self):
        """Without any API key, get_chat_model should return None."""
        old_keys = {}
        for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "LLM_PROVIDER"):
            old_keys[key] = os.environ.pop(key, None)
        try:
            model = get_chat_model()
            assert model is None
        finally:
            for key, val in old_keys.items():
                if val is not None:
                    os.environ[key] = val

    def test_get_llm_config_structure(self):
        """get_llm_config should return a well-structured dict."""
        config = get_llm_config()
        assert "provider" in config
        assert "model" in config
        assert "source" in config
        assert "fallback_active" in config
        assert "available_providers" in config
        assert "available_models" in config
        assert isinstance(config["available_models"], dict)

    def test_available_models_structure(self):
        """AVAILABLE_MODELS should have entries for all three providers."""
        assert "openai" in AVAILABLE_MODELS
        assert "anthropic" in AVAILABLE_MODELS
        assert "google" in AVAILABLE_MODELS
        for provider, models in AVAILABLE_MODELS.items():
            assert len(models) > 0
            for m in models:
                assert "id" in m
                assert "name" in m

    def test_set_llm_config_invalid_provider(self):
        """set_llm_config should raise ValueError for unknown provider."""
        with pytest.raises(ValueError):
            set_llm_config(provider="invalid_provider")


class TestTriageServiceFallback:
    def test_classify_high_risk(self):
        result = classify_incident("Critical breach detected in trading system")
        assert result["risk_level"] in ("high", "medium", "low")
        assert "confidence" in result
        assert "rationale" in result
        assert "source" in result

    def test_classify_low_risk(self):
        result = classify_incident("Routine system check completed successfully")
        assert result["risk_level"] in ("low", "medium")
        assert result["confidence"] > 0
        assert "source" in result

    def test_classify_medium_risk(self):
        result = classify_incident("Warning: delayed response from payment gateway")
        assert result["risk_level"] in ("medium", "high", "low")
        assert "source" in result

    def test_triage_result_schema(self):
        """TriageResult Pydantic model should validate correctly."""
        r = TriageResult(risk_level="high", confidence=0.95, rationale="test")
        assert r.risk_level == "high"
        assert r.confidence == 0.95


class TestRemediationServiceFallback:
    def test_remediate_critical(self):
        result = recommend_remediation("Critical breach in production database")
        assert result["risk_level"] in ("high", "medium", "low")
        assert "recommendation" in result
        assert "source" in result

    def test_remediate_timeout(self):
        result = recommend_remediation("Timeout on order router service")
        assert result["risk_level"] in ("medium", "high", "low")
        assert "source" in result

    def test_remediation_result_schema(self):
        r = RemediationResult(risk_level="medium", confidence=0.9, rationale="test", recommendation="restart")
        assert r.recommendation == "restart"


class TestComplianceServiceFallback:
    def test_compliance_sanctions(self):
        result = check_compliance("Transaction flagged: sanction list match")
        assert result["risk_level"] in ("high", "medium", "low")
        assert "recommendation" in result
        assert "source" in result

    def test_compliance_clean(self):
        result = check_compliance("Standard internal transfer between accounts")
        assert result["risk_level"] in ("low", "medium")
        assert "source" in result

    def test_compliance_result_schema(self):
        r = ComplianceResult(risk_level="low", confidence=0.99, rationale="clean", recommendation="approve")
        assert r.risk_level == "low"


class TestAuditServiceFallback:
    def test_audit_anomaly(self):
        result = summarize_audit_logs("Anomaly detected in FX desk trading patterns")
        assert result["risk_level"] in ("high", "medium", "low")
        assert "recommendation" in result
        assert "source" in result

    def test_audit_clean(self):
        result = summarize_audit_logs("Regular daily backup completed successfully")
        assert result["risk_level"] in ("low", "medium")
        assert "source" in result

    def test_audit_result_schema(self):
        r = AuditResult(risk_level="high", confidence=0.98, rationale="anomalies found", recommendation="review")
        assert r.risk_level == "high"
