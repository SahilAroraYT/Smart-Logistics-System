from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class AssignmentSession(Base):
    __tablename__ = "assignment_sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    date = Column(DateTime, server_default=func.now())
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    deliveries = relationship("SessionDelivery", back_populates="session", cascade="all, delete-orphan")
    routes = relationship("Route", back_populates="session")


class SessionDelivery(Base):
    __tablename__ = "session_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("assignment_sessions.id", ondelete="CASCADE"), nullable=False)
    delivery_id = Column(Integer, ForeignKey("deliveries.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("delivery_agents.id"), nullable=True)
    status = Column(String(20), default="pending")

    session = relationship("AssignmentSession", back_populates="deliveries")
    delivery = relationship("Delivery", foreign_keys=[delivery_id])
    agent = relationship("DeliveryAgent", foreign_keys=[agent_id])
