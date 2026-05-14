from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WarehouseResponse(BaseModel):
    id: int
    name: str
    street: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    lat: float
    lon: float
    created_at: datetime

    model_config = {"from_attributes": True}


class WarehouseCreate(BaseModel):
    name: str
    street: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    lat: float
    lon: float


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
