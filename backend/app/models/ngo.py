from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class NGO(Base):
    __tablename__ = "ngos"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    contact_name = Column(String(100))
    contact_phone = Column(String(20))
    lat = Column(Float)
    lng = Column(Float)
    food_preference = Column(String(20))
    capacity_kg = Column(Float)
    is_active = Column(Boolean, default=True)
    address = Column(String(500))
    accepted_categories = Column(String(500), default="ALL")
    operating_hours_start = Column(String(10), default="08:00")
    operating_hours_end = Column(String(10), default="22:00")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
