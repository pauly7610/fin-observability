"""
Feature Drift Detection for Anomaly Detection Model.

Uses Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) test
to detect distribution shifts in incoming transaction features.
When drift exceeds configurable thresholds, triggers automatic retraining.

PSI thresholds (industry standard):
  < 0.1  — No significant drift
  0.1-0.25 — Moderate drift (monitor)
  > 0.25 — Significant drift (retrain)
"""
import numpy as np
import logging
from collections import deque
from datetime import datetime
from typing import Dict, Any, Optional, List
from scipy.stats import ks_2samp
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Configurable thresholds
PSI_THRESHOLD = 0.25  # Trigger retrain above this
KS_P_VALUE_THRESHOLD = 0.01  # Reject null hypothesis (same distribution) below this
WINDOW_SIZE = 500  # Number of recent predictions to compare against reference
MIN_SAMPLES_FOR_DRIFT = 100  # Minimum samples before drift check is meaningful


def _compute_psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    """
    Compute Population Stability Index between two distributions.

    PSI = SUM( (current_pct - reference_pct) * ln(current_pct / reference_pct) )

    Args:
        reference: Reference (training) distribution
        current: Current (production) distribution
        bins: Number of bins for histogram

    Returns:
        PSI value (0 = identical distributions)
    """
    # Use reference distribution to define bin edges
    _, bin_edges = np.histogram(reference, bins=bins)

    ref_counts = np.histogram(reference, bins=bin_edges)[0]
    cur_counts = np.histogram(current, bins=bin_edges)[0]

    # Convert to proportions, add small epsilon to avoid division by zero
    eps = 1e-6
    ref_pct = (ref_counts + eps) / (ref_counts.sum() + eps * bins)
    cur_pct = (cur_counts + eps) / (cur_counts.sum() + eps * bins)

    psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
    return float(psi)


class DriftDetector:
    """
    Monitors feature distributions for drift and triggers retraining.

    Maintains a sliding window of recent predictions and compares them
    against the reference (training) distribution using PSI and KS tests.
    """

    def __init__(self, feature_names: List[str], window_size: int = WINDOW_SIZE):
        self.feature_names = feature_names
        self.window_size = window_size

        # Reference distributions (set after training)
        self._reference_data: Optional[np.ndarray] = None

        # Sliding window of recent feature vectors
        self._current_window: deque = deque(maxlen=window_size)

        # Drift history for monitoring
        self._drift_history: List[Dict[str, Any]] = []
        self._last_check: Optional[datetime] = None
        self._retrain_triggered_count: int = 0

    def set_reference(self, training_data: np.ndarray) -> None:
        """
        Set the reference distribution from training data.

        Args:
            training_data: Feature matrix used for training (n_samples x n_features)
        """
        self._reference_data = training_data.copy()
        self._current_window.clear()
        logger.info(
            f"Drift detector reference set: {training_data.shape[0]} samples, "
            f"{training_data.shape[1]} features"
        )

    def record(self, features: np.ndarray) -> None:
        """
        Record a feature vector from a production prediction.

        Args:
            features: 1D array of feature values for a single prediction
        """
        self._current_window.append(features.flatten())

    def check_drift(self) -> Dict[str, Any]:
        """
        Check for feature drift between reference and current window.

        Returns:
            Dict with drift status, per-feature PSI/KS scores, and recommendation.
        """
        with tracer.start_as_current_span("drift_detector.check_drift") as span:
            self._last_check = datetime.utcnow()

            if self._reference_data is None:
                return {"status": "no_reference", "message": "No reference data set"}

            n_current = len(self._current_window)
            if n_current < MIN_SAMPLES_FOR_DRIFT:
                return {
                    "status": "insufficient_data",
                    "message": f"Need {MIN_SAMPLES_FOR_DRIFT} samples, have {n_current}",
                    "samples": n_current,
                }

            current_data = np.array(list(self._current_window))
            feature_results = {}
            max_psi = 0.0
            drifted_features = []

            for i, name in enumerate(self.feature_names):
                ref_col = self._reference_data[:, i]
                cur_col = current_data[:, i]

                # PSI
                psi = _compute_psi(ref_col, cur_col)

                # KS test
                ks_stat, ks_p_value = ks_2samp(ref_col, cur_col)

                is_drifted = psi > PSI_THRESHOLD or ks_p_value < KS_P_VALUE_THRESHOLD

                feature_results[name] = {
                    "psi": round(psi, 4),
                    "ks_statistic": round(float(ks_stat), 4),
                    "ks_p_value": round(float(ks_p_value), 6),
                    "drifted": is_drifted,
                }

                if psi > max_psi:
                    max_psi = psi

                if is_drifted:
                    drifted_features.append(name)

            # Overall drift decision
            should_retrain = len(drifted_features) > 0
            severity = "none"
            if max_psi > PSI_THRESHOLD:
                severity = "high"
            elif max_psi > 0.1:
                severity = "moderate"

            result = {
                "status": "drift_detected" if should_retrain else "stable",
                "severity": severity,
                "max_psi": round(max_psi, 4),
                "drifted_features": drifted_features,
                "feature_details": feature_results,
                "samples_checked": n_current,
                "reference_samples": len(self._reference_data),
                "should_retrain": should_retrain,
                "timestamp": self._last_check.isoformat(),
            }

            # Log to OTel
            span.set_attribute("drift.max_psi", max_psi)
            span.set_attribute("drift.severity", severity)
            span.set_attribute("drift.should_retrain", should_retrain)
            span.set_attribute("drift.drifted_features", str(drifted_features))

            # Track history
            self._drift_history.append(result)
            if len(self._drift_history) > 100:
                self._drift_history = self._drift_history[-50:]

            if should_retrain:
                self._retrain_triggered_count += 1
                logger.warning(
                    f"Drift detected! PSI={max_psi:.4f}, "
                    f"drifted features: {drifted_features}"
                )
            else:
                logger.info(f"Drift check OK: PSI={max_psi:.4f}, severity={severity}")

            return result

    def get_status(self) -> Dict[str, Any]:
        """Return drift detector status and recent history."""
        return {
            "has_reference": self._reference_data is not None,
            "reference_samples": len(self._reference_data) if self._reference_data is not None else 0,
            "current_window_size": len(self._current_window),
            "window_capacity": self.window_size,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "retrain_triggered_count": self._retrain_triggered_count,
            "recent_checks": self._drift_history[-5:] if self._drift_history else [],
            "thresholds": {
                "psi": PSI_THRESHOLD,
                "ks_p_value": KS_P_VALUE_THRESHOLD,
                "min_samples": MIN_SAMPLES_FOR_DRIFT,
            },
        }


# Singleton
_drift_detector_instance: Optional[DriftDetector] = None


def get_drift_detector() -> DriftDetector:
    """Get or create singleton drift detector."""
    global _drift_detector_instance
    if _drift_detector_instance is None:
        from .anomaly_detector import AnomalyDetector
        _drift_detector_instance = DriftDetector(
            feature_names=AnomalyDetector.FEATURE_NAMES
        )
    return _drift_detector_instance
