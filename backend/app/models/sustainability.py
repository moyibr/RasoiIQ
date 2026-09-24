from sqlalchemy import Column, Integer, Float, Date, DateTime
from sqlalchemy.sql import func
from app.database import Base

class SustainabilityMetric(Base):
    __tablename__ = "sustainability_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True)
    kg_rescued = Column(Float, default=0)
    kg_wasted = Column(Float, default=0)
    co2_saved_kg = Column(Float, default=0)
    meals_served = Column(Integer, default=0)
    cost_saved_inr = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
