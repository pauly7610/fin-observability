from fastapi import APIRouter, Depends, HTTPException, Request
from apps.backend.rate_limit import limiter
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
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents", "export"])

@router.get("/export")
@limiter.limit("15/minute")  # Export endpoint, moderate limit
async def export_incidents(request: Request,
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
    user_id = getattr(user, 'id', None) if hasattr(user, 'id') else None
    # Approval workflow integration
    from apps.backend.approval import require_approval
    approved, approval_req = require_approval(
        db=db,
        resource_type="incident_export",
        resource_id=f"incidents_{status}_{severity}_{assigned_to}_{start}_{end}",
        user_id=user_id,
        reason="Export incidents for audit/review",
        meta={"status": status, "severity": severity, "assigned_to": assigned_to, "start": start, "end": end}
    )
    if not approved:
        # Block export, return approval pending info
        return {"detail": "Export requires approval", "approval_request_id": approval_req.id, "status": approval_req.status.value}
    with tracer.start_as_current_span("export.incidents") as span:
        span.set_attribute("user.id", user_id)
        span.set_attribute("export.format", format)
        span.set_attribute("status", status)
        span.set_attribute("severity", severity)
        span.set_attribute("assigned_to", assigned_to)
        span.set_attribute("start", str(start) if start else None)
        span.set_attribute("end", str(end) if end else None)
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
            span.set_attribute("export.record_count", len(incidents))
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
                span.set_attribute("export.hash", last_hash)
                span.set_attribute("export.signature", signature.hex() if hasattr(signature, 'hex') else str(signature))
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
                )
                    session.add(export_meta)
                    session.commit()
                finally:
                    session.close()
                return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=incidents.csv"})
            else:
                siem.send_syslog_event(
    event="Incidents exported as JSON",
    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    extra={"count": len(incidents), "user": str(user.get('id') if hasattr(user, 'id') else user)}
)
                return [inc.__dict__ for inc in incidents]
        except Exception as e:
            span.record_exception(e)
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))
