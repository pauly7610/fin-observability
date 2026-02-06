"""
Internal Evaluation Service for Compliance Model Audit Trails.
Tracks model predictions vs outcomes, computes evaluation metrics on schedule,
and maintains a full audit trail of model performance over time.
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EvalSubmission:
    """Represents a batch evaluation submission."""

    def __init__(
        self,
        submission_id: str,
        model_version: str,
        n_predictions: int,
        accuracy: float,
        precision: float,
        recall: float,
        f1: float,
        confusion_matrix: dict,
        submitted_at: str = None,
    ):
        self.submission_id = submission_id
        self.model_version = model_version
        self.n_predictions = n_predictions
        self.accuracy = accuracy
        self.precision = precision
        self.recall = recall
        self.f1 = f1
        self.confusion_matrix = confusion_matrix
        self.submitted_at = submitted_at or datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "submission_id": self.submission_id,
            "model_version": self.model_version,
            "n_predictions": self.n_predictions,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "confusion_matrix": self.confusion_matrix,
            "submitted_at": self.submitted_at,
        }


class EvalAIService:
    """
    Lightweight internal evaluation framework.
    
    - Accepts batch submissions of predictions + ground truth
    - Computes and stores evaluation metrics
    - Maintains a leaderboard of model versions
    - Provides audit trail for compliance reporting
    """

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self._submissions: List[EvalSubmission] = []
        self._load_from_redis()

    def _load_from_redis(self):
        """Load submission history from Redis."""
        if not self.redis_client:
            return
        try:
            data = self.redis_client.get("evalai:submissions")
            if data:
                submissions = json.loads(data)
                for s in submissions:
                    self._submissions.append(EvalSubmission(**s))
        except Exception as e:
            logger.warning(f"Failed to load eval submissions from Redis: {e}")

    def _save_to_redis(self):
        """Persist submissions to Redis."""
        if not self.redis_client:
            return
        try:
            data = json.dumps([s.to_dict() for s in self._submissions[-100:]])
            self.redis_client.set("evalai:submissions", data)
        except Exception:
            pass

    def submit_batch(
        self,
        predictions: List[Dict[str, str]],
        model_version: str = None,
    ) -> Dict[str, Any]:
        """
        Submit a batch of predictions with ground truth for evaluation.

        Args:
            predictions: List of dicts with keys:
                - transaction_id: str
                - predicted_action: str (approve, block, manual_review)
                - actual_action: str (approve, block, manual_review)
            model_version: Optional model version string

        Returns:
            Evaluation results dict.
        """
        if not predictions:
            return {"error": "No predictions provided"}

        actions = ["approve", "block", "manual_review"]

        # Build confusion matrix
        confusion = {a: {b: 0 for b in actions} for a in actions}
        correct = 0
        total = len(predictions)

        for pred in predictions:
            p = pred.get("predicted_action", "").lower()
            a = pred.get("actual_action", "").lower()
            if p in confusion and a in actions:
                confusion[p][a] += 1
            if p == a:
                correct += 1

        # Per-class metrics
        precisions, recalls, f1s = [], [], []
        for action in actions:
            tp = confusion[action][action]
            fp = sum(confusion[action][a] for a in actions if a != action)
            fn = sum(confusion[a][action] for a in actions if a != action)

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

            precisions.append(prec)
            recalls.append(rec)
            f1s.append(f1)

        macro_precision = sum(precisions) / len(actions)
        macro_recall = sum(recalls) / len(actions)
        macro_f1 = sum(f1s) / len(actions)
        accuracy = correct / total if total > 0 else 0.0

        # Create submission record
        import time
        submission = EvalSubmission(
            submission_id=f"eval_{int(time.time())}_{len(self._submissions)}",
            model_version=model_version or "unknown",
            n_predictions=total,
            accuracy=round(accuracy, 4),
            precision=round(macro_precision, 4),
            recall=round(macro_recall, 4),
            f1=round(macro_f1, 4),
            confusion_matrix=confusion,
        )

        self._submissions.append(submission)
        self._save_to_redis()

        return {
            "submission": submission.to_dict(),
            "status": "evaluated",
        }

    def get_results(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent evaluation results."""
        recent = self._submissions[-limit:]
        return {
            "total_submissions": len(self._submissions),
            "results": [s.to_dict() for s in reversed(recent)],
        }

    def get_leaderboard(self) -> Dict[str, Any]:
        """
        Get leaderboard of model versions ranked by F1 score.
        Shows best submission per model version.
        """
        best_per_version: Dict[str, EvalSubmission] = {}
        for sub in self._submissions:
            version = sub.model_version
            if version not in best_per_version or sub.f1 > best_per_version[version].f1:
                best_per_version[version] = sub

        leaderboard = sorted(
            best_per_version.values(), key=lambda s: s.f1, reverse=True
        )

        return {
            "leaderboard": [
                {
                    "rank": i + 1,
                    "model_version": s.model_version,
                    "f1": s.f1,
                    "precision": s.precision,
                    "recall": s.recall,
                    "accuracy": s.accuracy,
                    "n_predictions": s.n_predictions,
                    "submitted_at": s.submitted_at,
                }
                for i, s in enumerate(leaderboard)
            ],
            "total_versions": len(leaderboard),
        }

    def get_audit_trail(self, model_version: str = None) -> Dict[str, Any]:
        """
        Get full audit trail of evaluations, optionally filtered by model version.
        """
        submissions = self._submissions
        if model_version:
            submissions = [s for s in submissions if s.model_version == model_version]

        return {
            "audit_trail": [s.to_dict() for s in submissions],
            "total": len(submissions),
            "filter": {"model_version": model_version},
        }


# Singleton
_evalai_instance = None


def get_evalai_service() -> EvalAIService:
    """Get or create singleton EvalAI service."""
    global _evalai_instance
    if _evalai_instance is None:
        _evalai_instance = EvalAIService()
    return _evalai_instance
