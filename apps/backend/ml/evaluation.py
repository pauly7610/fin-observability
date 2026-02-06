"""
Model Evaluation Module for Compliance Anomaly Detection.
Computes precision, recall, F1, and confusion matrix from analyst feedback.
"""
import logging
from typing import Dict, Any, List, Optional
from collections import Counter
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

ACTIONS = ["approve", "block", "manual_review"]


class ModelEvaluator:
    """
    Evaluates compliance model performance using analyst feedback data.
    """

    MIN_SAMPLES = 10  # Minimum feedback samples before reporting metrics

    def compute_metrics(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """
        Compute precision, recall, F1 per action class from feedback.

        Args:
            db: Database session
            days: Lookback window in days

        Returns:
            Dict with per-class and aggregate metrics.
        """
        from apps.backend.models import ComplianceFeedback

        since = datetime.utcnow() - timedelta(days=days)
        feedback = (
            db.query(ComplianceFeedback)
            .filter(ComplianceFeedback.created_at >= since)
            .all()
        )

        total = len(feedback)
        if total < self.MIN_SAMPLES:
            return {
                "status": "insufficient_data",
                "total_feedback": total,
                "min_required": self.MIN_SAMPLES,
                "message": f"Need at least {self.MIN_SAMPLES} feedback samples. Currently have {total}.",
            }

        # Build confusion matrix counts
        confusion = {}
        for action in ACTIONS:
            confusion[action] = {a: 0 for a in ACTIONS}

        correct = 0
        for fb in feedback:
            pred = fb.predicted_action
            actual = fb.actual_action
            if pred in confusion and actual in ACTIONS:
                confusion[pred][actual] += 1
            if fb.is_correct:
                correct += 1

        # Per-class precision, recall, F1
        per_class = {}
        for action in ACTIONS:
            tp = confusion[action][action]
            fp = sum(confusion[action][a] for a in ACTIONS if a != action)
            fn = sum(confusion[a][action] for a in ACTIONS if a != action)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0.0
            )

            per_class[action] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "support": tp + fn,
            }

        # Macro averages
        macro_precision = sum(c["precision"] for c in per_class.values()) / len(ACTIONS)
        macro_recall = sum(c["recall"] for c in per_class.values()) / len(ACTIONS)
        macro_f1 = sum(c["f1"] for c in per_class.values()) / len(ACTIONS)

        return {
            "status": "ok",
            "total_feedback": total,
            "accuracy": round(correct / total, 4) if total > 0 else 0.0,
            "macro_precision": round(macro_precision, 4),
            "macro_recall": round(macro_recall, 4),
            "macro_f1": round(macro_f1, 4),
            "per_class": per_class,
            "confusion_matrix": confusion,
            "lookback_days": days,
        }

    def compute_confidence_calibration(
        self, db: Session, days: int = 30, n_bins: int = 10
    ) -> Dict[str, Any]:
        """
        Compute confidence calibration: are high-confidence predictions more accurate?

        Returns:
            Dict with bins of confidence ranges and their accuracy.
        """
        from apps.backend.models import ComplianceFeedback

        since = datetime.utcnow() - timedelta(days=days)
        feedback = (
            db.query(ComplianceFeedback)
            .filter(
                ComplianceFeedback.created_at >= since,
                ComplianceFeedback.confidence.isnot(None),
            )
            .all()
        )

        if len(feedback) < self.MIN_SAMPLES:
            return {"status": "insufficient_data", "total": len(feedback)}

        bin_size = 100.0 / n_bins
        bins = []
        for i in range(n_bins):
            low = i * bin_size
            high = (i + 1) * bin_size
            in_bin = [
                fb for fb in feedback if low <= (fb.confidence or 0) < high
            ]
            if in_bin:
                acc = sum(1 for fb in in_bin if fb.is_correct) / len(in_bin)
                bins.append({
                    "range": f"{low:.0f}-{high:.0f}",
                    "count": len(in_bin),
                    "accuracy": round(acc, 4),
                    "avg_confidence": round(
                        sum(fb.confidence for fb in in_bin) / len(in_bin), 2
                    ),
                })

        return {
            "status": "ok",
            "total": len(feedback),
            "bins": bins,
            "lookback_days": days,
        }
