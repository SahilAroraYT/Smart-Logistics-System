import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String, Boolean, func

from app.database import Base


class Role(str, enum.Enum):
    ADMIN = "admin"
    OPERATIONS_MANAGER = "operations_manager"
    DELIVERY_SUPERVISOR = "delivery_supervisor"
    DELIVERY_AGENT = "delivery_agent"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(Role, native_enum=False), nullable=False, default=Role.DELIVERY_AGENT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
