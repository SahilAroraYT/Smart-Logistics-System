import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, Integer, String, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class AgentStatus(str, enum.Enum):
    AVAILABLE = "available"
    ON_ROUTE = "on_route"
    OFFLINE = "offline"


class DeliveryAgent(Base):
    __tablename__ = "delivery_agents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20))
    vehicle_type = Column(String(50))
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    current_lat = Column(Float)
    current_lon = Column(Float)
    current_load = Column(Integer, default=0)
    max_load = Column(Integer, default=50)
    success_rate = Column(Float, default=0.0)
    is_available = Column(Boolean, default=True)
    status = Column(Enum(AgentStatus, native_enum=False), default=AgentStatus.AVAILABLE)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    warehouse = relationship("Warehouse", back_populates="agents")
    routes = relationship("Route", back_populates="agent")
    deliveries = relationship("Delivery", back_populates="agent")
