from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AgentResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    name: str
    phone: Optional[str] = None
    vehicle_type: Optional[str] = None
    warehouse_id: Optional[int] = None
    current_lat: Optional[float] = None
    current_lon: Optional[float] = None
    current_load: int
    max_load: int
    success_rate: float
    is_available: bool
    status: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    vehicle_type: Optional[str] = None
    warehouse_id: Optional[int] = None
    current_lat: Optional[float] = None
    current_lon: Optional[float] = None
    current_load: Optional[int] = None
    max_load: Optional[int] = None
    is_available: Optional[bool] = None


class AgentAssignmentRequest(BaseModel):
    delivery_ids: list[int]
    agent_id: int


class AgentAssignmentResponse(BaseModel):
    agent_id: int
    assigned_count: int
    deliveries: list[int]
