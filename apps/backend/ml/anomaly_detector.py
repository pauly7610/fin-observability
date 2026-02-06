"""
Enhanced Anomaly Detector for Financial Compliance
Uses Isolation Forest with 6 features for production-ready anomaly detection.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle
import os
import logging
from datetime import datetime
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Production-ready anomaly detector using Isolation Forest.
    
    Features:
    1. amount - Transaction amount (normalized)
    2. hour - Hour of day (0-23)
    3. day_of_week - Day of week (0-6, Monday=0)
    4. is_weekend - Binary (0/1)
    5. is_off_hours - Binary (before 6am or after 10pm)
    6. txn_type_encoded - Transaction type (wire=2, ach=1, internal=0)
    """
    
    MODEL_PATH = "models/isolation_forest_v2.pkl"
    SCALER_PATH = "models/scaler_v2.pkl"
    VERSION = "2.0.0"
    FEATURE_NAMES = [
        "amount",
        "hour",
        "day_of_week",
        "is_weekend",
        "is_off_hours",
        "txn_type_encoded"
    ]
    
    TXN_TYPE_ENCODING = {
        "internal": 0,
        "ach": 1,
        "wire": 2
    }
    
    def __init__(self):
        """Initialize detector, loading existing model or training new one."""
        self.model = None
        self.scaler = None
        self._load_or_train()
    
    def _load_or_train(self) -> None:
        """Load existing model from disk or train a new one."""
        if os.path.exists(self.MODEL_PATH) and os.path.exists(self.SCALER_PATH):
            try:
                with open(self.MODEL_PATH, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.SCALER_PATH, 'rb') as f:
                    self.scaler = pickle.load(f)
                logger.info(f"Loaded anomaly detector model v{self.VERSION}")
                return
            except Exception as e:
                logger.warning(f"Failed to load model: {e}, training new one")
        
        self._train_default_model()
    
    def _train_default_model(self) -> None:
        """Train on synthetic normal transactions."""
        logger.info("Training new anomaly detection model...")
        
        # Generate 2000 synthetic normal transactions
        np.random.seed(42)
        n_samples = 2000
        
        # Normal transaction patterns:
        # - Amount: $100-$10,000 (log-normal distribution centered around $2000)
        amounts = np.random.lognormal(mean=7.5, sigma=0.8, size=n_samples)
        amounts = np.clip(amounts, 100, 15000)
        
        # - Hour: Business hours (9-17) with some variance
        hours = np.random.normal(loc=13, scale=2.5, size=n_samples)
        hours = np.clip(hours, 0, 23).astype(int)
        
        # - Day of week: Mostly weekdays (0-4)
        day_weights = [0.2, 0.2, 0.2, 0.2, 0.15, 0.025, 0.025]  # Mon-Sun
        days = np.random.choice(7, size=n_samples, p=day_weights)
        
        # Derived features
        is_weekend = (days >= 5).astype(int)
        is_off_hours = ((hours < 6) | (hours > 22)).astype(int)
        
        # Transaction types: mostly ACH and internal
        txn_types = np.random.choice([0, 1, 2], size=n_samples, p=[0.3, 0.5, 0.2])
        
        # Combine features
        X = np.column_stack([
            amounts,
            hours,
            days,
            is_weekend,
            is_off_hours,
            txn_types
        ])
        
        # Fit scaler
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100,
            max_samples='auto'
        )
        self.model.fit(X_scaled)
        
        # Save model and scaler
        os.makedirs("models", exist_ok=True)
        with open(self.MODEL_PATH, 'wb') as f:
            pickle.dump(self.model, f)
        with open(self.SCALER_PATH, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        logger.info(f"Trained and saved anomaly detector model v{self.VERSION}")
    
    def _extract_features(
        self,
        amount: float,
        timestamp: datetime,
        txn_type: str
    ) -> np.ndarray:
        """Extract feature vector from transaction data."""
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0
        is_off_hours = 1 if (hour < 6 or hour > 22) else 0
        txn_type_encoded = self.TXN_TYPE_ENCODING.get(txn_type.lower(), 1)
        
        return np.array([[
            amount,
            hour,
            day_of_week,
            is_weekend,
            is_off_hours,
            txn_type_encoded
        ]])
    
    def predict(
        self,
        amount: float,
        timestamp: datetime,
        txn_type: str
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Predict anomaly score for a transaction.
        
        Args:
            amount: Transaction amount in dollars
            timestamp: Transaction timestamp
            txn_type: Transaction type ('wire', 'ach', 'internal')
        
        Returns:
            Tuple of (anomaly_score, feature_details)
            - anomaly_score: 0.0-1.0 (higher = more anomalous)
            - feature_details: Dict with feature values and contributions
        """
        features = self._extract_features(amount, timestamp, txn_type)
        features_scaled = self.scaler.transform(features)
        
        # Isolation Forest decision_function returns anomaly score
        # More negative = more anomalous
        raw_score = self.model.decision_function(features_scaled)[0]
        
        # Normalize to 0-1 range (0 = normal, 1 = anomaly)
        # Typical range is -0.5 to 0.5
        normalized_score = 1 - (max(min(raw_score, 0.5), -0.5) + 0.5)
        
        # Build feature details for transparency
        feature_values = features[0]
        feature_details = {
            "model_version": self.VERSION,
            "raw_score": float(raw_score),
            "features": {
                name: float(value) 
                for name, value in zip(self.FEATURE_NAMES, feature_values)
            },
            "risk_factors": self._identify_risk_factors(feature_values, normalized_score)
        }
        
        return float(normalized_score), feature_details
    
    def _identify_risk_factors(
        self,
        features: np.ndarray,
        score: float
    ) -> list:
        """Identify which features contributed to anomaly score."""
        risk_factors = []
        
        amount, hour, day_of_week, is_weekend, is_off_hours, txn_type = features
        
        if amount > 50000:
            risk_factors.append(f"High amount: ${amount:,.2f}")
        elif amount > 25000:
            risk_factors.append(f"Elevated amount: ${amount:,.2f}")
        
        if is_off_hours:
            risk_factors.append(f"Off-hours transaction (hour: {int(hour)})")
        
        if is_weekend:
            risk_factors.append("Weekend transaction")
        
        if txn_type == 2 and amount > 10000:
            risk_factors.append("Large wire transfer")
        
        if not risk_factors and score > 0.5:
            risk_factors.append("Statistical outlier - unusual pattern combination")
        
        return risk_factors
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata for status endpoints."""
        return {
            "version": self.VERSION,
            "algorithm": "IsolationForest",
            "features": self.FEATURE_NAMES,
            "training_samples": 2000,
            "contamination": 0.1,
            "model_path": self.MODEL_PATH
        }


# Singleton instance for use across the application
_detector_instance = None


def get_detector() -> AnomalyDetector:
    """Get or create singleton detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = AnomalyDetector()
    return _detector_instance
