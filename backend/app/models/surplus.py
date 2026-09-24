from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class SurplusEvent(Base):
    __tablename__ = "surplus_events"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"))
    category_id = Column(Integer, ForeignKey("food_categories.id"))
    quantity_kg = Column(Float)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    batch_created_at = Column(DateTime(timezone=True))
    expiry_at = Column(DateTime(timezone=True))
    urgency_level = Column(String(10))
    status = Column(String(20))
    notes = Column(String(500))
