from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
import numpy as np
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    def __init__(self):
        self.models = {
            "isolation_forest": IsolationForest(contamination=0.1, random_state=42),
            "knn": LocalOutlierFactor(n_neighbors=20, contamination=0.1),
        }
        self.scaler = StandardScaler()

    def _preprocess_data(self, data: List[Dict[str, Any]]) -> np.ndarray:
        """Convert list of dictionaries to numpy array for model input."""
        # Extract numerical features
        features = []
        for item in data:
            feature_vector = []
            for key, value in item.items():
                if isinstance(value, (int, float)):
                    feature_vector.append(value)
            features.append(feature_vector)
        return np.array(features)

    def detect_anomalies(
        self,
        data: List[Dict[str, Any]],
        model_type: str = "isolation_forest",
        parameters: Dict[str, Any] = None,
    ) -> Tuple[List[bool], List[float], Dict[str, Any]]:
        """
        Detect anomalies in the input data using the specified model.

        Args:
            data: List of dictionaries containing the data points
            model_type: Type of model to use ("isolation_forest" or "knn")
            parameters: Optional parameters to override model defaults

        Returns:
            Tuple of (anomaly_flags, anomaly_scores, model_meta)
        """
        try:
            if model_type not in self.models:
                raise ValueError(f"Unsupported model type: {model_type}")

            # Preprocess data
            X = self._preprocess_data(data)
            if len(X) == 0:
                raise ValueError("No valid numerical features found in data")

            # Scale the data
            X_scaled = self.scaler.fit_transform(X)

            # Get model and update parameters if provided
            model = self.models[model_type]
            if parameters:
                model.set_params(**parameters)

            # Fit and predict
            if model_type == "isolation_forest":
                model.fit(X_scaled)
                scores = -model.score_samples(X_scaled)  # Negative scores for anomalies
                predictions = model.predict(X_scaled)
                anomaly_flags = [bool(pred == -1) for pred in predictions]
            else:  # KNN
                predictions = model.fit_predict(X_scaled)
                scores = (
                    -model.negative_outlier_factor_
                )  # Negative scores for anomalies
                anomaly_flags = [bool(pred == -1) for pred in predictions]

            # Prepare meta
            model_meta = {
                "model_type": model_type,
                "n_samples": len(data),
                "n_features": X.shape[1],
                "parameters": model.get_params(),
            }

            return anomaly_flags, scores.tolist(), model_meta
        except Exception as e:
            from apps.backend.main import get_logger

            get_logger(__name__).error("Error in anomaly detection", error=str(e))
            raise
