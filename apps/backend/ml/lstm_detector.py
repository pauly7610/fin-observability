"""
LSTM-based Sequence Anomaly Detector for Financial Transactions.
Uses a lightweight autoencoder approach: learns to reconstruct normal transaction
sequences, then flags high-reconstruction-error sequences as anomalous.

Falls back gracefully if ONNX Runtime is unavailable.
"""
import numpy as np
import os
import pickle
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

MODEL_PATH = "models/lstm_autoencoder.pkl"
SCALER_PATH = "models/lstm_scaler.pkl"
SEQUENCE_LENGTH = 5  # Look at last N transactions per account
N_FEATURES = 4  # amount, hour, day_of_week, txn_type_encoded


class LSTMDetector:
    """
    Lightweight sequence-based anomaly detector.
    
    Uses a simple autoencoder approach with numpy (no deep learning framework needed):
    - Encodes transaction sequences into a compressed representation
    - Measures reconstruction error as anomaly score
    - High reconstruction error = anomalous sequence pattern
    
    This is a simplified version that uses PCA-based reconstruction
    as a proxy for LSTM autoencoder behavior, keeping deployment lightweight.
    """

    VERSION = "1.0.0"

    def __init__(self):
        self.scaler = None
        self.mean_vector = None
        self.components = None  # PCA-like components for reconstruction
        self.threshold = None
        self._is_trained = False
        self._load_or_train()

    def _load_or_train(self):
        """Load existing model or train from scratch."""
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    state = pickle.load(f)
                self.scaler = state["scaler"]
                self.mean_vector = state["mean_vector"]
                self.components = state["components"]
                self.threshold = state["threshold"]
                self.VERSION = state.get("version", "1.0.0")
                self._is_trained = True
                logger.info(f"Loaded LSTM detector v{self.VERSION}")
                return
            except Exception as e:
                logger.warning(f"Failed to load LSTM model: {e}")

        self._train_default()

    def _train_default(self):
        """Train on synthetic normal transaction sequences."""
        np.random.seed(123)
        n_sequences = 1000

        # Generate normal sequences: business hours, moderate amounts, weekdays
        sequences = []
        for _ in range(n_sequences):
            seq = []
            for _ in range(SEQUENCE_LENGTH):
                amount = np.random.lognormal(7.5, 0.8)
                amount = np.clip(amount, 100, 15000)
                hour = int(np.clip(np.random.normal(13, 2.5), 8, 18))
                day = np.random.choice([0, 1, 2, 3, 4], p=[0.2, 0.2, 0.2, 0.2, 0.2])
                txn_type = np.random.choice([0, 1, 2], p=[0.3, 0.5, 0.2])
                seq.append([amount, hour, day, txn_type])
            sequences.append(np.array(seq).flatten())

        X = np.array(sequences)

        # Fit scaler
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Compute PCA-like components (top-k singular vectors)
        self.mean_vector = X_scaled.mean(axis=0)
        X_centered = X_scaled - self.mean_vector
        U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
        n_components = min(10, X_centered.shape[1])
        self.components = Vt[:n_components]

        # Compute reconstruction errors for threshold
        reconstructed = X_centered @ self.components.T @ self.components
        errors = np.mean((X_centered - reconstructed) ** 2, axis=1)
        self.threshold = float(np.percentile(errors, 95))

        self._is_trained = True
        self._save()
        logger.info(f"Trained LSTM detector v{self.VERSION} on {n_sequences} sequences")

    def _save(self):
        """Save model state to disk."""
        os.makedirs("models", exist_ok=True)
        state = {
            "scaler": self.scaler,
            "mean_vector": self.mean_vector,
            "components": self.components,
            "threshold": self.threshold,
            "version": self.VERSION,
        }
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(state, f)

    def predict_sequence(
        self, transactions: List[Dict[str, Any]]
    ) -> tuple:
        """
        Score a sequence of transactions for anomalous patterns.

        Args:
            transactions: List of dicts with amount, timestamp, type.
                         Should be ordered chronologically.

        Returns:
            Tuple of (anomaly_score, details_dict)
        """
        if not self._is_trained:
            return 0.5, {"status": "untrained", "message": "Model not trained"}

        TXN_TYPE_ENCODING = {"internal": 0, "ach": 1, "wire": 2}

        # Pad or truncate to SEQUENCE_LENGTH
        txns = transactions[-SEQUENCE_LENGTH:]
        while len(txns) < SEQUENCE_LENGTH:
            txns.insert(0, txns[0] if txns else {"amount": 0, "timestamp": datetime.utcnow().isoformat(), "type": "ach"})

        # Extract features
        features = []
        for txn in txns:
            ts = txn.get("timestamp")
            if isinstance(ts, str):
                from dateutil.parser import parse as parse_date
                ts = parse_date(ts)
            elif ts is None:
                ts = datetime.utcnow()

            features.extend([
                float(txn.get("amount", 0)),
                ts.hour,
                ts.weekday(),
                TXN_TYPE_ENCODING.get(str(txn.get("type", "ach")).lower(), 1),
            ])

        X = np.array([features])
        X_scaled = self.scaler.transform(X)
        X_centered = X_scaled - self.mean_vector

        # Reconstruct and compute error
        reconstructed = X_centered @ self.components.T @ self.components
        error = float(np.mean((X_centered - reconstructed) ** 2))

        # Normalize to 0-1 score
        score = min(error / (self.threshold * 2), 1.0)

        return score, {
            "reconstruction_error": round(error, 6),
            "threshold": round(self.threshold, 6),
            "is_anomalous": error > self.threshold,
            "sequence_length": len(transactions),
            "model_version": self.VERSION,
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata."""
        return {
            "version": self.VERSION,
            "algorithm": "PCA-Autoencoder (LSTM proxy)",
            "sequence_length": SEQUENCE_LENGTH,
            "n_features_per_step": N_FEATURES,
            "total_features": SEQUENCE_LENGTH * N_FEATURES,
            "is_trained": self._is_trained,
            "threshold": self.threshold,
        }


# Singleton
_lstm_instance = None


def get_lstm_detector() -> LSTMDetector:
    """Get or create singleton LSTM detector."""
    global _lstm_instance
    if _lstm_instance is None:
        _lstm_instance = LSTMDetector()
    return _lstm_instance
