from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RouteResponse(BaseModel):
    id: int
    name: str
    agent_id: int
    status: str
    total_distance: Optional[float] = None
    total_risk_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RouteGenerationRequest(BaseModel):
    agent_id: Optional[int] = None
    max_deliveries: int = 20


class RouteStopInfo(BaseModel):
    stop_order: int
    delivery_id: int
    delivery_order_id: str
    estimated_arrival: Optional[str] = None


class RouteGenerationResponse(BaseModel):
    route_id: int
    route_name: str
    agent_id: int
    total_distance: float
    total_risk_score: float
    stops: list[RouteStopInfo]
