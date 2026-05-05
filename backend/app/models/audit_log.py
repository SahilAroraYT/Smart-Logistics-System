from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, func

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action_type = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer, nullable=True)
    extra_data = Column("metadata", JSON, nullable=True)
    timestamp = Column(DateTime, server_default=func.now())
