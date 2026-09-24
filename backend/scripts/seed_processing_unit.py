"""
Seed script: ingests processing_unit_dataset_v3_verified.csv into the database.

CRITICAL: All numeric values are inserted VERBATIM from the CSV.
No recalculation, normalization, rounding, or overwriting of pre-computed
metrics (e.g., process_yield_pct, daily_profit_inr). The CSV is the source
of truth. After seeding, DB row count MUST match CSV row count exactly.

Run with:   python -m scripts.seed_processing_unit
(from the backend/ directory)
"""

import csv
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.database import Base
from app.models.processing_unit import ProcessingUnit, ProcessingUnitLog

UNIT_ID = 1
CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "processing_unit_dataset_v3_verified.csv"
)


def seed_processing_unit(db=None):
    Base.metadata.create_all(bind=engine)
    own_db = db is None
    if own_db:
        db = SessionLocal()

    try:
        # Idempotency: skip if already seeded
        existing_count = db.query(ProcessingUnitLog).filter_by(unit_id=UNIT_ID).count()
        if existing_count > 0:
            print(f"[OK] Processing unit logs already seeded ({existing_count} rows). Skipping.")
            return

        # Ensure unit record exists
        unit = db.query(ProcessingUnit).filter_by(id=UNIT_ID).first()
        if not unit:
            unit = ProcessingUnit(
                id=UNIT_ID,
                name="Central Processing Unit — Maize/Pulse Line",
                location="BMTC Central Processing Facility, Peenya Industrial Area, Bengaluru",
                description=(
                    "STATED SYNTHETIC DATASET — "
                    "Operational data generated for system demonstration and validation. "
                    "Sourced from processing_unit_dataset_v3_verified.csv (180 rows, 2026-03-24 to 2026-09-19). "
                    "Source benchmarks: FSSAI Inspection Data (2022), UNIDO Agro-processing Report (2020), "
                    "BEE Energy Performance Report (2023), NCDEX spot prices Sept 2026."
                ),
            )
            db.add(unit)
            db.commit()

        # Read CSV
        if not os.path.exists(CSV_PATH):
            print(f"ERROR: CSV not found at {CSV_PATH}")
            return

        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        csv_count = len(rows)
        logs = []
        for row in rows:
            log = ProcessingUnitLog(
                unit_id=UNIT_ID,
                date=datetime.date.fromisoformat(row["date"]),
                day_of_week=row["day_of_week"],
                root_cause=row["root_cause"],
                scheduled_hours=float(row["scheduled_hours"]),
                downtime_hours=float(row["downtime_hours"]),
                runtime_hours=float(row["runtime_hours"]),
                throughput_kg_per_hr=float(row["throughput_kg_per_hr"]),
                planned_input_kg=float(row["planned_input_kg"]),
                actual_input_kg=float(row["actual_input_kg"]),
                expected_output_kg=float(row["expected_output_kg"]),
                net_good_output_kg=float(row["net_good_output_kg"]),
                rejected_kg=float(row["rejected_kg"]),
                # Pre-computed metrics — stored VERBATIM, no recalculation
                process_yield_pct=float(row["process_yield_pct"]),
                target_achievement_pct=float(row["target_achievement_pct"]),
                downtime_pct=float(row["downtime_pct"]),
                rejection_pct=float(row["rejection_pct"]),
                energy_consumed_kwh=float(row["energy_consumed_kwh"]),
                energy_intensity_kwh_per_kg=float(row["energy_intensity_kwh_per_kg"]),
                revenue_inr=float(row["revenue_inr"]),
                total_cost_inr=float(row["total_cost_inr"]),
                daily_profit_inr=float(row["daily_profit_inr"]),
                waste_loss_inr=float(row["waste_loss_inr"]),
                downtime_opportunity_loss_inr=float(row["downtime_opportunity_loss_inr"]),
            )
            logs.append(log)

        db.add_all(logs)
        db.commit()

        # Verify: DB count must match CSV count exactly
        db_count = db.query(ProcessingUnitLog).filter_by(unit_id=UNIT_ID).count()
        if db_count != csv_count:
            print(f"ERROR: DB count {db_count} != CSV count {csv_count}. Integrity check FAILED.")
            return

        print(f"[OK] Seeded {db_count} processing unit log rows.")
        print(f"[OK] Integrity check PASSED: DB count ({db_count}) == CSV count ({csv_count}).")

    finally:
        if own_db:
            db.close()


if __name__ == "__main__":
    seed_processing_unit()
