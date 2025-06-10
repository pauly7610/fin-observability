from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..schemas import AnomalyDetectionRequest, AnomalyDetectionResponse
from ..services.anomaly_detection import AnomalyDetectionService
from ..services.agentic_workflow_service import AgenticWorkflowService
from ..models import Transaction, SystemMetric
import logging
import os
from apps.backend import siem

router = APIRouter(prefix="/anomaly", tags=["anomaly"])
logger = logging.getLogger(__name__)
anomaly_service = AnomalyDetectionService()
workflow_service = AgenticWorkflowService()

@router.post("/detect", response_model=AnomalyDetectionResponse)
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    db: Session = Depends(get_db)
):
    """
    Detect anomalies in the provided data using the specified model.
    """
    try:
        anomaly_flags, scores, meta = anomaly_service.detect_anomalies(
            request.data,
            request.model_type,
            request.parameters
        )
        siem.send_syslog_event(
            f"Anomaly detection performed: model={request.model_type}, count={len(request.data)}",
            host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
            port=int(os.getenv("SIEM_SYSLOG_PORT", "514"))
        )
        return AnomalyDetectionResponse(
            anomalies=[{
                "index": i,
                "is_anomaly": flag,
                "score": score,
                "data": request.data[i]
            } for i, (flag, score) in enumerate(zip(anomaly_flags, scores))],
            scores=scores,
            model_meta=meta
        )
    except Exception as e:
        logger.error(f"Error in anomaly detection endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions/recent")
async def get_recent_anomalies(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get recent transactions marked as anomalies.
    """
    try:
        anomalies = db.query(Transaction)\
            .filter(Transaction.is_anomaly == True)\
            .order_by(Transaction.timestamp.desc())\
            .limit(limit)\
            .all()
        siem.send_syslog_event(
            f"Queried recent anomalous transactions, count={len(anomalies)}",
            host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
            port=int(os.getenv("SIEM_SYSLOG_PORT", "514"))
        )
        return anomalies
    except Exception as e:
        logger.error(f"Error fetching recent anomalies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/recent")
async def get_recent_metric_anomalies(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get recent system metrics marked as anomalies.
    """
    try:
        anomalies = db.query(SystemMetric)\
            .filter(SystemMetric.is_anomaly == True)\
            .order_by(SystemMetric.timestamp.desc())\
            .limit(limit)\
            .all()
        siem.send_syslog_event(
            f"Queried recent anomalous system metrics",
            host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
            port=int(os.getenv("SIEM_SYSLOG_PORT", "514"))
        )
        return anomalies
    except Exception as e:
        logger.error(f"Error fetching recent metric anomalies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train")
async def train_anomaly_model(
    source: str = Body("transactions", embed=True, description="Source table: 'transactions' or 'system_metrics'"),
    feature_keys: Optional[List[str]] = Body(None, embed=True, description="List of feature keys to use from meta/labels (optional)"),
    db: Session = Depends(get_db)
):
    """
    Retrain the anomaly detection model from historical data.
    """
    try:
        result = anomaly_service.retrain_from_historical(db, source=source, feature_keys=feature_keys)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("reason", "Unknown error"))
        siem.send_syslog_event(
            f"Anomaly model retrained: source={source}",
            host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
            port=int(os.getenv("SIEM_SYSLOG_PORT", "514"))
        )
        return {"message": "Model retrained successfully"}
    except Exception as e:
        logger.error(f"Error retraining anomaly model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))