from typing import Optional
from sqlalchemy.orm import Session
from app.models.alert import Alert, AlertSeverity
from app.models.delivery import Delivery


def create_alert(
    db: Session,
    alert_type: str,
    severity: AlertSeverity,
    message: str,
    delivery_id: Optional[int] = None,
    agent_id: Optional[int] = None,
) -> Alert:
    alert = Alert(
        alert_type=alert_type,
        severity=severity,
        message=message,
        delivery_id=delivery_id,
        agent_id=agent_id,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def check_delivery_risk(db: Session, delivery: Delivery):
    if delivery.risk_score and delivery.risk_score > 75:
        create_alert(
            db,
            "high_risk_delivery",
            AlertSeverity.HIGH,
            f"Delivery {delivery.order_id} has high risk score: {delivery.risk_score:.1f}",
            delivery_id=delivery.id,
        )


def check_agent_overload(db: Session, agent_id: int, agent_load: int, max_load: int):
    if agent_load >= max_load * 0.9:
        create_alert(
            db,
            "agent_overload",
            AlertSeverity.CRITICAL,
            f"Agent {agent_id} is at {agent_load}/{max_load} capacity",
            agent_id=agent_id,
        )


def check_failed_attempts(db: Session, delivery: Delivery):
    if delivery.previous_failed_attempt_same_order and delivery.previous_failed_attempt_same_order >= 2:
        create_alert(
            db,
            "repeated_failure",
            AlertSeverity.HIGH,
            f"Delivery {delivery.order_id} has {delivery.previous_failed_attempt_same_order} failed attempts",
            delivery_id=delivery.id,
        )


def get_alerts(
    db: Session,
    acknowledged: Optional[bool] = None,
    severity: Optional[str] = None,
):
    query = db.query(Alert)
    if acknowledged is not None:
        query = query.filter(Alert.is_acknowledged == acknowledged)
    if severity:
        query = query.filter(Alert.severity == severity)
    return query.order_by(Alert.created_at.desc()).all()


def acknowledge_alert(db: Session, alert_id: int, user_id: int) -> Optional[Alert]:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.is_acknowledged = True
        alert.acknowledged_by = user_id
        db.commit()
        db.refresh(alert)
    return alert
