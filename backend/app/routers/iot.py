from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.iot import IoTSensorData
from pydantic import BaseModel
import datetime
import random

router = APIRouter(prefix="/iot", tags=["IoT Monitor"])

class IoTDataPayload(BaseModel):
    unit_id: int
    temperature_c: float
    humidity_pct: float
    downtime_minutes: float
    energy_kwh: float

@router.post("/ingest")
def ingest_iot_data(payload: IoTDataPayload, db: Session = Depends(get_db)):
    new_data = IoTSensorData(
        unit_id=payload.unit_id,
        temperature_c=payload.temperature_c,
        humidity_pct=payload.humidity_pct,
        downtime_minutes=payload.downtime_minutes,
        energy_kwh=payload.energy_kwh
    )
    db.add(new_data)
    db.commit()
    
    # Rule-based alerts
    alerts = []
    if payload.temperature_c > 5.0 or payload.temperature_c < 0.0:
        alerts.append(f"Temperature out of safe range (0-5°C): {payload.temperature_c:.1f}°C")
    if payload.humidity_pct > 85.0:
        alerts.append(f"High humidity detected: {payload.humidity_pct:.1f}%")
    if payload.downtime_minutes > 15.0:
        alerts.append(f"High downtime: {payload.downtime_minutes:.0f} mins")
    if payload.energy_kwh > 50.0:
        alerts.append(f"Energy spike detected: {payload.energy_kwh:.1f} kWh")

    return {"status": "success", "alerts": alerts}

@router.get("/data")
def get_iot_data(unit_id: int = 1, limit: int = 20, db: Session = Depends(get_db)):
    data = db.query(IoTSensorData).filter(IoTSensorData.unit_id == unit_id)\
             .order_by(IoTSensorData.timestamp.desc()).limit(limit).all()
    
    # Reverse so oldest is first for charts
    return [
        {
            "id": d.id,
            "timestamp": d.timestamp.isoformat(),
            "temperature_c": d.temperature_c,
            "humidity_pct": d.humidity_pct,
            "downtime_minutes": d.downtime_minutes,
            "energy_kwh": d.energy_kwh
        } for d in reversed(data)
    ]

@router.post("/simulate")
def simulate_iot_data(unit_id: int = 1, db: Session = Depends(get_db)):
    # Generate realistic dummy data
    is_anomaly = random.random() < 0.2
    
    payload = IoTDataPayload(
        unit_id=unit_id,
        temperature_c=random.uniform(1.0, 4.0) if not is_anomaly else random.uniform(5.5, 8.0),
        humidity_pct=random.uniform(50.0, 75.0) if not is_anomaly else random.uniform(86.0, 95.0),
        downtime_minutes=0.0 if not is_anomaly else random.uniform(16.0, 45.0),
        energy_kwh=random.uniform(10.0, 30.0) if not is_anomaly else random.uniform(55.0, 100.0)
    )
    
    return ingest_iot_data(payload, db)
