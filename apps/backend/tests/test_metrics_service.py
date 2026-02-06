"""
Unit tests for the ComplianceMetricsService (in-memory fallback mode).
"""
import pytest
from apps.backend.services.metrics_service import ComplianceMetricsService


class TestComplianceMetricsService:
    def setup_method(self):
        # Force in-memory mode by using an invalid Redis URL
        self.service = ComplianceMetricsService(redis_url="redis://invalid:9999")
        self.service.redis_client = None  # Ensure in-memory fallback
        self.service.reset_metrics()

    def test_initial_metrics_are_zero(self):
        metrics = self.service.get_metrics()
        assert metrics["total_transactions"] == 0
        assert metrics["approved"] == 0
        assert metrics["blocked"] == 0
        assert metrics["manual_review"] == 0

    def test_increment_approve(self):
        self.service.increment_transaction("approve", 90.0)
        metrics = self.service.get_metrics()
        assert metrics["total_transactions"] == 1
        assert metrics["approved"] == 1
        assert metrics["blocked"] == 0
        assert metrics["manual_review"] == 0

    def test_increment_block(self):
        self.service.increment_transaction("block", 95.0)
        metrics = self.service.get_metrics()
        assert metrics["total_transactions"] == 1
        assert metrics["blocked"] == 1

    def test_increment_manual_review(self):
        self.service.increment_transaction("manual_review", 85.0)
        metrics = self.service.get_metrics()
        assert metrics["total_transactions"] == 1
        assert metrics["manual_review"] == 1

    def test_multiple_increments(self):
        self.service.increment_transaction("approve", 90.0)
        self.service.increment_transaction("approve", 85.0)
        self.service.increment_transaction("block", 95.0)
        self.service.increment_transaction("manual_review", 80.0)
        metrics = self.service.get_metrics()
        assert metrics["total_transactions"] == 4
        assert metrics["approved"] == 2
        assert metrics["blocked"] == 1
        assert metrics["manual_review"] == 1

    def test_confidence_tracking(self):
        self.service.increment_transaction("approve", 90.0)
        self.service.increment_transaction("approve", 80.0)
        metrics = self.service.get_metrics()
        avg = metrics.get("avg_confidence")
        if avg is not None:
            assert 80.0 <= avg <= 90.0

    def test_reset(self):
        self.service.increment_transaction("approve", 90.0)
        self.service.increment_transaction("block", 95.0)
        self.service.reset_metrics()
        metrics = self.service.get_metrics()
        assert metrics["total_transactions"] == 0
        assert metrics["approved"] == 0
        assert metrics["blocked"] == 0

    def test_unknown_action_still_counts(self):
        """Unknown action types should still increment total."""
        self.service.increment_transaction("unknown_action", 50.0)
        metrics = self.service.get_metrics()
        assert metrics["total_transactions"] == 1
