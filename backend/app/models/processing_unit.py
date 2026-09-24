from sqlalchemy import Column, Integer, String, Float, Date, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class ProcessingUnit(Base):
    """Single stable processing unit record."""
    __tablename__ = "processing_units"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    location = Column(String(500))
    description = Column(String(1000))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProcessingUnitLog(Base):
    """
    Daily operational log for a processing unit.

    STATED SYNTHETIC DATASET: Sourced from processing_unit_dataset_v3_verified.csv
    (180 rows, 2026-03-24 to 2026-09-19). All metric values are preserved exactly
    as-is from the verified CSV — no recalculation, normalization, or rounding applied
    at ingestion time.

    Column definitions mirror the CSV schema exactly:
      process_yield_pct     = (net_good_output_kg / expected_output_kg) * 100
      downtime_pct          = (downtime_hours / scheduled_hours) * 100
      rejection_pct         = (rejected_kg / (net_good_output_kg + rejected_kg)) * 100
      energy_intensity_kwh_per_kg = energy_consumed_kwh / net_good_output_kg
      (All pre-computed in the source CSV; stored verbatim.)
    """
    __tablename__ = "processing_unit_logs"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, nullable=False, index=True)  # FK to processing_units.id
    date = Column(Date, nullable=False, index=True)
    day_of_week = Column(String(20))
    root_cause = Column(String(200))

    # Time fields
    scheduled_hours = Column(Float, nullable=False)
    downtime_hours = Column(Float, nullable=False)
    runtime_hours = Column(Float, nullable=False)

    # Throughput
    throughput_kg_per_hr = Column(Float)
    planned_input_kg = Column(Float)
    actual_input_kg = Column(Float)
    expected_output_kg = Column(Float)
    net_good_output_kg = Column(Float)
    rejected_kg = Column(Float)

    # Pre-computed metrics (preserved verbatim from CSV, NOT recalculated)
    process_yield_pct = Column(Float)
    target_achievement_pct = Column(Float)
    downtime_pct = Column(Float)
    rejection_pct = Column(Float)

    # Energy
    energy_consumed_kwh = Column(Float)
    energy_intensity_kwh_per_kg = Column(Float)

    # Financial
    revenue_inr = Column(Float)
    total_cost_inr = Column(Float)
    daily_profit_inr = Column(Float)
    waste_loss_inr = Column(Float)
    downtime_opportunity_loss_inr = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("unit_id", "date", name="uq_pu_log_unit_date"),
    )
