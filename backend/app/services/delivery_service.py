from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.delivery import Delivery, DeliveryStatus
from app.services import ml_service


def get_deliveries(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    risk_category: Optional[str] = None,
    agent_id: Optional[int] = None,
):
    query = db.query(Delivery)
    if status:
        query = query.filter(Delivery.status == status)
    if risk_category:
        query = query.filter(Delivery.risk_category == risk_category)
    if agent_id:
        query = query.filter(Delivery.agent_id == agent_id)
    total = query.count()
    deliveries = (
        query.order_by(Delivery.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return deliveries, total


def get_delivery(db: Session, delivery_id: int) -> Optional[Delivery]:
    return db.query(Delivery).filter(Delivery.id == delivery_id).first()


def get_pending_deliveries(db: Session):
    return (
        db.query(Delivery)
        .filter(Delivery.status == DeliveryStatus.PENDING)
        .order_by(Delivery.risk_score.desc(), Delivery.created_at.asc())
        .all()
    )


def update_delivery_status(db: Session, delivery_id: int, status: DeliveryStatus):
    delivery = get_delivery(db, delivery_id)
    if delivery:
        delivery.status = status
        if status == DeliveryStatus.DELIVERED:
            delivery.delivered_at = datetime.utcnow()
        db.commit()
        db.refresh(delivery)
    return delivery


def predict_delivery_risk(db: Session, delivery_id: int) -> Optional[dict]:
    delivery = get_delivery(db, delivery_id)
    if not delivery:
        return None
    data = delivery_to_prediction_data(delivery)
    result = ml_service.predict(data)
    delivery.risk_score = result["risk_score"]
    delivery.risk_category = result["risk_category"]
    db.commit()
    db.refresh(delivery)
    return result


def batch_predict_pending(db: Session):
    deliveries = get_pending_deliveries(db)
    results = []
    for d in deliveries:
        data = delivery_to_prediction_data(d)
        result = ml_service.predict(data)
        d.risk_score = result["risk_score"]
        d.risk_category = result["risk_category"]
        results.append({"delivery_id": d.id, "order_id": d.order_id, **result})
    db.commit()
    return results


def delivery_to_prediction_data(delivery: Delivery) -> dict:
    return {
        "distance_km": delivery.distance_km or 0.0,
        "package_weight": delivery.package_weight or 0.0,
        "floor_number": delivery.floor_number or 0,
        "past_success_rate": delivery.past_success_rate or 0.0,
        "customer_cancellation_rate": delivery.customer_cancellation_rate or 0.0,
        "customer_return_rate": delivery.customer_return_rate or 0.0,
        "agent_daily_load": delivery.agent_daily_load or 0,
        "previous_failed_attempt_same_order": delivery.previous_failed_attempt_same_order or 0,
        "lift_available": delivery.lift_available or False,
        "delivery_zone": delivery.delivery_zone or "Zone_A",
        "time_slot": delivery.time_slot or "morning",
        "day_of_week": delivery.day_of_week or "Mon",
        "location_type": delivery.location_type or "residential",
        "building_type": delivery.building_type or "apartment",
        "payment_type": delivery.payment_type or "prepaid",
        "package_size": delivery.package_size or "medium",
        "weather": delivery.weather or "clear",
        "traffic_level": delivery.traffic_level or "low",
        "month": delivery.month or 1,
        "is_weekend": delivery.is_weekend or False,
        "is_holiday": delivery.is_holiday or False,
        "customer_past_orders": delivery.customer_past_orders or 0,
        "phone_reachable": delivery.phone_reachable or True,
        "customer_available": delivery.customer_available or True,
        "preferred_slot_match": delivery.preferred_slot_match or True,
        "otp_required": delivery.otp_required or False,
        "agent_experience_years": delivery.agent_experience_years or 0.0,
        "agent_success_rate": delivery.agent_success_rate or 0.0,
        "order_value": delivery.order_value or 0.0,
        "delivery_attempts": delivery.delivery_attempts or 0,
    }
