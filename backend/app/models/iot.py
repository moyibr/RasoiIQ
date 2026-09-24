from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base

class IoTSensorData(Base):
    __tablename__ = "iot_sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    temperature_c = Column(Float)
    humidity_pct = Column(Float)
    downtime_minutes = Column(Float)
    energy_kwh = Column(Float)
