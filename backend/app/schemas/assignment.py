from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SessionDeliveryInfo(BaseModel):
    id: int
    delivery_id: int
    agent_id: Optional[int] = None
    status: str
    order_id: Optional[str] = None
    customer_name: Optional[str] = None
    delivery_street: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_pincode: Optional[str] = None
    customer_lat: Optional[float] = None
    customer_lon: Optional[float] = None
    risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    delivery_zone: Optional[str] = None
    distance_km: Optional[float] = None

    model_config = {"from_attributes": True}


class RouteInSession(BaseModel):
    id: int
    name: str
    agent_id: int
    status: str
    total_distance: Optional[float] = None
    total_risk_score: Optional[float] = None

    model_config = {"from_attributes": True}


class AgentGroupInfo(BaseModel):
    agent_id: int
    agent_name: str
    vehicle_type: Optional[str] = None
    success_rate: float
    current_load: int
    max_load: int
    deliveries: list[SessionDeliveryInfo]
    route: Optional[RouteInSession] = None


class AssignmentSessionResponse(BaseModel):
    id: int
    name: str
    date: datetime
    status: str
    created_at: datetime
    updated_at: datetime
    delivery_count: int = 0
    agent_count: int = 0
    routes_count: int = 0

    model_config = {"from_attributes": True}


class AssignmentSessionDetail(BaseModel):
    id: int
    name: str
    date: datetime
    status: str
    created_at: datetime
    updated_at: datetime
    deliveries: list[SessionDeliveryInfo] = []
    agents: list[AgentGroupInfo] = []
    routes: list[RouteInSession] = []

    model_config = {"from_attributes": True}


class AssignmentSessionCreate(BaseModel):
    name: Optional[str] = None
    delivery_ids: list[int] = []


class AddDeliveriesRequest(BaseModel):
    delivery_ids: list[int]


class ManualDeliveryRequest(BaseModel):
    customer_name: str
    delivery_street: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_pincode: Optional[str] = None
    customer_lat: Optional[float] = None
    customer_lon: Optional[float] = None
    address: Optional[str] = None
    package_description: Optional[str] = None
    package_weight: float = 1.0
    phone: Optional[str] = None


class GenerateRoutesResponse(BaseModel):
    session_id: int
    routes_created: int
    unassigned_count: int
    routes: list[RouteInSession]
