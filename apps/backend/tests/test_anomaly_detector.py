"""
Unit tests for the Isolation Forest anomaly detector.
"""
import pytest
from datetime import datetime
from apps.backend.ml.anomaly_detector import AnomalyDetector, get_detector


class TestAnomalyDetector:
    def setup_method(self):
        self.detector = AnomalyDetector()

    def test_predict_returns_score_and_details(self):
        """predict() should return a tuple of (score, details_dict)."""
        score, details = self.detector.predict(
            amount=5000.0,
            timestamp=datetime(2024, 6, 10, 14, 30),
            txn_type="ach",
        )
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert isinstance(details, dict)
        assert "risk_factors" in details
        assert "model_version" in details

    def test_small_ach_low_score(self):
        """A small ACH during business hours should have a low anomaly score."""
        score, details = self.detector.predict(
            amount=500.0,
            timestamp=datetime(2024, 6, 10, 10, 0),
            txn_type="ach",
        )
        assert score < 0.5, f"Expected low score for small ACH, got {score}"

    def test_large_wire_high_score(self):
        """A large wire transfer should have a higher anomaly score."""
        score, details = self.detector.predict(
            amount=80000.0,
            timestamp=datetime(2024, 6, 10, 3, 0),
            txn_type="wire",
        )
        assert score > 0.3, f"Expected elevated score for large wire, got {score}"

    def test_off_hours_increases_score(self):
        """Off-hours transactions should score higher than business-hours ones."""
        score_business, _ = self.detector.predict(
            amount=10000.0,
            timestamp=datetime(2024, 6, 10, 14, 0),
            txn_type="ach",
        )
        score_offhours, _ = self.detector.predict(
            amount=10000.0,
            timestamp=datetime(2024, 6, 10, 3, 0),
            txn_type="ach",
        )
        assert score_offhours >= score_business, (
            f"Off-hours score ({score_offhours}) should be >= business hours ({score_business})"
        )

    def test_feature_extraction(self):
        """_extract_features should return a numpy array with 6 features."""
        features = self.detector._extract_features(
            amount=25000.0,
            timestamp=datetime(2024, 6, 10, 14, 30),
            txn_type="wire",
        )
        assert features.shape == (1, 6)
        assert all(isinstance(float(f), float) for f in features[0])

    def test_get_model_info(self):
        """get_model_info should return dict with version and model metadata."""
        info = self.detector.get_model_info()
        assert isinstance(info, dict)
        assert "version" in info
        assert "algorithm" in info
        assert "features" in info
        assert len(info["features"]) == 6

    def test_get_detector_singleton(self):
        """get_detector() should return the same instance."""
        d1 = get_detector()
        d2 = get_detector()
        assert d1 is d2

    def test_predict_edge_zero_amount(self):
        """Zero amount should not crash."""
        score, details = self.detector.predict(
            amount=0.0,
            timestamp=datetime(2024, 6, 10, 12, 0),
            txn_type="ach",
        )
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_predict_edge_negative_amount(self):
        """Negative amount (refund) should not crash."""
        score, details = self.detector.predict(
            amount=-500.0,
            timestamp=datetime(2024, 6, 10, 12, 0),
            txn_type="ach",
        )
        assert isinstance(score, float)

    def test_predict_unknown_txn_type(self):
        """Unknown transaction type should not crash."""
        score, details = self.detector.predict(
            amount=5000.0,
            timestamp=datetime(2024, 6, 10, 12, 0),
            txn_type="crypto",
        )
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
