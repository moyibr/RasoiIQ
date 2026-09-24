from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base

class FoodCategory(Base):
    __tablename__ = "food_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    shelf_life_hours = Column(Float)
    is_vegetarian = Column(Boolean, default=True)
    unit = Column(String(20), default="kg")
