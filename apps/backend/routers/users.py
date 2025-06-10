from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import User as UserModel
from ..database import get_db
from ..security import require_role
from datetime import datetime
import csv
from fastapi.responses import StreamingResponse
from io import StringIO
import os
from apps.backend import siem

router = APIRouter(prefix="/users", tags=["users", "export"])

@router.get("/export")
async def export_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    format: str = "csv",
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin"]))
):
    """
    Export users as CSV or JSON for audit/review.
    """
    try:
        query = db.query(UserModel)
        if role:
            query = query.filter(UserModel.role == role)
        if is_active is not None:
            query = query.filter(UserModel.is_active == is_active)
        if start:
            from dateutil.parser import parse
            query = query.filter(UserModel.created_at >= parse(start))
        if end:
            from dateutil.parser import parse
            query = query.filter(UserModel.created_at <= parse(end))
        users = query.order_by(UserModel.created_at.desc()).all()
        if format == "csv":
            fieldnames = [c.name for c in UserModel.__table__.columns]
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for u in users:
                writer.writerow({fn: getattr(u, fn) for fn in fieldnames})
            output.seek(0)
            siem.send_syslog_event(
                f"Users exported as CSV, count={len(users)}",
                host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
                port=int(os.getenv("SIEM_SYSLOG_PORT", "514"))
            )
            # Write ExportMetadata for CSV export
            from apps.backend.models import ExportMetadata
            from apps.backend.database import SessionLocal
            session = SessionLocal()
            try:
                export_meta = ExportMetadata(
                    export_type="user",
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
            return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=users.csv"})
        else:
            siem.send_syslog_event(
                f"Users exported as JSON, count={len(users)}",
                host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
                port=int(os.getenv("SIEM_SYSLOG_PORT", "514"))
            )
            # Write ExportMetadata for JSON export
            from apps.backend.models import ExportMetadata
            from apps.backend.database import SessionLocal
            session = SessionLocal()
            try:
                export_meta = ExportMetadata(
                    export_type="user",
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
                    meta={"format": "json", "count": len(users)}
                )
                session.add(export_meta)
                session.commit()
            finally:
                session.close()
            return [u.__dict__ for u in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
