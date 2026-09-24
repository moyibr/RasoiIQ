from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.processing_unit_service import get_unit_metrics, get_flagged_days

router = APIRouter(prefix="/processing-unit", tags=["Processing Unit"])


@router.get("/{unit_id}/metrics")
def metrics(
    unit_id: int,
    date_range: str = Query("30d", description="Supports: 7d, 30d, or YYYY-MM-DD:YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    Returns aggregated metrics and daily trend for a processing unit.

    Date range anchoring: relative ranges (7d, 30d) anchor to the latest
    available date in the dataset, NOT the server clock.
    """
    result = get_unit_metrics(db, unit_id, date_range)
    if not result.get("data_available") and result.get("days_with_data", 0) == 0:
        # Check if unit exists at all
        from app.models.processing_unit import ProcessingUnit
        unit = db.query(ProcessingUnit).filter_by(id=unit_id).first()
        if not unit:
            raise HTTPException(status_code=404, detail=f"Processing unit {unit_id} not found.")
    return result


@router.get("/{unit_id}/flagged-days")
def flagged_days(
    unit_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns all days that crossed any operational threshold.

    Thresholds:
      - process_yield_pct < 82%   (UNIDO minimum for grain/pulse lines)
      - downtime_pct > 15%        (>2.4 hrs/day on 16h schedule)
      - rejection_pct > 3%        (FSSAI institutional quality standard)

    Response includes: date, failed_metrics (metric, value, threshold), root_cause.
    """
    from app.models.processing_unit import ProcessingUnit
    unit = db.query(ProcessingUnit).filter_by(id=unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail=f"Processing unit {unit_id} not found.")

    flagged = get_flagged_days(db, unit_id)
    return {
        "unit_id": unit_id,
        "total_flagged_days": len(flagged),
        "thresholds": {
            "process_yield_pct": "< 82% (UNIDO grain/pulse minimum)",
            "downtime_pct": "> 15% (>2.4 hrs/day on 16h schedule)",
            "rejection_pct": "> 3% (FSSAI institutional quality standard)",
        },
        "flagged_days": flagged,
    }
