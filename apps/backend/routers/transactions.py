from fastapi import APIRouter, Depends, HTTPException
from slowapi.decorator import limiter as rate_limiter
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import Transaction as TransactionModel
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

router = APIRouter(prefix="/transactions", tags=["transactions", "export"])

@router.get("/export")
@rate_limiter("15/minute")  # Export endpoint, moderate limit
async def export_transactions(
    status: Optional[str] = None,
    currency: Optional[str] = None,
    is_anomaly: Optional[bool] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    format: str = "csv",
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
):
    """
    Export transactions as CSV or JSON for audit/review. SIEM event and digital signature included.
    """
    user_id = getattr(user, 'id', None) if hasattr(user, 'id') else None
    # Approval workflow integration
    from apps.backend.approval import require_approval
    approved, approval_req = require_approval(
        db=db,
        resource_type="transaction_export",
        resource_id=f"transactions_{status}_{currency}_{is_anomaly}_{start}_{end}",
        user_id=user_id,
        reason="Export transactions for audit/review",
        meta={"status": status, "currency": currency, "is_anomaly": is_anomaly, "start": start, "end": end}
    )
    if not approved:
        return {"detail": "Export requires approval", "approval_request_id": approval_req.id, "status": approval_req.status.value}
    with tracer.start_as_current_span("export.transactions") as span:
        span.set_attribute("user.id", user_id)
        span.set_attribute("export.format", format)
        span.set_attribute("status", status)
        span.set_attribute("currency", currency)
        span.set_attribute("is_anomaly", is_anomaly)
        span.set_attribute("start", str(start) if start else None)
        span.set_attribute("end", str(end) if end else None)
        try:
            query = db.query(TransactionModel)
            if status:
                query = query.filter(TransactionModel.status == status)
            if currency:
                query = query.filter(TransactionModel.currency == currency)
            if is_anomaly is not None:
                query = query.filter(TransactionModel.is_anomaly == is_anomaly)
            if start:
                from dateutil.parser import parse
                query = query.filter(TransactionModel.timestamp >= parse(start))
            if end:
                from dateutil.parser import parse
                query = query.filter(TransactionModel.timestamp <= parse(end))
            transactions = query.order_by(TransactionModel.timestamp.desc()).all()
            span.set_attribute("export.record_count", len(transactions))
            if format == "csv":
                fieldnames = [c.name for c in TransactionModel.__table__.columns]
                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for t in transactions:
                    writer.writerow({fn: getattr(t, fn) for fn in fieldnames})
                output.seek(0)
                # Hash chain and sign for manual export
                last_hash = hash_chain_csv(output.getvalue())
                signature = crypto_utils.sign_data(last_hash.encode())
                span.set_attribute("export.hash", last_hash)
                span.set_attribute("export.signature", signature.hex() if hasattr(signature, 'hex') else str(signature))
                siem.send_syslog_event(
                    event="Transactions exported as CSV",
                    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
                    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
                    extra={
                        "count": len(transactions),
                        "user": str(user.get('id') if hasattr(user, 'id') else user),
                        "trace_id": span.get_span_context().trace_id,
                        "span_id": span.get_span_context().span_id,
                        "status": status,
                        "currency": currency,
                        "is_anomaly": is_anomaly,
                        "start": str(start) if start else None,
                        "end": str(end) if end else None,
                    }
                )
                # Write ExportMetadata for CSV export
                from apps.backend.models import ExportMetadata
                from apps.backend.database import SessionLocal
                session = SessionLocal()
                try:
                    export_meta = ExportMetadata(
                        export_type="transaction",
                        file_path="transactions.csv",
                        hash=last_hash,
                        signature=signature,
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
                return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=transactions.csv"})
            else:
                siem.send_syslog_event(
    event="Transactions exported as JSON",
    host=os.getenv("SIEM_SYSLOG_HOST", "localhost"),
    port=int(os.getenv("SIEM_SYSLOG_PORT", "514")),
    extra={"count": len(transactions), "user": str(user.get('id') if hasattr(user, 'id') else user)}
)
                return [t.__dict__ for t in transactions]
        except Exception as e:
            span.record_exception(e)
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))
