import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Boolean, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.id"), nullable=True)
    agent_id = Column(Integer, ForeignKey("delivery_agents.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(Enum(AlertSeverity, native_enum=False), nullable=False)
    message = Column(Text, nullable=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    delivery = relationship("Delivery", back_populates="alerts")
