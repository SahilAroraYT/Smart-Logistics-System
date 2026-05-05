from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.route import RouteResponse, RouteGenerationRequest, RouteGenerationResponse, RouteStopInfo
from app.services import routing_service, delivery_service, audit_service
from app.models.route import Route, RouteStop
from app.models.delivery import DeliveryStatus

router = APIRouter()


@router.get("/", response_model=list[RouteResponse])
def list_routes(db: Session = Depends(get_db)):
    routes = db.query(Route).all()
    return [RouteResponse.model_validate(r) for r in routes]


@router.get("/{route_id}")
def get_route(route_id: int, db: Session = Depends(get_db)):
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    stops = db.query(RouteStop).filter(RouteStop.route_id == route_id).order_by(RouteStop.stop_order).all()
    data = RouteResponse.model_validate(route)
    data.stops = [RouteStopInfo(stop_order=s.stop_order, delivery_id=s.delivery_id, delivery_order_id=s.delivery.order_id if s.delivery else "") for s in stops]
    return data


@router.post("/generate", response_model=RouteGenerationResponse)
def generate_route(payload: RouteGenerationRequest, db: Session = Depends(get_db)):
    pending = delivery_service.get_pending_deliveries(db)
    if not pending:
        raise HTTPException(status_code=400, detail="No pending deliveries")

    delivery_ids = [d.id for d in pending[:payload.max_deliveries]]

    agent_id = payload.agent_id
    if not agent_id and delivery_ids:
        agent_id = routing_service.assign_best_agent(db, pending[0])
    if not agent_id:
        raise HTTPException(status_code=400, detail="No available agents")

    route = routing_service.generate_route(db, agent_id, delivery_ids)
    if not route:
        raise HTTPException(status_code=500, detail="Failed to generate route")

    stops = db.query(RouteStop).filter(RouteStop.route_id == route.id).order_by(RouteStop.stop_order).all()
    return RouteGenerationResponse(
        route_id=route.id,
        route_name=route.name,
        agent_id=route.agent_id,
        total_distance=route.total_distance or 0,
        total_risk_score=route.total_risk_score or 0,
        stops=[RouteStopInfo(stop_order=s.stop_order, delivery_id=s.delivery_id, delivery_order_id=s.delivery.order_id if s.delivery else "") for s in stops],
    )


@router.post("/{route_id}/reroute")
def reroute_route(route_id: int, failed_delivery_ids: list[int] = [], db: Session = Depends(get_db)):
    route = routing_service.trigger_reroute(db, route_id, failed_delivery_ids)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found or no remaining stops")
    return RouteResponse.model_validate(route)
