from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..services.basel_compliance_service import BaselComplianceService
from ..database import get_db
from ..security import require_role
from datetime import datetime
import csv
from fastapi.responses import StreamingResponse
from io import StringIO

router = APIRouter(prefix="/compliance/lcr", tags=["compliance", "lcr", "export"])
basel_service = BaselComplianceService()

@router.get("/export")
async def export_lcr_snapshots(
    lookback_days: Optional[int] = 30,
    start: Optional[str] = None,
    end: Optional[str] = None,
    format: str = "csv",
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "compliance"]))
):
    """
    Export Basel III LCR snapshots as CSV or JSON, with date filtering.
    """
    try:
        # For MVP, get LCR for each day in range
        from dateutil.parser import parse
        from datetime import timedelta
        if start and end:
            start_dt = parse(start)
            end_dt = parse(end)
        else:
            end_dt = datetime.utcnow()
            start_dt = end_dt - timedelta(days=lookback_days or 30)
        snapshots = []
        for i in range((end_dt - start_dt).days + 1):
            day = start_dt + timedelta(days=i)
            lcr_data = basel_service.calculate_lcr(db, lookback_days=1, ref_date=day)
            lcr_data["date"] = day.strftime("%Y-%m-%d")
            snapshots.append(lcr_data)
        if format == "csv":
            if not snapshots:
                return StreamingResponse(StringIO(""), media_type="text/csv")
            fieldnames = list(snapshots[0].keys())
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for snap in snapshots:
                writer.writerow(snap)
            output.seek(0)
            return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=lcr_snapshots.csv"})
        else:
            return snapshots
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
