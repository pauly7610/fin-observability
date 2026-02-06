"""
SHAP-based Explainability Module for Compliance Anomaly Detection.
Provides feature-level explanations for individual predictions.
"""
import numpy as np
import shap
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Cache the explainer to avoid re-initialization (~200ms first call, ~5ms after)
_explainer_cache = None
_explainer_model_version = None


def get_shap_explainer(detector):
    """Get or create cached SHAP TreeExplainer for the detector's model."""
    global _explainer_cache, _explainer_model_version

    if _explainer_cache is not None and _explainer_model_version == detector.VERSION:
        return _explainer_cache

    logger.info(f"Initializing SHAP TreeExplainer for model v{detector.VERSION}")
    _explainer_cache = shap.TreeExplainer(detector.model)
    _explainer_model_version = detector.VERSION
    return _explainer_cache


def explain_prediction(
    detector,
    amount: float,
    timestamp: datetime,
    txn_type: str,
) -> Dict[str, Any]:
    """
    Explain a single prediction using SHAP values.

    Args:
        detector: AnomalyDetector instance
        amount: Transaction amount
        timestamp: Transaction timestamp
        txn_type: Transaction type (ach, wire, internal)

    Returns:
        Dict with SHAP values per feature, base value, and risk direction.
    """
    # Extract and scale features
    features_raw = detector._extract_features(amount, timestamp, txn_type)
    features_scaled = detector.scaler.transform(features_raw)

    # Get SHAP values
    explainer = get_shap_explainer(detector)
    shap_values = explainer.shap_values(features_scaled)

    # shap_values shape: (1, n_features)
    sv = shap_values[0] if len(shap_values.shape) > 1 else shap_values
    base_value = float(explainer.expected_value)

    # Build per-feature explanation
    feature_explanations = []
    for i, name in enumerate(detector.FEATURE_NAMES):
        raw_val = float(features_raw[0][i])
        shap_val = float(sv[i])
        feature_explanations.append({
            "feature": name,
            "value": raw_val,
            "shap_value": round(shap_val, 6),
            "direction": "risk_increasing" if shap_val < 0 else "risk_decreasing",
            "abs_importance": round(abs(shap_val), 6),
        })

    # Sort by absolute importance (most impactful first)
    feature_explanations.sort(key=lambda x: x["abs_importance"], reverse=True)

    # Get the anomaly score for context
    score, details = detector.predict(amount, timestamp, txn_type)

    return {
        "anomaly_score": score,
        "base_value": round(base_value, 6),
        "model_output": round(base_value + sum(sv), 6),
        "model_version": detector.VERSION,
        "features": feature_explanations,
        "top_risk_factors": [
            f for f in feature_explanations if f["direction"] == "risk_increasing"
        ][:3],
        "top_safe_factors": [
            f for f in feature_explanations if f["direction"] == "risk_decreasing"
        ][:3],
        "waterfall": {
            "base": round(base_value, 6),
            "steps": [
                {"feature": f["feature"], "contribution": f["shap_value"]}
                for f in feature_explanations
            ],
            "final": round(base_value + sum(sv), 6),
        },
    }


def explain_batch(
    detector,
    transactions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Explain a batch of transactions and return aggregate feature importance.

    Args:
        detector: AnomalyDetector instance
        transactions: List of dicts with amount, timestamp, type

    Returns:
        Dict with mean absolute SHAP values per feature.
    """
    from dateutil.parser import parse as parse_date

    all_features = []
    for txn in transactions:
        ts = txn.get("timestamp")
        if isinstance(ts, str):
            ts = parse_date(ts)
        features_raw = detector._extract_features(
            float(txn["amount"]), ts, txn.get("type", "ach")
        )
        features_scaled = detector.scaler.transform(features_raw)
        all_features.append(features_scaled[0])

    X = np.array(all_features)
    explainer = get_shap_explainer(detector)
    shap_values = explainer.shap_values(X)

    # Mean absolute SHAP values
    mean_abs = np.mean(np.abs(shap_values), axis=0)

    importance = []
    for i, name in enumerate(detector.FEATURE_NAMES):
        importance.append({
            "feature": name,
            "mean_abs_shap": round(float(mean_abs[i]), 6),
        })

    importance.sort(key=lambda x: x["mean_abs_shap"], reverse=True)

    return {
        "n_transactions": len(transactions),
        "model_version": detector.VERSION,
        "feature_importance": importance,
    }
