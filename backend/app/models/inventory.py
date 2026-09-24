from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id = Column(Integer, primary_key=True, index=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"))
    category_id = Column(Integer, ForeignKey("food_categories.id"))
    date = Column(Date, nullable=False)
    usable_inventory = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
