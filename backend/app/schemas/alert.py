from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: int
    delivery_id: Optional[int] = None
    agent_id: Optional[int] = None
    alert_type: str
    severity: str
    message: str
    is_acknowledged: bool
    acknowledged_by: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}
