import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Boolean, func
from sqlalchemy.orm import relationship

from app.database import Base


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    REROUTED = "rerouted"


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, index=True)

    # Customer & location
    customer_id = Column(Integer, index=True)
    customer_name = Column(String(255), nullable=True)
    delivery_street = Column(String(255), nullable=True)
    delivery_city = Column(String(100), nullable=True)
    delivery_pincode = Column(String(20), nullable=True)
    customer_lat = Column(Float)
    customer_lon = Column(Float)
    warehouse_lat = Column(Float)
    warehouse_lon = Column(Float)
    distance_km = Column(Float)
    delivery_zone = Column(String(20))

    # Time
    time_slot = Column(String(20))
    day_of_week = Column(String(10))
    month = Column(Integer)
    is_weekend = Column(Boolean)
    is_holiday = Column(Boolean)

    # Location details
    location_type = Column(String(20))
    building_type = Column(String(30))
    floor_number = Column(Integer)
    lift_available = Column(Boolean)

    # Payment & package
    payment_type = Column(String(20))
    order_value = Column(Float)
    package_weight = Column(Float)
    package_size = Column(String(20))

    # Conditions
    weather = Column(String(20))
    traffic_level = Column(String(20))

    # Customer history
    customer_past_orders = Column(Integer)
    past_success_rate = Column(Float)
    customer_cancellation_rate = Column(Float)
    customer_return_rate = Column(Float)
    phone_reachable = Column(Boolean)
    customer_available = Column(Boolean)
    preferred_slot_match = Column(Boolean)
    otp_required = Column(Boolean)

    # Agent info
    agent_experience_years = Column(Float)
    agent_success_rate = Column(Float)
    agent_daily_load = Column(Integer)
    delivery_attempts = Column(Integer, default=0)
    previous_failed_attempt_same_order = Column(Integer, default=0)

    # Assignment & risk
    agent_id = Column(Integer, ForeignKey("delivery_agents.id"), nullable=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    status = Column(Enum(DeliveryStatus, native_enum=False), default=DeliveryStatus.PENDING)
    risk_score = Column(Float, nullable=True)
    risk_category = Column(String(10), nullable=True)
    assigned_route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    delivered_at = Column(DateTime, nullable=True)

    agent = relationship("DeliveryAgent", back_populates="deliveries")
    warehouse = relationship("Warehouse")
    route = relationship("Route", back_populates="deliveries")
    alerts = relationship("Alert", back_populates="delivery")
