from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.audit_log import AuditLogResponse
from app.services import audit_service

router = APIRouter()


@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs(
    user_id: int | None = None,
    action_type: str | None = None,
    entity_type: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    logs = audit_service.get_audit_logs(db, user_id, action_type, entity_type, limit)
    return [AuditLogResponse.model_validate(l) for l in logs]
