"""
Automated Retraining Pipeline for the Anomaly Detection Model.

Supports two retraining modes:
1. Scheduled (cron): Runs on a configurable interval (default: weekly) via APScheduler
2. Drift-triggered: Checks feature drift (PSI/KS) and retrains only when drift is detected

Pipeline steps:
- Check drift status (if drift mode)
- Snapshot current model metrics (before)
- Retrain the Isolation Forest model with auto-versioning
- Snapshot new model metrics (after)
- Log delta to OpenTelemetry
- Can also be triggered manually via API endpoint
"""
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Default schedule: every 168 hours (weekly)
RETRAIN_INTERVAL_HOURS = int(os.environ.get("RETRAIN_SCHEDULE_HOURS", "168"))


class RetrainingPipeline:
    """Manages automated model retraining with metrics tracking."""

    def __init__(self):
        self._last_retrain: Optional[datetime] = None
        self._retrain_count: int = 0

    def run(self) -> Dict[str, Any]:
        """
        Execute a full retraining cycle.

        Steps:
        1. Snapshot current model metrics (before)
        2. Retrain from the latest dataset CSV
        3. Snapshot new model metrics (after)
        4. Log delta to OTel and return summary
        """
        with tracer.start_as_current_span("retraining_pipeline.run") as span:
            try:
                from .anomaly_detector import get_detector

                detector = get_detector()

                # Step 1: Before metrics
                before_info = detector.get_model_info()
                before_version = before_info.get("version", "unknown")
                span.set_attribute("retrain.before_version", before_version)
                logger.info(f"Retraining pipeline started (current version: {before_version})")

                # Step 2: Retrain
                result = detector.retrain_from_csv()

                if result.get("status") != "retrained":
                    span.set_attribute("retrain.status", "failed")
                    logger.warning(f"Retraining failed: {result}")
                    return {
                        "status": "failed",
                        "reason": result.get("detail", "Unknown error"),
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                # Step 3: After metrics
                after_info = detector.get_model_info()
                after_version = after_info.get("version", "unknown")
                span.set_attribute("retrain.after_version", after_version)
                span.set_attribute("retrain.status", "success")

                self._last_retrain = datetime.utcnow()
                self._retrain_count += 1

                summary = {
                    "status": "success",
                    "before_version": before_version,
                    "after_version": after_version,
                    "retrain_count": self._retrain_count,
                    "timestamp": self._last_retrain.isoformat(),
                    "training_samples": result.get("training_samples"),
                    "model_info": after_info,
                }

                logger.info(
                    f"Retraining complete: {before_version} -> {after_version} "
                    f"({result.get('training_samples', '?')} samples)"
                )

                return summary

            except Exception as e:
                span.record_exception(e)
                from opentelemetry.trace.status import Status, StatusCode
                span.set_status(Status(StatusCode.ERROR, str(e)))
                logger.error(f"Retraining pipeline error: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }

    def run_if_drifted(self) -> Dict[str, Any]:
        """
        Check for feature drift and retrain only if drift is detected.
        This is the preferred production mode — avoids unnecessary retraining.
        """
        with tracer.start_as_current_span("retraining_pipeline.run_if_drifted") as span:
            from .drift_detector import get_drift_detector

            drift_detector = get_drift_detector()
            drift_result = drift_detector.check_drift()
            span.set_attribute("drift.status", drift_result.get("status", "unknown"))

            if drift_result.get("should_retrain"):
                logger.info(
                    f"Drift detected (PSI={drift_result.get('max_psi', 0):.4f}), "
                    f"triggering retraining..."
                )
                retrain_result = self.run()
                retrain_result["trigger"] = "drift"
                retrain_result["drift"] = drift_result
                return retrain_result
            else:
                logger.info(
                    f"No drift detected (PSI={drift_result.get('max_psi', 0):.4f}), "
                    f"skipping retraining"
                )
                return {
                    "status": "skipped",
                    "reason": "no_drift",
                    "trigger": "drift_check",
                    "drift": drift_result,
                    "timestamp": datetime.utcnow().isoformat(),
                }

    def get_status(self) -> Dict[str, Any]:
        """Return pipeline status including drift detector state."""
        from .drift_detector import get_drift_detector

        drift_detector = get_drift_detector()
        return {
            "last_retrain": self._last_retrain.isoformat() if self._last_retrain else None,
            "retrain_count": self._retrain_count,
            "schedule_hours": RETRAIN_INTERVAL_HOURS,
            "drift": drift_detector.get_status(),
        }


# Singleton
_pipeline_instance = None


def get_retraining_pipeline() -> RetrainingPipeline:
    """Get or create singleton retraining pipeline."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RetrainingPipeline()
    return _pipeline_instance
