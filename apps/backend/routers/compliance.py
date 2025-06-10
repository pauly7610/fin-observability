from fastapi import APIRouter, Depends, HTTPException
from ..security import require_role
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas import ComplianceLog, ComplianceLogCreate
from ..models import ComplianceLog as ComplianceLogModel
import logging
from datetime import datetime
import os
from apps.backend import siem
import hashlib

router = APIRouter(prefix="/compliance", tags=["compliance"])
logger = logging.getLogger(__name__)

@router.post("/logs", response_model=ComplianceLog)
async def create_compliance_log(log: dict, db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance"]))) -> ComplianceLog:
    try:
        new_log = ComplianceLogModel(**log)
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        from apps.backend import siem
        siem.send_syslog_event(f"Compliance log created: id={new_log.id}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
        return new_log
    except Exception as e:
        logger.error(f"Error creating compliance log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def create_compliance_log(
    log: ComplianceLogCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
):
    """
    Create a new compliance log entry.
    """
    try:
        new_log = ComplianceLogModel(**log.dict())
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        siem.send_syslog_event(f"Compliance log created: id={new_log.id}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
        return new_log
    except Exception as e:
        logger.error(f"Error creating compliance log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs", response_model=List[ComplianceLog])
async def get_compliance_logs(
    event_type: str = None,
    severity: str = None,
    is_resolved: bool = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get compliance logs with optional filtering.
    """
    try:
        query = db.query(ComplianceLogModel)
        
        if event_type:
            query = query.filter(ComplianceLogModel.event_type == event_type)
        if severity:
            query = query.filter(ComplianceLogModel.severity == severity)
        if is_resolved is not None:
            query = query.filter(ComplianceLogModel.is_resolved == is_resolved)
            
        logs = query.order_by(ComplianceLogModel.timestamp.desc())\
            .limit(limit)\
            .all()
        return logs
    except Exception as e:
        logger.error(f"Error fetching compliance logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

from ..security import require_role

@router.get("/export")
async def export_compliance_logs(
    format: str = "json",
    event_type: str = None,
    severity: str = None,
    is_resolved: bool = None,
    start: str = None,
    end: str = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
):
    """
    Export compliance logs as CSV or JSON, with RBAC and filtering.
    """
    try:
        query = db.query(ComplianceLogModel)
        if event_type:
            query = query.filter(ComplianceLogModel.event_type == event_type)
        if severity:
            query = query.filter(ComplianceLogModel.severity == severity)
        if is_resolved is not None:
            query = query.filter(ComplianceLogModel.is_resolved == is_resolved)
        if start:
            from dateutil.parser import parse
            query = query.filter(ComplianceLogModel.timestamp >= parse(start))
        if end:
            from dateutil.parser import parse
            query = query.filter(ComplianceLogModel.timestamp <= parse(end))
        logs = query.order_by(ComplianceLogModel.timestamp.desc()).all()
        if format == "csv":
            import csv
            from fastapi.responses import StreamingResponse
            from io import StringIO
            fieldnames = [c.name for c in ComplianceLogModel.__table__.columns]
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for log in logs:
                writer.writerow({fn: getattr(log, fn) for fn in fieldnames})
            output.seek(0)
            # Digitally sign hash chain for manual exports
            hash_chain = hashlib.sha256(output.read().encode()).hexdigest()
            siem.send_syslog_event(f"Compliance log export: hash={hash_chain}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
            siem.send_syslog_event(f"Compliance log export: hash={hash_chain}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
            return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=compliance_logs.csv"})
        else:
            # Default to JSON
            siem.send_syslog_event(f"Compliance log export: count={len(logs)}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
            siem.send_syslog_event(f"Compliance log export: count={len(logs)}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
            return [log.__dict__ for log in logs]
    except Exception as e:
        logger.error(f"Error exporting compliance logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/logs/{log_id}/resolve")
async def resolve_compliance_log(log_id: int, db: Session = Depends(get_db), user=Depends(require_role(["admin", "compliance"]))) -> ComplianceLog:
    try:
        log = db.query(ComplianceLogModel).filter(ComplianceLogModel.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Log not found")
        log.is_resolved = True
        db.commit()
        from apps.backend import siem
        siem.send_syslog_event(f"Compliance log resolved: id={log_id}", host=os.getenv("SIEM_SYSLOG_HOST", "localhost"), port=int(os.getenv("SIEM_SYSLOG_PORT", "514")))
        return log
    except Exception as e:
        logger.error(f"Error resolving compliance log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def resolve_compliance_log(
    log_id: int,
    resolution_notes: str,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
):
    """
    Mark a compliance log as resolved with resolution notes.
    """
    try:
        log = db.query(ComplianceLogModel).filter(ComplianceLogModel.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Compliance log not found")
            
        log.is_resolved = True
        log.resolution_notes = resolution_notes
        db.commit()
        return {"status": "success", "message": "Compliance log resolved"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving compliance log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/stats")
async def get_compliance_stats(
    db: Session = Depends(get_db)
):
    """
    Get compliance statistics.
    """
    try:
        total_logs = db.query(ComplianceLogModel).count()
        resolved_logs = db.query(ComplianceLogModel)\
            .filter(ComplianceLogModel.is_resolved == True)\
            .count()
            
        severity_counts = db.query(
            ComplianceLogModel.severity,
            db.func.count(ComplianceLogModel.id)
        ).group_by(ComplianceLogModel.severity).all()
        
        return {
            "total_logs": total_logs,
            "resolved_logs": resolved_logs,
            "unresolved_logs": total_logs - resolved_logs,
            "severity_distribution": dict(severity_counts)
        }
    except Exception as e:
        logger.error(f"Error fetching compliance stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 