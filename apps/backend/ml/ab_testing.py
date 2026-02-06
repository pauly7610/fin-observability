"""
A/B Testing Framework for Compliance Model Variants.
Routes traffic between model variants and tracks per-variant metrics.
"""
import hashlib
import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Experiment:
    """Represents a single A/B test experiment."""

    def __init__(
        self,
        id: str,
        name: str,
        model_a: str = "isolation_forest",
        model_b: str = "ensemble",
        traffic_split: int = 50,
        status: str = "active",
    ):
        self.id = id
        self.name = name
        self.model_a = model_a
        self.model_b = model_b
        self.traffic_split = traffic_split  # % of traffic to model A
        self.status = status
        self.created_at = datetime.utcnow().isoformat()
        self.metrics_a = {"total": 0, "correct": 0, "scores": []}
        self.metrics_b = {"total": 0, "correct": 0, "scores": []}

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "model_a": self.model_a,
            "model_b": self.model_b,
            "traffic_split": self.traffic_split,
            "status": self.status,
            "created_at": self.created_at,
        }


class ABTestManager:
    """
    Manages A/B test experiments for compliance models.
    
    Uses deterministic hashing of transaction_id for consistent routing:
    the same transaction always goes to the same model variant.
    
    Stores experiment state in-memory with optional Redis persistence.
    """

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self._experiments: Dict[str, Experiment] = {}
        self._load_from_redis()

    def _load_from_redis(self):
        """Load experiments from Redis if available."""
        if not self.redis_client:
            return
        try:
            keys = self.redis_client.keys("ab_test:experiment:*")
            for key in keys:
                data = self.redis_client.get(key)
                if data:
                    exp_data = json.loads(data)
                    exp = Experiment(**{k: v for k, v in exp_data.items() if k in Experiment.__init__.__code__.co_varnames})
                    self._experiments[exp.id] = exp
        except Exception as e:
            logger.warning(f"Failed to load experiments from Redis: {e}")

    def _save_experiment(self, experiment: Experiment):
        """Persist experiment to Redis if available."""
        if self.redis_client:
            try:
                self.redis_client.set(
                    f"ab_test:experiment:{experiment.id}",
                    json.dumps(experiment.to_dict()),
                )
            except Exception:
                pass

    def create_experiment(
        self,
        name: str,
        model_a: str = "isolation_forest",
        model_b: str = "ensemble",
        traffic_split: int = 50,
    ) -> Dict[str, Any]:
        """Create a new A/B test experiment."""
        exp_id = f"exp_{int(time.time())}_{len(self._experiments)}"
        experiment = Experiment(
            id=exp_id,
            name=name,
            model_a=model_a,
            model_b=model_b,
            traffic_split=traffic_split,
        )
        self._experiments[exp_id] = experiment
        self._save_experiment(experiment)
        return experiment.to_dict()

    def list_experiments(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """List all experiments."""
        experiments = self._experiments.values()
        if active_only:
            experiments = [e for e in experiments if e.status == "active"]
        return [e.to_dict() for e in experiments]

    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID."""
        return self._experiments.get(experiment_id)

    def route_transaction(
        self, experiment_id: str, transaction_id: str
    ) -> Dict[str, Any]:
        """
        Determine which model variant to use for a transaction.
        Uses deterministic hashing for consistent routing.
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment or experiment.status != "active":
            return {"variant": "a", "model": "isolation_forest", "reason": "default"}

        # Deterministic hash-based routing
        hash_val = int(hashlib.md5(transaction_id.encode()).hexdigest(), 16)
        bucket = hash_val % 100

        if bucket < experiment.traffic_split:
            variant = "a"
            model = experiment.model_a
        else:
            variant = "b"
            model = experiment.model_b

        return {
            "variant": variant,
            "model": model,
            "experiment_id": experiment_id,
            "bucket": bucket,
            "split": experiment.traffic_split,
        }

    def record_result(
        self,
        experiment_id: str,
        variant: str,
        score: float,
        is_correct: bool = None,
    ):
        """Record a prediction result for an experiment variant."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return

        metrics = experiment.metrics_a if variant == "a" else experiment.metrics_b
        metrics["total"] += 1
        metrics["scores"].append(score)
        if is_correct is not None:
            if is_correct:
                metrics["correct"] += 1

        # Keep only last 10000 scores
        if len(metrics["scores"]) > 10000:
            metrics["scores"] = metrics["scores"][-10000:]

    def get_results(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get experiment results with statistical comparison.
        """
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return {"error": "Experiment not found"}

        def compute_stats(metrics: dict) -> dict:
            total = metrics["total"]
            if total == 0:
                return {"total": 0, "accuracy": None, "avg_score": None}

            accuracy = None
            if metrics["correct"] > 0 or total > 0:
                accuracy = round(metrics["correct"] / total, 4) if total > 0 else None

            scores = metrics["scores"]
            avg_score = round(sum(scores) / len(scores), 4) if scores else None

            return {
                "total": total,
                "accuracy": accuracy,
                "avg_score": avg_score,
                "score_std": round(float(__import__("numpy").std(scores)), 4) if len(scores) > 1 else None,
            }

        stats_a = compute_stats(experiment.metrics_a)
        stats_b = compute_stats(experiment.metrics_b)

        # Chi-squared test for significance (if enough data)
        significant = None
        p_value = None
        if stats_a["total"] >= 30 and stats_b["total"] >= 30:
            try:
                from scipy.stats import chi2_contingency
                import numpy as np

                correct_a = experiment.metrics_a["correct"]
                incorrect_a = stats_a["total"] - correct_a
                correct_b = experiment.metrics_b["correct"]
                incorrect_b = stats_b["total"] - correct_b

                if (correct_a + incorrect_a) > 0 and (correct_b + incorrect_b) > 0:
                    table = np.array([[correct_a, incorrect_a], [correct_b, incorrect_b]])
                    chi2, p, dof, expected = chi2_contingency(table)
                    p_value = round(float(p), 6)
                    significant = p < 0.05
            except Exception:
                pass

        return {
            "experiment": experiment.to_dict(),
            "model_a": {
                "model": experiment.model_a,
                "stats": stats_a,
            },
            "model_b": {
                "model": experiment.model_b,
                "stats": stats_b,
            },
            "significance": {
                "is_significant": significant,
                "p_value": p_value,
                "min_samples_per_variant": 30,
            },
            "recommendation": _get_recommendation(stats_a, stats_b, significant),
        }

    def promote_winner(self, experiment_id: str) -> Dict[str, Any]:
        """Mark experiment as complete and identify the winner."""
        experiment = self._experiments.get(experiment_id)
        if not experiment:
            return {"error": "Experiment not found"}

        results = self.get_results(experiment_id)
        stats_a = results["model_a"]["stats"]
        stats_b = results["model_b"]["stats"]

        winner = "a"
        if stats_b.get("accuracy") and stats_a.get("accuracy"):
            if stats_b["accuracy"] > stats_a["accuracy"]:
                winner = "b"

        experiment.status = "completed"
        self._save_experiment(experiment)

        return {
            "experiment_id": experiment_id,
            "winner": winner,
            "winning_model": experiment.model_a if winner == "a" else experiment.model_b,
            "status": "completed",
        }


def _get_recommendation(stats_a: dict, stats_b: dict, significant: bool) -> str:
    """Generate a human-readable recommendation."""
    if stats_a["total"] < 30 or stats_b["total"] < 30:
        return "Insufficient data. Need at least 30 samples per variant."

    if significant is None:
        return "Unable to compute significance."

    if not significant:
        return "No statistically significant difference between models. Continue collecting data."

    acc_a = stats_a.get("accuracy", 0) or 0
    acc_b = stats_b.get("accuracy", 0) or 0

    if acc_a > acc_b:
        return f"Model A is significantly better (accuracy: {acc_a:.1%} vs {acc_b:.1%}). Consider promoting Model A."
    else:
        return f"Model B is significantly better (accuracy: {acc_b:.1%} vs {acc_a:.1%}). Consider promoting Model B."


# Singleton
_ab_manager_instance = None


def get_ab_manager() -> ABTestManager:
    """Get or create singleton AB test manager."""
    global _ab_manager_instance
    if _ab_manager_instance is None:
        _ab_manager_instance = ABTestManager()
    return _ab_manager_instance
