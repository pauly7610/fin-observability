from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import SystemMetric as SystemMetricModel
from ..database import get_db
from ..security import require_role
from datetime import datetime
import csv
from fastapi.responses import StreamingResponse
from io import StringIO
import os
from apps.backend import siem

router = APIRouter(prefix="/system_metrics", tags=["system_metrics", "export"])

@router.get("/export")
async def export_system_metrics(
    metric_name: Optional[str] = None,
    is_anomaly: Optional[bool] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    format: str = "csv",
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
):
    """
    Export system metrics as CSV or JSON for audit/review.
    """
    try:
        query = db.query(SystemMetricModel)
        if metric_name:
            query = query.filter(SystemMetricModel.metric_name == metric_name)
        if is_anomaly is not None:
            query = query.filter(SystemMetricModel.is_anomaly == is_anomaly)
        if start:
            from dateutil.parser import parse
            query = query.filter(SystemMetricModel.timestamp >= parse(start))
        if end:
            from dateutil.parser import parse
            query = query.filter(SystemMetricModel.timestamp <= parse(end))
        metrics = query.order_by(SystemMetricModel.timestamp.desc()).all()
        if format == "csv":
            fieldnames = [c.name for c in SystemMetricModel.__table__.columns]
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for m in metrics:
                writer.writerow({fn: getattr(m, fn) for fn in fieldnames})
            output.seek(0)
            siem.send_syslog_event(
    event="System metrics exported as CSV",
    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    extra={"count": len(metrics), "user": str(user.get('id') if hasattr(user, 'id') else user)}
)
            return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=system_metrics.csv"})
        else:
            siem.send_syslog_event(
    event="System metrics exported as JSON",
    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    extra={"count": len(metrics), "user": str(user.get('id') if hasattr(user, 'id') else user)}
)
            return [m.__dict__ for m in metrics]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
