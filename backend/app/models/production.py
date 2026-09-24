from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class ProductionLog(Base):
    __tablename__ = "production_logs"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"))
    category_id = Column(Integer, ForeignKey("food_categories.id"))
    date = Column(Date, nullable=False)
    planned_kg = Column(Float)
    actual_kg = Column(Float)
    batch_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FoodConsumptionLog(Base):
    __tablename__ = "food_consumption_logs"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"))
    category_id = Column(Integer, ForeignKey("food_categories.id"))
    date = Column(Date, nullable=False)
    consumed_qty = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

