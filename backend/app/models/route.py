import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class RouteStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    agent_id = Column(Integer, ForeignKey("delivery_agents.id"), nullable=False)
    status = Column(Enum(RouteStatus, native_enum=False), default=RouteStatus.PLANNED)
    total_distance = Column(Float)
    total_risk_score = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    agent = relationship("DeliveryAgent", back_populates="routes")
    deliveries = relationship("Delivery", back_populates="route")
    stops = relationship("RouteStop", back_populates="route", order_by="RouteStop.stop_order")


class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    delivery_id = Column(Integer, ForeignKey("deliveries.id"), nullable=False)
    stop_order = Column(Integer, nullable=False)
    estimated_arrival = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending")

    route = relationship("Route", back_populates="stops")
    delivery = relationship("Delivery")
