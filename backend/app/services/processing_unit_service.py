"""
Processing Unit Metrics Service
================================
Aggregation rules (spec-compliant):
  - process_yield_pct, downtime_pct, rejection_pct → ARITHMETIC MEAN
  - downtime_hours, energy_consumed_kwh, revenue_inr, total_cost_inr,
    daily_profit_inr, waste_loss_inr, downtime_opportunity_loss_inr,
    net_good_output_kg, rejected_kg → SUM
  - Period energy_intensity → SUM(energy_consumed_kwh) / SUM(net_good_output_kg)
    (NOT average of daily intensities)

Flagging thresholds (documented):
  - process_yield_pct < 82     → flagged (below UNIDO minimum for grain/pulse lines)
  - downtime_pct > 15          → flagged (>2.4 hrs/day on 16h schedule; maintenance trigger)
  - rejection_pct > 3          → flagged (exceeds FSSAI institutional quality standard)

Date-range anchoring: For relative ranges (7d, 30d), anchor to the LATEST
AVAILABLE DATE IN THE DATASET, not the server clock.
"""

import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc

from app.models.processing_unit import ProcessingUnitLog

YIELD_FLAG_THRESHOLD = 82.0
DOWNTIME_FLAG_THRESHOLD = 15.0
REJECTION_FLAG_THRESHOLD = 3.0


def _parse_date_range(db: Session, unit_id: int, date_range: str):
    """
    Returns (start_date, end_date) as datetime.date objects.

    Supported formats:
      - "7d"  → last 7 days anchored to latest dataset date
      - "30d" → last 30 days anchored to latest dataset date
      - "YYYY-MM-DD:YYYY-MM-DD" → explicit inclusive range

    CRITICAL: relative ranges anchor to the latest available date in the DB,
    NOT the server's current clock — so prototype historical data always renders.
    """
    if date_range.endswith("d") and date_range[:-1].isdigit():
        days = int(date_range[:-1])
        # Anchor to latest date in dataset
        latest = db.query(sqlfunc.max(ProcessingUnitLog.date)).filter(
            ProcessingUnitLog.unit_id == unit_id
        ).scalar()
        if latest is None:
            today = datetime.date.today()
            return today - datetime.timedelta(days=days - 1), today
        end_date = latest
        start_date = end_date - datetime.timedelta(days=days - 1)
        return start_date, end_date
    elif ":" in date_range:
        parts = date_range.split(":")
        return datetime.date.fromisoformat(parts[0]), datetime.date.fromisoformat(parts[1])
    else:
        # Single date
        d = datetime.date.fromisoformat(date_range)
        return d, d


def get_unit_metrics(db: Session, unit_id: int, date_range: str) -> Dict[str, Any]:
    """Returns aggregated metrics + daily trend for the specified range."""
    start_date, end_date = _parse_date_range(db, unit_id, date_range)

    logs = (
        db.query(ProcessingUnitLog)
        .filter(
            ProcessingUnitLog.unit_id == unit_id,
            ProcessingUnitLog.date >= start_date,
            ProcessingUnitLog.date <= end_date,
        )
        .order_by(ProcessingUnitLog.date)
        .all()
    )

    if not logs:
        return {
            "unit_id": unit_id,
            "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "data_available": False,
            "days_with_data": 0,
            "aggregates": None,
            "trend": [],
        }

    n = len(logs)

    # SUM fields (per spec)
    total_downtime_hours = sum(l.downtime_hours for l in logs)
    total_energy_kwh = sum(l.energy_consumed_kwh for l in logs)
    total_revenue_inr = sum(l.revenue_inr for l in logs)
    total_cost_inr = sum(l.total_cost_inr for l in logs)
    total_profit_inr = sum(l.daily_profit_inr for l in logs)
    total_waste_loss_inr = sum(l.waste_loss_inr for l in logs)
    total_downtime_opp_loss_inr = sum(l.downtime_opportunity_loss_inr for l in logs)
    total_net_good_output_kg = sum(l.net_good_output_kg for l in logs)
    total_rejected_kg = sum(l.rejected_kg for l in logs)

    # MEAN fields (per spec)
    avg_yield_pct = sum(l.process_yield_pct for l in logs) / n
    avg_downtime_pct = sum(l.downtime_pct for l in logs) / n
    avg_rejection_pct = sum(l.rejection_pct for l in logs) / n

    # Period energy intensity: SUM(kwh) / SUM(good_output) — NOT avg of daily values
    period_energy_intensity = (
        total_energy_kwh / total_net_good_output_kg
        if total_net_good_output_kg > 0
        else None
    )

    # Build daily trend (raw CSV values, no recalculation)
    trend = []
    for l in logs:
        trend.append({
            "date": l.date.isoformat(),
            "day_of_week": l.day_of_week,
            "process_yield_pct": l.process_yield_pct,
            "downtime_pct": l.downtime_pct,
            "rejection_pct": l.rejection_pct,
            "energy_intensity_kwh_per_kg": l.energy_intensity_kwh_per_kg,
            "net_good_output_kg": l.net_good_output_kg,
            "daily_profit_inr": l.daily_profit_inr,
            "root_cause": l.root_cause,
        })

    return {
        "unit_id": unit_id,
        "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "data_available": True,
        "days_with_data": n,
        "aggregates": {
            # MEAN metrics
            "avg_process_yield_pct": round(avg_yield_pct, 3),
            "avg_downtime_pct": round(avg_downtime_pct, 3),
            "avg_rejection_pct": round(avg_rejection_pct, 3),
            # SUM metrics
            "total_downtime_hours": round(total_downtime_hours, 2),
            "total_energy_consumed_kwh": round(total_energy_kwh, 1),
            "total_revenue_inr": round(total_revenue_inr, 2),
            "total_cost_inr": round(total_cost_inr, 2),
            "total_profit_inr": round(total_profit_inr, 2),
            "total_waste_loss_inr": round(total_waste_loss_inr, 2),
            "total_downtime_opportunity_loss_inr": round(total_downtime_opp_loss_inr, 2),
            "total_net_good_output_kg": round(total_net_good_output_kg, 2),
            "total_rejected_kg": round(total_rejected_kg, 2),
            # Period-level derived metric (spec: SUM/SUM, not avg of daily)
            "period_energy_intensity_kwh_per_kg": (
                round(period_energy_intensity, 4) if period_energy_intensity else None
            ),
        },
        "trend": trend,
    }


def get_flagged_days(db: Session, unit_id: int) -> List[Dict[str, Any]]:
    """
    Returns all days that crossed any threshold, most recent first.
    Each entry includes: date, failed_metrics (metric, value, threshold), root_cause.
    """
    logs = (
        db.query(ProcessingUnitLog)
        .filter(ProcessingUnitLog.unit_id == unit_id)
        .order_by(ProcessingUnitLog.date.desc())
        .all()
    )

    flagged = []
    for l in logs:
        failed = []
        if l.process_yield_pct is not None and l.process_yield_pct < YIELD_FLAG_THRESHOLD:
            failed.append({
                "metric": "process_yield_pct",
                "value": l.process_yield_pct,
                "threshold": f"< {YIELD_FLAG_THRESHOLD}%",
                "direction": "below_minimum",
            })
        if l.downtime_pct is not None and l.downtime_pct > DOWNTIME_FLAG_THRESHOLD:
            failed.append({
                "metric": "downtime_pct",
                "value": l.downtime_pct,
                "threshold": f"> {DOWNTIME_FLAG_THRESHOLD}%",
                "direction": "above_maximum",
            })
        if l.rejection_pct is not None and l.rejection_pct > REJECTION_FLAG_THRESHOLD:
            failed.append({
                "metric": "rejection_pct",
                "value": l.rejection_pct,
                "threshold": f"> {REJECTION_FLAG_THRESHOLD}%",
                "direction": "above_maximum",
            })

        if failed:
            flagged.append({
                "date": l.date.isoformat(),
                "day_of_week": l.day_of_week,
                "root_cause": l.root_cause,
                "failed_metrics": failed,
                "downtime_hours": l.downtime_hours,
                "net_good_output_kg": l.net_good_output_kg,
                "daily_profit_inr": l.daily_profit_inr,
            })

    return flagged
