from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ngo import NGO
from app.models.surplus import SurplusEvent
from app.services.matching_engine import calculate_ngo_matches
from typing import List, Dict, Any

router = APIRouter()

@router.get("/surplus/{surplus_event_id}/matches")
def get_matches(surplus_event_id: int, db: Session = Depends(get_db)):
    surplus = db.query(SurplusEvent).filter(SurplusEvent.id == surplus_event_id).first()
    if not surplus:
        raise HTTPException(status_code=404, detail="Surplus event not found")
        
    ngos = db.query(NGO).filter(NGO.is_active == True).all()
    
    matches = calculate_ngo_matches(db, surplus, ngos)
    return matches
