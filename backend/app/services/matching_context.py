import csv
import os
from sqlalchemy.orm import Session
from app.models.ngo import NGO

# STATED ASSUMPTION: Routing multipliers and speeds estimate realistic Bengaluru traffic without requiring an external maps API.
SCORING_WEIGHTS = {
    "distance": 0.40, 
    "capacity": 0.25, 
    "time": 0.20, 
    "food_type": 0.15
}

ROAD_DISTANCE_MULTIPLIER = 1.5
URBAN_SPEED_KMH = 20.0
SAFETY_BUFFER_HOURS = 0.5

def seed_ngos(db: Session):
    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "seed_ngo_recipients.csv")
    if not os.path.exists(csv_path):
        return
        
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing = db.query(NGO).filter(NGO.name == row["name"]).first()
            if not existing:
                ngo = NGO(
                    name=row["name"],
                    contact_name=row["contact_name"],
                    contact_phone=row["contact_phone"],
                    lat=float(row["lat"]),
                    lng=float(row["lng"]),
                    food_preference=row["food_preference"],
                    capacity_kg=float(row["capacity_kg"]),
                    address=row["address"],
                    accepted_categories=row["accepted_categories"],
                    operating_hours_start=row["operating_hours_start"],
                    operating_hours_end=row["operating_hours_end"]
                )
                db.add(ngo)
        db.commit()
