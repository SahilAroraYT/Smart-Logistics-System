from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PredictionRiskExplanation(BaseModel):
    factor: str
    value: float
    description: str


class PredictionResponse(BaseModel):
    order_id: Optional[str] = None
    probability: float
    risk_score: float
    risk_category: str
    confidence: str
    explanation: list[PredictionRiskExplanation]


class DeliveryResponse(BaseModel):
    id: int
    order_id: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    delivery_street: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_pincode: Optional[str] = None
    customer_lat: Optional[float] = None
    customer_lon: Optional[float] = None
    warehouse_lat: Optional[float] = None
    warehouse_lon: Optional[float] = None
    distance_km: Optional[float] = None
    delivery_zone: Optional[str] = None
    time_slot: Optional[str] = None
    day_of_week: Optional[str] = None
    month: Optional[int] = None
    is_weekend: Optional[bool] = None
    is_holiday: Optional[bool] = None
    location_type: Optional[str] = None
    building_type: Optional[str] = None
    floor_number: Optional[int] = None
    lift_available: Optional[bool] = None
    payment_type: Optional[str] = None
    order_value: Optional[float] = None
    package_weight: Optional[float] = None
    package_size: Optional[str] = None
    weather: Optional[str] = None
    traffic_level: Optional[str] = None
    customer_past_orders: Optional[int] = None
    past_success_rate: Optional[float] = None
    customer_cancellation_rate: Optional[float] = None
    customer_return_rate: Optional[float] = None
    phone_reachable: Optional[bool] = None
    customer_available: Optional[bool] = None
    preferred_slot_match: Optional[bool] = None
    otp_required: Optional[bool] = None
    agent_experience_years: Optional[float] = None
    agent_success_rate: Optional[float] = None
    agent_daily_load: Optional[int] = None
    delivery_attempts: Optional[int] = None
    previous_failed_attempt_same_order: Optional[int] = None
    agent_id: Optional[int] = None
    status: Optional[str] = None
    risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    delivered_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DeliveryListResponse(BaseModel):
    deliveries: list[DeliveryResponse]
    total: int
    page: int
    page_size: int


class PredictionRequest(BaseModel):
    distance_km: float
    package_weight: float
    floor_number: int
    past_success_rate: float
    customer_cancellation_rate: float
    customer_return_rate: float
    agent_daily_load: int
    previous_failed_attempt_same_order: int
    lift_available: bool
    delivery_zone: str
    time_slot: str
    day_of_week: str
    location_type: str
    building_type: str
    payment_type: str
    package_size: str
    weather: str
    traffic_level: str
    order_id: Optional[str] = None
    customer_lat: Optional[float] = None
    customer_lon: Optional[float] = None
    warehouse_lat: Optional[float] = None
    warehouse_lon: Optional[float] = None
    month: int = 1
    is_weekend: bool = False
    is_holiday: bool = False
    customer_past_orders: int = 0
    phone_reachable: bool = True
    customer_available: bool = True
    preferred_slot_match: bool = True
    otp_required: bool = False
    agent_experience_years: float = 0.0
    agent_success_rate: float = 0.0
    order_value: float = 0.0
    delivery_attempts: int = 0


class ManualDeliveryCreate(BaseModel):
    customer_name: str
    delivery_street: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_pincode: Optional[str] = None
    customer_lat: Optional[float] = None
    customer_lon: Optional[float] = None
    session_id: Optional[int] = None
    package_weight: float = 1.0
    package_description: Optional[str] = None
    phone: Optional[str] = None
