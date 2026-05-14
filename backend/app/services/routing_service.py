import json

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.delivery import Delivery, DeliveryStatus
from app.models.agent import DeliveryAgent
from app.models.route import Route, RouteStop, RouteStatus
from app.services import delivery_service, agent_service, alert_service


TRAFFIC_PENALTY = {"low": 0.0, "medium": 0.5, "high": 1.0}
WEATHER_PENALTY = {"clear": 0.0, "rain": 0.5, "fog": 0.8}


def compute_delivery_cost(delivery: Delivery) -> float:
    risk_normalized = (delivery.risk_score or 50) / 100.0
    traffic = TRAFFIC_PENALTY.get(delivery.traffic_level or "low", 0.0)
    weather = WEATHER_PENALTY.get(delivery.weather or "clear", 0.0)
    agent_load = 0.0
    if delivery.agent_id:
        agent_load = 0.3
    distance = delivery.distance_km or 1.0
    return (
        distance * 0.4
        + risk_normalized * 0.3
        + traffic * 0.1
        + weather * 0.1
        + agent_load * 0.1
    )


def get_osrm_route(coords: list[tuple[float, float]]) -> dict:
    if len(coords) < 2:
        return {"distance": 0, "duration": 0, "geometry": ""}
    coords_str = ";".join(f"{lon},{lat}" for lat, lon in coords)
    url = f"{settings.OSRM_BASE_URL}/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                return {
                    "distance": route.get("distance", 0) / 1000,
                    "duration": route.get("duration", 0),
                    "geometry": route.get("geometry", {}),
                }
    except Exception:
        pass
    total = sum(
        ((coords[i][0] - coords[i-1][0])**2 + (coords[i][1] - coords[i-1][1])**2)**0.5 * 111
        for i in range(1, len(coords))
    )
    return {"distance": total, "duration": total * 300, "geometry": {}}


def generate_route(
    db: Session,
    agent_id: int,
    delivery_ids: list[int],
) -> Route | None:
    agent = agent_service.get_agent(db, agent_id)
    if not agent:
        return None

    deliveries = []
    for did in delivery_ids:
        d = db.query(Delivery).filter(Delivery.id == did).first()
        if d and d.status == DeliveryStatus.PENDING:
            deliveries.append(d)

    if not deliveries:
        return None

    deliveries.sort(key=lambda d: (
        0 if d.risk_category == "HIGH" else 1 if d.risk_category == "MEDIUM" else 2,
        d.created_at,
    ))

    wh = agent.warehouse
    origin_lat = wh.lat if wh else (agent.current_lat or 28.7)
    origin_lon = wh.lon if wh else (agent.current_lon or 77.1)
    coords = [(origin_lat, origin_lon)]
    for d in deliveries:
        if d.customer_lat and d.customer_lon:
            coords.append((d.customer_lat, d.customer_lon))

    osrm_result = get_osrm_route(coords)

    geometry_str = None
    geom = osrm_result.get("geometry")
    if geom and isinstance(geom, dict) and geom.get("coordinates"):
        geometry_str = json.dumps(geom)

    route = Route(
        name=f"Route-{agent_id}-{len(db.query(Route).filter(Route.agent_id == agent_id).all()) + 1}",
        agent_id=agent_id,
        status=RouteStatus.PLANNED,
        total_distance=osrm_result["distance"],
        total_risk_score=sum(d.risk_score or 0 for d in deliveries) / len(deliveries),
        geometry=geometry_str,
    )
    db.add(route)
    db.flush()

    for i, d in enumerate(deliveries):
        d.agent_id = agent_id
        d.status = DeliveryStatus.ASSIGNED
        d.assigned_route_id = route.id
        stop = RouteStop(route_id=route.id, delivery_id=d.id, stop_order=i + 1)
        db.add(stop)

    agent.current_load += len(deliveries)
    if agent.current_load >= agent.max_load:
        agent.is_available = False

    db.commit()
    db.refresh(route)
    return route


def trigger_reroute(db: Session, route_id: int, failed_delivery_ids: list[int]):
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        return None
    remaining_stops = (
        db.query(RouteStop)
        .filter(RouteStop.route_id == route_id)
        .filter(RouteStop.delivery_id.notin_(failed_delivery_ids))
        .order_by(RouteStop.stop_order)
        .all()
    )
    if not remaining_stops:
        return None

    agent = agent_service.get_agent(db, route.agent_id)
    if not agent:
        return None

    remaining_deliveries = [s.delivery for s in remaining_stops if s.delivery]
    remaining_deliveries.sort(key=lambda d: (
        0 if (d.risk_category == "HIGH") else 1 if (d.risk_category == "MEDIUM") else 2,
        d.created_at,
    ))

    wh = agent.warehouse
    origin_lat = wh.lat if wh else (agent.current_lat or 28.7)
    origin_lon = wh.lon if wh else (agent.current_lon or 77.1)
    coords = [(origin_lat, origin_lon)]
    for d in remaining_deliveries:
        if d.customer_lat and d.customer_lon:
            coords.append((d.customer_lat, d.customer_lon))

    osrm_result = get_osrm_route(coords)
    route.total_distance = osrm_result["distance"]
    route.total_risk_score = sum(d.risk_score or 0 for d in remaining_deliveries) / len(remaining_deliveries) if remaining_deliveries else 0
    geom = osrm_result.get("geometry")
    if geom and isinstance(geom, dict) and geom.get("coordinates"):
        route.geometry = json.dumps(geom)

    for stop in remaining_stops:
        db.delete(stop)
    db.flush()

    for i, d in enumerate(remaining_deliveries):
        stop = RouteStop(route_id=route.id, delivery_id=d.id, stop_order=i + 1)
        db.add(stop)

    db.commit()
    db.refresh(route)
    return route


def assign_best_agent(db: Session, delivery: Delivery) -> int | None:
    agents = agent_service.get_available_agents(db)
    if not agents:
        return None

    def agent_score(a: DeliveryAgent) -> float:
        dist = 0
        wh = a.warehouse
        ref_lat = wh.lat if wh else (a.current_lat or 28.7)
        ref_lon = wh.lon if wh else (a.current_lon or 77.1)
        if delivery.customer_lat and delivery.customer_lon:
            dist = ((delivery.customer_lat - ref_lat)**2 + (delivery.customer_lon - ref_lon)**2)**0.5
        load_ratio = a.current_load / a.max_load if a.max_load else 1
        return dist * 0.4 + load_ratio * 0.3 + (1 - a.success_rate) * 0.3

    best = min(agents, key=agent_score)
    return best.id
