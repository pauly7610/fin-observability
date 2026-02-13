"""
Tests for the telemetry module (metrics middleware, counter initialization).
"""
import pytest
from fastapi.testclient import TestClient
from apps.backend.main import app
from apps.backend import telemetry


client = TestClient(app)


class TestMetricsMiddleware:
    def test_counters_initialized(self):
        """All metric counters should be initialized after app startup."""
        assert telemetry.http_request_counter is not None
        assert telemetry.http_request_duration is not None
        assert telemetry.export_job_counter is not None
        assert telemetry.compliance_action_counter is not None
        assert telemetry.anomaly_detected_counter is not None
        assert telemetry.audit_trail_write_failures_counter is not None

    def test_health_request_records_metrics(self):
        """A request to /health should not crash the metrics middleware."""
        resp = client.get("/health")
        assert resp.status_code in (200, 429)

    def test_404_records_status_code(self):
        """A request to a nonexistent path should still pass through middleware."""
        resp = client.get("/nonexistent-path-12345")
        assert resp.status_code == 404
