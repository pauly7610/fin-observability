from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from apps.backend.models import ExportMetadata as ExportMetadataModel
from apps.backend.database import get_db
from apps.backend.schemas import ExportMetadata, ExportMetadataCreate
from apps.backend.security import require_role
from datetime import datetime

router = APIRouter(prefix="/exports", tags=["exports", "reporting"])


@router.get("/", response_model=List[ExportMetadata])
def list_exports(
    export_type: Optional[str] = None,
    delivery_status: Optional[str] = None,
    verification_status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"])),
):
    query = db.query(ExportMetadataModel)
    if export_type:
        query = query.filter(ExportMetadataModel.export_type == export_type)
    if delivery_status:
        query = query.filter(ExportMetadataModel.delivery_status == delivery_status)
    if verification_status:
        query = query.filter(
            ExportMetadataModel.verification_status == verification_status
        )
    if start_date:
        query = query.filter(ExportMetadataModel.created_at >= start_date)
    if end_date:
        query = query.filter(ExportMetadataModel.created_at <= end_date)
    return query.order_by(ExportMetadataModel.created_at.desc()).all()


@router.get("/{export_id}", response_model=ExportMetadata)
def get_export(
    export_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"])),
) -> ExportMetadata:
    export = (
        db.query(ExportMetadataModel)
        .filter(ExportMetadataModel.id == export_id)
        .first()
    )
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    return export


@router.post("/", response_model=ExportMetadata)
def create_export_metadata(
    export: ExportMetadataCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"])),
) -> ExportMetadata:
    new_export = ExportMetadataModel(**export.dict(), created_at=datetime.utcnow())
    db.add(new_export)
    db.commit()
    db.refresh(new_export)
    return new_export


# WORM Policy: ExportMetadata is Write Once, Read Many (WORM) for compliance. Only delivery_status, verification_status, delivered_at, and verified_at can ever be updated. All other fields are immutable after creation.


@router.patch("/{export_id}", response_model=ExportMetadata)
def update_export_metadata(
    export_id: int,
    delivery_status: Optional[str] = None,
    verification_status: Optional[str] = None,
    delivered_at: Optional[datetime] = None,
    verified_at: Optional[datetime] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"])),
) -> ExportMetadata:
    """
    Update only status or verification fields for ExportMetadata. All other fields are immutable (WORM compliance).
    """
    export = (
        db.query(ExportMetadataModel)
        .filter(ExportMetadataModel.id == export_id)
        .first()
    )
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    # Only allow updates to status/verification fields
    if delivery_status is not None:
        export.delivery_status = delivery_status
    if verification_status is not None:
        export.verification_status = verification_status
    if delivered_at is not None:
        export.delivered_at = delivered_at
    if verified_at is not None:
        export.verified_at = verified_at
    db.commit()
    db.refresh(export)
    return export


@router.post("/batch_verify")
def batch_verify_exports(
    export_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"])),
):
    from apps.backend.verify_export import verify_hash_chain, verify_signature

    exports = db.query(ExportMetadataModel)
    if export_type:
        exports = exports.filter(ExportMetadataModel.export_type == export_type)
    if start_date:
        exports = exports.filter(ExportMetadataModel.created_at >= start_date)
    if end_date:
        exports = exports.filter(ExportMetadataModel.created_at <= end_date)
    exports = exports.all()
    results = []
    for export in exports:
        if not export.file_path:
            continue
        hash_ok = verify_hash_chain(export.file_path)
        sig_ok = verify_signature(export.file_path)
        export.verification_status = (
            "verified"
            if hash_ok and sig_ok
            else "tampered" if not hash_ok else "failed"
        )
        export.verified_at = datetime.utcnow()
        db.commit()
        results.append(
            {
                "id": export.id,
                "file": export.file_path,
                "hash_chain": hash_ok,
                "signature": sig_ok,
                "status": export.verification_status,
            }
        )
    return {"results": results}


@router.post("/{export_id}/redeliver", response_model=ExportMetadata)
def redeliver_export(
    export_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"])),
) -> ExportMetadata:
    export = (
        db.query(ExportMetadataModel)
        .filter(ExportMetadataModel.id == export_id)
        .first()
    )
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    # Example: Try to resend via email and/or S3 (pseudo-logic)
    email_status, s3_status = None, None
    if (
        export.delivery_method
        and "email" in export.delivery_method
        and export.file_path
    ):
        from apps.backend.scheduled_exports import send_export_email, EXPORT_EMAIL_TO

        email_status = send_export_email(
            subject=f"Re-delivery: {export.export_type} Export",
            body=f"Re-delivered export file {export.file_path}",
            attachment_path=export.file_path,
        )
    if export.delivery_method and "s3" in export.delivery_method and export.file_path:
        from apps.backend.scheduled_exports import upload_export_s3

        s3_status = upload_export_s3(export.file_path)
    export.delivery_status = (
        "delivered"
        if email_status and s3_status
        else "partial" if email_status or s3_status else "failed"
    )
    export.delivered_at = datetime.utcnow()
    db.commit()
    db.refresh(export)
    return export
