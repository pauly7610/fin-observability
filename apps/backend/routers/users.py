from fastapi import APIRouter, Depends, HTTPException
from slowapi.decorator import limiter as rate_limiter
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
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

router = APIRouter(prefix="/users", tags=["users", "export"])

@router.get("/export")
@rate_limiter("15/minute")  # Export endpoint, moderate limit
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
    user_id = getattr(user, 'id', None) if hasattr(user, 'id') else None
    # Approval workflow integration
    from apps.backend.approval import require_approval
    approved, approval_req = require_approval(
        db=db,
        resource_type="user_export",
        resource_id=f"users_{role}_{is_active}_{start}_{end}",
        user_id=user_id,
        reason="Export users for audit/review",
        meta={"role": role, "is_active": is_active, "start": start, "end": end}
    )
    if not approved:
        return {"detail": "Export requires approval", "approval_request_id": approval_req.id, "status": approval_req.status.value}
    with tracer.start_as_current_span("export.users") as span:
        span.set_attribute("user.id", user_id)
        span.set_attribute("export.format", format)
        span.set_attribute("role", role)
        span.set_attribute("is_active", is_active)
        span.set_attribute("start", str(start) if start else None)
        span.set_attribute("end", str(end) if end else None)
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
            span.set_attribute("export.record_count", len(users))
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
                    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
                    delivery_status="delivered",
                    verification_status="unverified",
                    created_at=datetime.utcnow(),
                    delivered_at=datetime.utcnow(),
                    meta={"format": "csv"}
                )
                return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=users.csv"})
            else:
                siem.send_syslog_event(
                    f"Users exported as JSON, count={len(users)}",
                    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
                    port=int(os.getenv("SIEM_SYSLOG_PORT", "514"))
                )
                from apps.backend.models import ExportMetadata
                from apps.backend.database import SessionLocal
                session = SessionLocal()
                try:
                    export_meta = ExportMetadata(
                        export_type="user",
                        file_path="users.json",
                        hash=None,
                        signature=None,
                        requested_by=user_id,
                        delivered_to=None,
                        delivery_method="manual",
                        delivery_status="delivered",
                        verification_status="unverified",
                    )
                    session.add(export_meta)
                    session.commit()
                finally:
                    session.close()
                return [u.__dict__ for u in users]
        except Exception as e:
            span.record_exception(e)
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))
