from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.surplus import SurplusEventResponse
from app.models.surplus import SurplusEvent
from app.models.kitchen import Kitchen
from app.models.food_category import FoodCategory
from app.services.shelf_life_context import calculate_urgency
import datetime

router = APIRouter(prefix="/surplus", tags=["Surplus"])

@router.get("", response_model=list[SurplusEventResponse])
def get_surplus(kitchen_id: int = None, status: str = "", db: Session = Depends(get_db)):
    query = db.query(SurplusEvent, Kitchen, FoodCategory).join(
        Kitchen, SurplusEvent.kitchen_id == Kitchen.id
    ).join(
        FoodCategory, SurplusEvent.category_id == FoodCategory.id
    )
    
    if kitchen_id:
        query = query.filter(SurplusEvent.kitchen_id == kitchen_id)
        
    events = query.all()
    
    responses = []
    for se, kit, cat in events:
        if status and se.status.lower() != status.lower():
            continue
            
        remaining_hours, urgency = calculate_urgency(cat.name, se.batch_created_at)
        
        responses.append({
            "id": se.id,
            "kitchen_id": se.kitchen_id,
            "kitchen_name": kit.name,
            "category": cat.name,
            "is_vegetarian": cat.is_vegetarian,
            "quantity_kg": se.quantity_kg,
            "detected_at": se.detected_at.isoformat() if se.detected_at else "",
            "expiry_at": se.expiry_at.isoformat() if se.expiry_at else "",
            "rescue_window_hours": remaining_hours,
            "urgency_level": urgency,
            "status": se.status
        })
        
    # Sort by remaining_window_hours ASC, pushing EXPIRED to the bottom
    def sort_key(item):
        if item["urgency_level"] == "EXPIRED":
            return (1, item["rescue_window_hours"])
        return (0, item["rescue_window_hours"])
        
    responses.sort(key=sort_key)
    
    return [SurplusEventResponse(**r) for r in responses]

from pydantic import BaseModel
from typing import Optional
from app.services.shelf_life_context import SHELF_LIFE_HOURS
from fastapi import HTTPException

class ManualSurplusRequest(BaseModel):
    kitchen_id: int
    category_name: str
    quantity_kg: float
    hours_remaining_override: Optional[float] = None

@router.post("", response_model=SurplusEventResponse)
def create_manual_surplus(req: ManualSurplusRequest, db: Session = Depends(get_db)):
    kit = db.query(Kitchen).filter(Kitchen.id == req.kitchen_id).first()
    if not kit:
        raise HTTPException(status_code=404, detail="Kitchen not found")
        
    cat = db.query(FoodCategory).filter(FoodCategory.name == req.category_name).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
        
    now = datetime.datetime.now(datetime.timezone.utc)
    
    if req.hours_remaining_override is not None:
        shelf_life = SHELF_LIFE_HOURS.get(cat.name, 24.0)
        hours_elapsed = shelf_life - req.hours_remaining_override
        batch_created_at = now - datetime.timedelta(hours=hours_elapsed)
    else:
        batch_created_at = now

    new_event = SurplusEvent(
        kitchen_id=kit.id,
        category_id=cat.id,
        quantity_kg=req.quantity_kg,
        status="ACTIVE",
        detected_at=now,
        batch_created_at=batch_created_at,
        expiry_at=batch_created_at + datetime.timedelta(hours=SHELF_LIFE_HOURS.get(cat.name, 24.0))
    )
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    remaining_hours, urgency = calculate_urgency(cat.name, new_event.batch_created_at)
    
    return SurplusEventResponse(
        id=new_event.id,
        kitchen_id=kit.id,
        kitchen_name=kit.name,
        category=cat.name,
        is_vegetarian=cat.is_vegetarian,
        quantity_kg=new_event.quantity_kg,
        detected_at=new_event.detected_at.isoformat(),
        expiry_at=new_event.expiry_at.isoformat() if new_event.expiry_at else "",
        rescue_window_hours=remaining_hours,
        urgency_level=urgency,
        status=new_event.status
    )
