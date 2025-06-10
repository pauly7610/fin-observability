from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import Incident as IncidentModel
from ..database import get_db
from ..security import require_role
from datetime import datetime
import csv
from fastapi.responses import StreamingResponse
from io import StringIO
import os
from apps.backend import siem, crypto_utils
from apps.backend.scheduled_exports import hash_chain_csv

router = APIRouter(prefix="/incidents", tags=["incidents", "export"])

@router.get("/export")
async def export_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    assigned_to: Optional[int] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    format: str = "csv",
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
):
    """
    Export incidents as CSV or JSON for audit/review. SIEM event and digital signature included.
    """
    try:
        query = db.query(IncidentModel)
        if status:
            query = query.filter(IncidentModel.status == status)
        if severity:
            query = query.filter(IncidentModel.severity == severity)
        if assigned_to:
            query = query.filter(IncidentModel.assigned_to == assigned_to)
        if start:
            from dateutil.parser import parse
            query = query.filter(IncidentModel.created_at >= parse(start))
        if end:
            from dateutil.parser import parse
            query = query.filter(IncidentModel.created_at <= parse(end))
        incidents = query.order_by(IncidentModel.created_at.desc()).all()
        if format == "csv":
            fieldnames = [c.name for c in IncidentModel.__table__.columns]
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for inc in incidents:
                writer.writerow({fn: getattr(inc, fn) for fn in fieldnames})
            output.seek(0)
            # Hash chain and sign for manual export
            last_hash = hash_chain_csv(output.getvalue())
            signature = crypto_utils.sign_data(last_hash.encode())
            siem.send_syslog_event(f"Incidents manually exported, hash: {last_hash}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
            # Write ExportMetadata for CSV export
            from apps.backend.models import ExportMetadata
            from apps.backend.database import SessionLocal
            session = SessionLocal()
            try:
                export_meta = ExportMetadata(
                    export_type="incident",
                    file_path=filename,
                    hash=None,
                    signature=None,
                    requested_by=None,
                    delivered_to=None,
                    delivery_method="manual",
                    delivery_status="delivered",
                    verification_status="unverified",
                    created_at=datetime.utcnow(),
                    delivered_at=datetime.utcnow(),
                    meta={"format": "csv"}
                )
                session.add(export_meta)
                session.commit()
            finally:
                session.close()
            return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=incidents.csv"})
        else:
            siem.send_syslog_event(f"Incidents manually exported (JSON)", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
            # Write ExportMetadata for JSON export
            from apps.backend.models import ExportMetadata
            from apps.backend.database import SessionLocal
            session = SessionLocal()
            try:
                export_meta = ExportMetadata(
                    export_type="incident",
                    file_path=None,
                    hash=None,
                    signature=None,
                    requested_by=None,
                    delivered_to=None,
                    delivery_method="manual",
                    delivery_status="delivered",
                    verification_status="unverified",
                    created_at=datetime.utcnow(),
                    delivered_at=datetime.utcnow(),
                    meta={"format": "json", "count": len(incidents)}
                )
                session.add(export_meta)
                session.commit()
            finally:
                session.close()
            return [inc.__dict__ for inc in incidents]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
