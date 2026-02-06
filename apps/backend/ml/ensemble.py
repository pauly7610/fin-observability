"""
Ensemble Anomaly Detector combining Isolation Forest and Sequence-based detection.
Weighted average of both models for more robust anomaly scoring.
"""
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Default weights: Isolation Forest is primary, sequence model is supplementary
DEFAULT_IF_WEIGHT = 0.6
DEFAULT_SEQ_WEIGHT = 0.4


class EnsembleDetector:
    """
    Combines Isolation Forest (point anomaly) with sequence-based detection
    for more robust compliance anomaly scoring.
    
    Falls back to IF-only if sequence model is unavailable.
    """

    def __init__(
        self,
        if_weight: float = DEFAULT_IF_WEIGHT,
        seq_weight: float = DEFAULT_SEQ_WEIGHT,
    ):
        self.if_weight = if_weight
        self.seq_weight = seq_weight
        self._if_detector = None
        self._seq_detector = None

    @property
    def if_detector(self):
        if self._if_detector is None:
            from .anomaly_detector import get_detector
            self._if_detector = get_detector()
        return self._if_detector

    @property
    def seq_detector(self):
        if self._seq_detector is None:
            try:
                from .lstm_detector import get_lstm_detector
                self._seq_detector = get_lstm_detector()
            except Exception as e:
                logger.warning(f"Sequence detector unavailable: {e}")
                self._seq_detector = None
        return self._seq_detector

    def predict(
        self,
        amount: float,
        timestamp: datetime,
        txn_type: str,
        transaction_history: List[Dict[str, Any]] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Ensemble prediction combining both models.

        Args:
            amount: Transaction amount
            timestamp: Transaction timestamp
            txn_type: Transaction type
            transaction_history: Optional list of recent transactions for sequence analysis

        Returns:
            Tuple of (ensemble_score, details_dict)
        """
        # Isolation Forest score
        if_score, if_details = self.if_detector.predict(amount, timestamp, txn_type)

        # Sequence score (if history available and model loaded)
        seq_score = None
        seq_details = None
        effective_if_weight = 1.0
        effective_seq_weight = 0.0

        if transaction_history and self.seq_detector:
            try:
                # Add current transaction to history
                current = {
                    "amount": amount,
                    "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
                    "type": txn_type,
                }
                history_with_current = list(transaction_history) + [current]
                seq_score, seq_details = self.seq_detector.predict_sequence(history_with_current)
                effective_if_weight = self.if_weight
                effective_seq_weight = self.seq_weight
            except Exception as e:
                logger.warning(f"Sequence prediction failed, using IF only: {e}")

        # Weighted ensemble
        if seq_score is not None:
            ensemble_score = (
                effective_if_weight * if_score + effective_seq_weight * seq_score
            )
        else:
            ensemble_score = if_score

        return ensemble_score, {
            "ensemble_score": round(ensemble_score, 4),
            "isolation_forest": {
                "score": round(if_score, 4),
                "weight": effective_if_weight,
                "details": if_details,
            },
            "sequence_model": {
                "score": round(seq_score, 4) if seq_score is not None else None,
                "weight": effective_seq_weight,
                "details": seq_details,
                "available": seq_score is not None,
            },
            "weights": {
                "isolation_forest": effective_if_weight,
                "sequence": effective_seq_weight,
            },
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Return ensemble metadata."""
        info = {
            "type": "ensemble",
            "weights": {
                "isolation_forest": self.if_weight,
                "sequence": self.seq_weight,
            },
            "models": {
                "isolation_forest": self.if_detector.get_model_info(),
            },
        }
        if self.seq_detector:
            info["models"]["sequence"] = self.seq_detector.get_model_info()
        else:
            info["models"]["sequence"] = {"status": "unavailable"}
        return info


# Singleton
_ensemble_instance = None


def get_ensemble_detector() -> EnsembleDetector:
    """Get or create singleton ensemble detector."""
    global _ensemble_instance
    if _ensemble_instance is None:
        _ensemble_instance = EnsembleDetector()
    return _ensemble_instance
