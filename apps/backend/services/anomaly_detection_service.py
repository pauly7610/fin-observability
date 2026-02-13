import numpy as np
from sklearn.ensemble import IsolationForest
from typing import List, Dict, Any
import logging

from apps.backend.models import Transaction, SystemMetric

logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    def __init__(self, contamination: float = 0.01):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.is_trained = False

    def retrain_from_historical(
        self, db, source: str = "transactions", feature_keys: list = None
    ) -> dict:
        """
        Retrain the anomaly detection model using historical data from the database.
        NOTE: Ideally, the first step should be to load and train on a curated, labeled historical dataset
        with both normal and anomalous examples (ground truth). This is currently unavailable, so we
        fallback to available transactions/system_metrics for MVP. Replace this block with labeled data loading
        when available.
        :param db: SQLAlchemy session
        :param source: 'transactions' or 'system_metrics'
        :param feature_keys: list of keys in meta to use as features (if None, use all numeric in meta)
        :return: dict with training status
        """
        # TODO: For production, replace the following with loading and training on a curated, labeled
        # historical dataset containing both normal and anomalous examples. This ensures robust model performance.
        # Currently using available transaction/metric data for MVP purposes only.

        if source == "transactions":
            records = (
                db.query(Transaction).filter(Transaction.status == "completed").all()
            )
            data = []
            for tx in records:
                meta = tx.meta or {}
                if feature_keys:
                    features = [meta.get(k, 0.0) for k in feature_keys]
                else:
                    features = [v for v in meta.values() if isinstance(v, (int, float))]
                if features:
                    data.append(features)
        elif source == "system_metrics":
            records = db.query(SystemMetric).all()
            data = []
            for m in records:
                meta = m.labels or {}
                features = [m.value] + [
                    v for v in meta.values() if isinstance(v, (int, float))
                ]
                data.append(features)
        else:
            return {"success": False, "reason": f"Unknown source: {source}"}
        if not data:
            return {"success": False, "reason": "No data found for retraining."}
        try:
            self.fit(data)
            return {"success": True, "n_samples": len(data), "source": source}
        except Exception as e:
            return {"success": False, "reason": str(e)}

    def fit(self, data: List[List[float]]):
        self.model.fit(data)
        self.is_trained = True
        logger.info("Anomaly detection model trained.")

    def predict(self, data: List[List[float]]) -> List[int]:
        if not self.is_trained:
            raise RuntimeError("Model not trained.")
        return self.model.predict(data)

    def anomaly_score(self, data: List[List[float]]) -> List[float]:
        if not self.is_trained:
            raise RuntimeError("Model not trained.")
        return self.model.decision_function(data)

    def detect(self, features: List[float]) -> Dict[str, Any]:
        if not self.is_trained:
            return {"anomaly": False, "score": 0.0, "reason": "Model not trained."}
        prediction = self.model.predict([features])[0]
        score = self.model.decision_function([features])[0]
        is_anomaly = prediction == -1
        return {"anomaly": is_anomaly, "score": float(score)}
