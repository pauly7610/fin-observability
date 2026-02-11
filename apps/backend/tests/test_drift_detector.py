"""
Tests for the drift detection module (PSI + KS test).
"""
import numpy as np
import pytest
from apps.backend.ml.drift_detector import (
    DriftDetector,
    _compute_psi,
    MIN_SAMPLES_FOR_DRIFT,
)


FEATURE_NAMES = ["amount", "hour", "day_of_week", "is_weekend", "is_off_hours", "txn_type"]


class TestPSIComputation:
    def test_identical_distributions_psi_near_zero(self):
        """PSI of identical distributions should be ~0."""
        rng = np.random.default_rng(42)
        data = rng.normal(0, 1, size=1000)
        psi = _compute_psi(data, data)
        assert psi < 0.01, f"PSI of identical data should be ~0, got {psi}"

    def test_shifted_distribution_high_psi(self):
        """PSI of significantly shifted distribution should be > 0.25."""
        rng = np.random.default_rng(42)
        ref = rng.normal(0, 1, size=1000)
        shifted = rng.normal(5, 1, size=1000)
        psi = _compute_psi(ref, shifted)
        assert psi > 0.25, f"PSI of shifted data should be > 0.25, got {psi}"


class TestDriftDetector:
    def setup_method(self):
        self.detector = DriftDetector(feature_names=FEATURE_NAMES)

    def test_no_reference_returns_status(self):
        """check_drift without reference data should return no_reference."""
        result = self.detector.check_drift()
        assert result["status"] == "no_reference"

    def test_insufficient_data(self):
        """check_drift with too few samples should return insufficient_data."""
        rng = np.random.default_rng(42)
        ref = rng.normal(size=(200, 6))
        self.detector.set_reference(ref)
        # Record fewer than MIN_SAMPLES_FOR_DRIFT
        for i in range(MIN_SAMPLES_FOR_DRIFT - 1):
            self.detector.record(rng.normal(size=6))
        result = self.detector.check_drift()
        assert result["status"] == "insufficient_data"

    def test_stable_distribution(self):
        """Same distribution should be detected as stable."""
        rng_ref = np.random.default_rng(42)
        rng_cur = np.random.default_rng(99)
        ref = rng_ref.normal(loc=0, scale=1, size=(2000, 6))
        self.detector.set_reference(ref)
        # Record samples from the same distribution (different seed, same params)
        for _ in range(500):
            self.detector.record(rng_cur.normal(loc=0, scale=1, size=6))
        result = self.detector.check_drift()
        assert result["status"] == "stable", f"Expected stable, got {result['status']} (max_psi={result.get('max_psi')})"
        assert result["should_retrain"] is False

    def test_drift_detected(self):
        """Significantly shifted distribution should trigger drift detection."""
        rng = np.random.default_rng(42)
        ref = rng.normal(loc=0, scale=1, size=(500, 6))
        self.detector.set_reference(ref)
        # Record samples from a very different distribution
        for _ in range(150):
            self.detector.record(rng.normal(loc=10, scale=1, size=6))
        result = self.detector.check_drift()
        assert result["status"] == "drift_detected"
        assert result["should_retrain"] is True
        assert len(result["drifted_features"]) > 0

    def test_get_status(self):
        """get_status should return detector metadata."""
        status = self.detector.get_status()
        assert status["has_reference"] is False
        assert status["current_window_size"] == 0
        assert "thresholds" in status

    def test_set_reference_clears_window(self):
        """Setting new reference should clear the current window."""
        rng = np.random.default_rng(42)
        self.detector.record(rng.normal(size=6))
        assert self.detector.get_status()["current_window_size"] == 1
        self.detector.set_reference(rng.normal(size=(100, 6)))
        assert self.detector.get_status()["current_window_size"] == 0
