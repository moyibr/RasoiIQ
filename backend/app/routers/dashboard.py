from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.dashboard import DashboardSummaryResponse, DailyStat
from app.models.production import FoodConsumptionLog, ProductionLog
from app.models.surplus import SurplusEvent
import datetime

router = APIRouter()

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    today = datetime.datetime.now().date()
    
    from app.services.shelf_life_context import calculate_urgency
    from app.models.food_category import FoodCategory

    # Active surplus
    active_surplus_events = db.query(SurplusEvent, FoodCategory).join(
        FoodCategory, SurplusEvent.category_id == FoodCategory.id
    ).filter(SurplusEvent.status == 'ACTIVE').all()
    
    active_surplus = 0
    for se, cat in active_surplus_events:
        rem, urgency = calculate_urgency(cat.name, se.batch_created_at)
        if urgency != "EXPIRED":
            active_surplus += 1
            
    # Let's compute kg_rescued, etc. Just sum for today.
    rescued_today = db.query(SurplusEvent).filter(SurplusEvent.status.in_(['DELIVERED', 'MATCHED']), SurplusEvent.detected_at >= today).all()
    kg_rescued_today = sum(s.quantity_kg for s in rescued_today) if rescued_today else 0.0
    
    kg_wasted_today = sum(s.quantity_kg for s in db.query(SurplusEvent).filter(SurplusEvent.status == 'EXPIRED', SurplusEvent.detected_at >= today).all())
    
    trend = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        
        rescued = db.query(SurplusEvent).filter(SurplusEvent.status.in_(['DELIVERED', 'MATCHED']), SurplusEvent.detected_at >= d, SurplusEvent.detected_at < d + datetime.timedelta(days=1)).all()
        kg_rescued = sum(s.quantity_kg for s in rescued) if rescued else 0.0
        
        wasted = db.query(SurplusEvent).filter(SurplusEvent.status == 'EXPIRED', SurplusEvent.detected_at >= d, SurplusEvent.detected_at < d + datetime.timedelta(days=1)).all()
        kg_wasted = sum(s.quantity_kg for s in wasted) if wasted else 0.0
        
        trend.append(DailyStat(
            date=d.isoformat(),
            kg_rescued=kg_rescued,
            kg_wasted=kg_wasted,
            meals_served=int(kg_rescued / 0.35),
            co2_saved_kg=kg_rescued * 2.5
        ))
        
    from sqlalchemy import extract
    from app.models.delivery import Delivery

    ngos_served_this_month = db.query(Delivery.ngo_id).filter(
        Delivery.status == 'DELIVERED',
        extract('month', Delivery.delivered_at) == today.month,
        extract('year', Delivery.delivered_at) == today.year
    ).distinct().count()

    # Derived from Anumaan's MAE (~48.8) and baseline (~295)
    baseline_mae = 48.8
    baseline_demand = 295.0
    forecast_accuracy_pct = round(100.0 - ((baseline_mae / baseline_demand) * 100.0), 1)

    return DashboardSummaryResponse(
        kg_rescued_today=round(kg_rescued_today, 2),
        kg_wasted_today=round(kg_wasted_today, 2),
        active_surplus_count=active_surplus,
        ngos_served_this_month=ngos_served_this_month,
        forecast_accuracy_pct=forecast_accuracy_pct,
        co2_saved_today_kg=round(kg_rescued_today * 2.5, 2),
        cost_saved_today_inr=round(kg_rescued_today * 50.0, 2),
        weekly_trend=trend
    )
