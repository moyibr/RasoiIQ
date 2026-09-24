import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.sustainability_aggregator import aggregate_sustainability_metrics
from app.services.llm_service import generate_narrative

router = APIRouter(prefix="/reports", tags=["Reports"])


def _parse_date_range(date_range: str):
    """Parses date_range string into (start, end) as datetime.date objects."""
    if date_range.endswith("d") and date_range[:-1].isdigit():
        days = int(date_range[:-1])
        end = datetime.date.today()
        start = end - datetime.timedelta(days=days - 1)
        return start, end
    elif ":" in date_range:
        parts = date_range.split(":")
        return datetime.date.fromisoformat(parts[0]), datetime.date.fromisoformat(parts[1])
    else:
        raise ValueError(f"Unsupported date_range format: {date_range}. Use 7d, 30d, or YYYY-MM-DD:YYYY-MM-DD")


@router.get("/sustainability")
def sustainability_report(
    date_range: str = Query(
        "30d",
        description="Supports: 7d, 30d, or YYYY-MM-DD:YYYY-MM-DD",
    ),
    db: Session = Depends(get_db),
):
    """
    Returns the sustainability report for the specified period.

    Response structure:
      - provenance: period, sources, assumptions, synthetic flags
      - metrics: aggregated DB data (the ONLY input to the LLM)
      - narrative: LLM-generated text (narrates metrics, invents nothing)
      - llm_error: null on success; error string if LLM call failed/unconfigured

    The LLM receives ONLY the metrics dict — it has zero DB access.
    """
    try:
        start_date, end_date = _parse_date_range(date_range)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Aggregate from DB — LLM gets only this dict
    metrics = aggregate_sustainability_metrics(db, start_date, end_date)

    # Call LLM with aggregated metrics only (no raw DB data passed)
    narrative, narrative_source, llm_error = generate_narrative(metrics)

    return {
        "provenance": {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "sources": [
                "surplus_events table (SQLite, seed data)",
                "processing_unit_logs table (processing_unit_dataset_v3_verified.csv)",
            ],
            "documented_assumptions": {
                "co2e_factor": "2.5 kg CO2e/kg — FAO (2013) Food Wastage Footprint",
                "meal_weight_kg": "0.4 kg/meal — FSSAI institutional portion guidance (stated assumption)",
                "forecast_mae": "48.8 customers/day — Anumaan model test-set evaluation (Phase 2a)",
            },
            "is_synthetic_data": True,
            "synthetic_note": (
                "All kitchen surplus data is synthetic, generated for system demonstration. "
                "Processing unit data sourced from processing_unit_dataset_v3_verified.csv."
            ),
        },
        "metrics": metrics,
        "narrative": narrative,
        "narrative_source": narrative_source,
        "llm_error": llm_error,
    }
