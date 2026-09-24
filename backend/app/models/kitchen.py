from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Kitchen(Base):
    __tablename__ = "kitchens"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    address = Column(String(500))
    lat = Column(Float)
    lng = Column(Float)
    capacity_meals = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
