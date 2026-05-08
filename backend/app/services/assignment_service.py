from datetime import datetime
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.models.assignment import AssignmentSession, SessionDelivery
from app.models.delivery import Delivery, DeliveryStatus
from app.models.agent import DeliveryAgent
from app.models.route import Route, RouteStop, RouteStatus
from app.services import delivery_service, agent_service, routing_service, ml_service


NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"


def _geocode_address(street: str, city: str, pincode: str) -> tuple[Optional[float], Optional[float]]:
    """Resolve structured address to (lat, lon) via Nominatim."""
    parts = [p for p in [street, city, pincode] if p]
    if not parts:
        return None, None
    query = ", ".join(parts)
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                NOMINATIM_BASE,
                params={"q": query, "format": "json", "limit": 1},
                headers={"User-Agent": "SmartLogisticsSystem/1.0"},
            )
            resp.raise_for_status()
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None, None


def create_session(
    db: Session,
    name: Optional[str] = None,
    delivery_ids: Optional[list[int]] = None,
) -> AssignmentSession:
    if not name:
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        count = (
            db.query(AssignmentSession)
            .filter(AssignmentSession.name.like(f"Assignment {today_str}%"))
            .count()
        )
        name = f"Assignment {today_str} #{count + 1}"

    session = AssignmentSession(name=name, status="draft")
    db.add(session)
    db.flush()

    if delivery_ids:
        for did in delivery_ids:
            d = db.query(Delivery).filter(Delivery.id == did, Delivery.status == DeliveryStatus.PENDING).first()
            if d:
                sd = SessionDelivery(session_id=session.id, delivery_id=d.id)
                db.add(sd)

    db.commit()
    db.refresh(session)
    return session


def get_sessions(db: Session) -> list[AssignmentSession]:
    return db.query(AssignmentSession).order_by(AssignmentSession.created_at.desc()).all()


def get_session(db: Session, session_id: int) -> Optional[AssignmentSession]:
    return db.query(AssignmentSession).filter(AssignmentSession.id == session_id).first()


def delete_session(db: Session, session_id: int) -> bool:
    session = get_session(db, session_id)
    if not session:
        return False
    db.delete(session)
    db.commit()
    return True


def add_deliveries_to_session(
    db: Session, session_id: int, delivery_ids: list[int]
) -> int:
    added = 0
    for did in delivery_ids:
        exists = (
            db.query(SessionDelivery)
            .filter(SessionDelivery.session_id == session_id, SessionDelivery.delivery_id == did)
            .first()
        )
        if exists:
            continue
        d = db.query(Delivery).filter(Delivery.id == did, Delivery.status == DeliveryStatus.PENDING).first()
        if d:
            sd = SessionDelivery(session_id=session_id, delivery_id=d.id)
            db.add(sd)
            added += 1
    db.commit()
    return added


def remove_delivery_from_session(db: Session, session_id: int, delivery_id: int) -> bool:
    sd = (
        db.query(SessionDelivery)
        .filter(SessionDelivery.session_id == session_id, SessionDelivery.delivery_id == delivery_id)
        .first()
    )
    if not sd:
        return False
    db.delete(sd)
    db.commit()
    return True


def create_manual_delivery(
    db: Session,
    session_id: int,
    customer_name: str,
    delivery_street: Optional[str] = None,
    delivery_city: Optional[str] = None,
    delivery_pincode: Optional[str] = None,
    customer_lat: Optional[float] = None,
    customer_lon: Optional[float] = None,
    package_weight: float = 1.0,
) -> Delivery:
    # Geocode if lat/lon not provided and address is available
    resolved_lat, resolved_lon = customer_lat, customer_lon
    if resolved_lat is None or resolved_lon is None:
        resolved_lat, resolved_lon = _geocode_address(
            delivery_street or "", delivery_city or "", delivery_pincode or ""
        )

    delivery = Delivery(
        customer_id=99999,
        customer_name=customer_name,
        delivery_street=delivery_street,
        delivery_city=delivery_city,
        delivery_pincode=delivery_pincode,
        customer_lat=resolved_lat,
        customer_lon=resolved_lon,
        warehouse_lat=28.7,
        warehouse_lon=77.1,
        distance_km=5.0,
        package_weight=package_weight,
        package_size="medium",
        delivery_zone="Zone_A",
        time_slot="morning",
        day_of_week=datetime.utcnow().strftime("%a"),
        month=datetime.utcnow().month,
        is_weekend=datetime.utcnow().weekday() >= 5,
        is_holiday=False,
        location_type="residential",
        building_type="apartment",
        floor_number=1,
        lift_available=True,
        payment_type="prepaid",
        order_value=0.0,
        weather="clear",
        traffic_level="low",
        customer_past_orders=0,
        past_success_rate=0.9,
        customer_cancellation_rate=0.0,
        customer_return_rate=0.0,
        phone_reachable=True,
        customer_available=True,
        preferred_slot_match=True,
        otp_required=False,
        agent_experience_years=0.0,
        agent_success_rate=0.0,
        agent_daily_load=0,
        delivery_attempts=0,
        previous_failed_attempt_same_order=0,
        status=DeliveryStatus.PENDING,
    )
    db.add(delivery)
    db.flush()

    pred_data = delivery_service.delivery_to_prediction_data(delivery)
    try:
        result = ml_service.predict(pred_data)
        delivery.risk_score = result["risk_score"]
        delivery.risk_category = result["risk_category"]
    except Exception:
        pass

    sd = SessionDelivery(session_id=session_id, delivery_id=delivery.id)
    db.add(sd)
    db.commit()
    db.refresh(delivery)
    return delivery


def _greedy_assign_deliveries(
    db: Session, deliveries: list[Delivery], agents: list[DeliveryAgent]
) -> dict[int, list[int]]:
    """Greedy cluster-based assignment: sort deliveries by risk, assign each to best agent."""
    agent_assignments: dict[int, list[int]] = {a.id: [] for a in agents}
    agent_capacities: dict[int, int] = {
        a.id: a.max_load - a.current_load for a in agents
    }

    sorted_dels = sorted(
        deliveries,
        key=lambda d: (
            0 if d.risk_category == "HIGH" else 1 if d.risk_category == "MEDIUM" else 2,
            -(d.risk_score or 0),
        ),
    )

    for d in sorted_dels:
        best_agent_id = None
        best_score = float("inf")

        for a in agents:
            if agent_capacities.get(a.id, 0) <= 0:
                continue

            dist = 0.0
            if d.customer_lat and d.customer_lon and a.current_lat and a.current_lon:
                dist = (
                    (d.customer_lat - a.current_lat) ** 2
                    + (d.customer_lon - a.current_lon) ** 2
                ) ** 0.5

            load_ratio = (a.current_load + len(agent_assignments[a.id])) / a.max_load if a.max_load else 1
            score = dist * 0.4 + load_ratio * 0.3 + (1 - a.success_rate) * 0.3

            if score < best_score:
                best_score = score
                best_agent_id = a.id

        if best_agent_id is not None:
            agent_assignments[best_agent_id].append(d.id)
            agent_capacities[best_agent_id] -= 1

    return {k: v for k, v in agent_assignments.items() if v}


def generate_routes_for_session(db: Session, session_id: int) -> dict:
    """Cluster session deliveries → assign to agents → generate per-agent routes."""
    session = get_session(db, session_id)
    if not session:
        return {"error": "Session not found"}

    session.status = "generating"
    db.commit()

    session_dels = (
        db.query(SessionDelivery)
        .filter(SessionDelivery.session_id == session_id)
        .all()
    )

    delivery_ids = [sd.delivery_id for sd in session_dels]
    deliveries = (
        db.query(Delivery)
        .filter(Delivery.id.in_(delivery_ids), Delivery.status == DeliveryStatus.PENDING)
        .all()
    )

    if not deliveries:
        session.status = "completed"
        db.commit()
        return {"routes_created": 0, "unassigned_count": 0, "error": "No pending deliveries"}

    agents = agent_service.get_available_agents(db)
    if not agents:
        session.status = "completed"
        db.commit()
        return {"routes_created": 0, "unassigned_count": len(deliveries), "error": "No available agents"}

    agent_assignments = _greedy_assign_deliveries(db, deliveries, agents)

    routes_created = 0
    unassigned = len(deliveries)

    for agent_id, d_ids in agent_assignments.items():
        route = routing_service.generate_route(db, agent_id, d_ids)
        if route:
            route.session_id = session_id
            for did in d_ids:
                sd = (
                    db.query(SessionDelivery)
                    .filter(SessionDelivery.session_id == session_id, SessionDelivery.delivery_id == did)
                    .first()
                )
                if sd:
                    sd.agent_id = agent_id
                    sd.status = "assigned"
            routes_created += 1
            unassigned -= len(d_ids)

    session.status = "completed"
    db.commit()

    return {
        "routes_created": routes_created,
        "unassigned_count": unassigned,
    }


def get_session_detail(db: Session, session_id: int) -> Optional[dict]:
    session = get_session(db, session_id)
    if not session:
        return None

    session_dels = (
        db.query(SessionDelivery)
        .filter(SessionDelivery.session_id == session_id)
        .all()
    )

    deliveries_info = []
    for sd in session_dels:
        d = _get_delivery_info(db, sd.delivery_id)
        deliveries_info.append({
            "id": sd.id,
            "delivery_id": sd.delivery_id,
            "agent_id": sd.agent_id,
            "status": sd.status,
            "order_id": d.get("order_id") if d else None,
            "customer_name": d.get("customer_name") if d else None,
            "delivery_street": d.get("delivery_street") if d else None,
            "delivery_city": d.get("delivery_city") if d else None,
            "delivery_pincode": d.get("delivery_pincode") if d else None,
            "customer_lat": d.get("customer_lat") if d else None,
            "customer_lon": d.get("customer_lon") if d else None,
            "risk_score": d.get("risk_score") if d else None,
            "risk_category": d.get("risk_category") if d else None,
            "delivery_zone": d.get("delivery_zone") if d else None,
            "distance_km": d.get("distance_km") if d else None,
        })

    routes = (
        db.query(Route)
        .filter(Route.session_id == session_id)
        .all()
    )

    routes_info = [
        {
            "id": r.id,
            "name": r.name,
            "agent_id": r.agent_id,
            "status": r.status,
            "total_distance": r.total_distance,
            "total_risk_score": r.total_risk_score,
        }
        for r in routes
    ]

    agent_ids = set()
    for sd in session_dels:
        if sd.agent_id:
            agent_ids.add(sd.agent_id)
    for r in routes:
        agent_ids.add(r.agent_id)

    agents_info = []
    for aid in agent_ids:
        agent = agent_service.get_agent(db, aid)
        if not agent:
            continue
        agent_dels = []
        for sd in session_dels:
            if sd.agent_id != aid:
                continue
            d = _get_delivery_info(db, sd.delivery_id)
            agent_dels.append({
                "id": sd.id,
                "delivery_id": sd.delivery_id,
                "agent_id": sd.agent_id,
                "status": sd.status,
                "order_id": d.get("order_id") if d else None,
                "customer_name": d.get("customer_name") if d else None,
                "delivery_street": d.get("delivery_street") if d else None,
                "delivery_city": d.get("delivery_city") if d else None,
                "delivery_pincode": d.get("delivery_pincode") if d else None,
                "customer_lat": d.get("customer_lat") if d else None,
                "customer_lon": d.get("customer_lon") if d else None,
                "risk_score": d.get("risk_score") if d else None,
                "risk_category": d.get("risk_category") if d else None,
                "delivery_zone": d.get("delivery_zone") if d else None,
                "distance_km": d.get("distance_km") if d else None,
            })
        agent_route = next((r for r in routes if r.agent_id == aid), None)
        agents_info.append({
            "agent_id": agent.id,
            "agent_name": agent.name,
            "vehicle_type": agent.vehicle_type,
            "success_rate": agent.success_rate,
            "current_load": agent.current_load,
            "max_load": agent.max_load,
            "deliveries": agent_dels,
            "route": {
                "id": agent_route.id,
                "name": agent_route.name,
                "agent_id": agent_route.agent_id,
                "status": agent_route.status,
                "total_distance": agent_route.total_distance,
                "total_risk_score": agent_route.total_risk_score,
            } if agent_route else None,
        })

    return {
        "id": session.id,
        "name": session.name,
        "date": session.date,
        "status": session.status,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "deliveries": deliveries_info,
        "agents": agents_info,
        "routes": routes_info,
    }


def _get_delivery_info(db: Session, delivery_id: int) -> Optional[dict]:
    d = delivery_service.get_delivery(db, delivery_id)
    if not d:
        return None
    return {
        "id": d.id,
        "order_id": d.order_id,
        "customer_name": d.customer_name,
        "delivery_street": d.delivery_street,
        "delivery_city": d.delivery_city,
        "delivery_pincode": d.delivery_pincode,
        "customer_lat": d.customer_lat,
        "customer_lon": d.customer_lon,
        "risk_score": d.risk_score,
        "risk_category": d.risk_category,
        "status": d.status,
        "delivery_zone": d.delivery_zone,
        "distance_km": d.distance_km,
    }
