from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.alert import AlertResponse
from app.services import alert_service
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=list[AlertResponse])
def list_alerts(
    acknowledged: bool | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db),
):
    alerts = alert_service.get_alerts(db, acknowledged, severity)
    return [AlertResponse.model_validate(a) for a in alerts]


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = alert_service.acknowledge_alert(db, alert_id, current_user.id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse.model_validate(alert)
