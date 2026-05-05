from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    metadata: Optional[dict] = None
    timestamp: datetime

    model_config = {"from_attributes": True}
