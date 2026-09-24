from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Waypoint(BaseModel):
    lat: float
    lng: float
    label: str
    type: str

class RouteRequest(BaseModel):
    kitchen_id: int
    delivery_ids: List[int]

class RouteResponse(BaseModel):
    delivery_id: Optional[int] = None
    waypoints: list[Waypoint]
    total_distance_km: float
    eta_minutes: int
    route_polyline: list[list[float]] = []
    route_geometry: Optional[Dict[str, Any]] = None
    routing_method_used: str = "vrptw"
