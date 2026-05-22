import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import Role, User
from app.models.delivery import Delivery, DeliveryStatus
from app.models.route import Route, RouteStatus, RouteStop
from app.models.agent import DeliveryAgent
from app.schemas.agent import AgentResponse, AgentDashboardResponse
from app.schemas.delivery import DeliveryResponse
from app.schemas.route import RouteDetailResponse, RouteStopInfo
from app.services import delivery_service

router = APIRouter()


def get_current_agent(
    current_user: User = Depends(require_role(Role.DELIVERY_AGENT)),
    db: Session = Depends(get_db),
) -> DeliveryAgent:
    agent = db.query(DeliveryAgent).filter(DeliveryAgent.user_id == current_user.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Delivery agent profile not found")
    return agent


@router.get("/me", response_model=AgentResponse)
def me(agent: DeliveryAgent = Depends(get_current_agent)):
    return AgentResponse.model_validate(agent)


@router.get("/dashboard", response_model=AgentDashboardResponse)
def dashboard(
    agent: DeliveryAgent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    deliveries = (
        db.query(Delivery)
        .filter(
            Delivery.agent_id == agent.id,
            Delivery.status == DeliveryStatus.ASSIGNED,
        )
        .all()
    )

    active_route = (
        db.query(Route)
        .filter(
            Route.agent_id == agent.id,
            Route.status.in_([RouteStatus.PLANNED, RouteStatus.IN_PROGRESS]),
        )
        .order_by(Route.created_at.desc())
        .first()
    )

    route_detail = None
    if active_route:
        stops = (
            db.query(RouteStop)
            .filter(RouteStop.route_id == active_route.id)
            .order_by(RouteStop.stop_order)
            .all()
        )
        stop_infos = []
        for s in stops:
            d = s.delivery
            # Only include stops for deliveries still assigned to this agent
            if d and d.agent_id == agent.id:
                stop_infos.append(RouteStopInfo(
                    stop_order=s.stop_order,
                    delivery_id=s.delivery_id,
                    delivery_order_id=d.order_id or "",
                    customer_lat=d.customer_lat,
                    customer_lon=d.customer_lon,
                    risk_category=d.risk_category,
                    risk_score=d.risk_score,
                ))

        geometry = None
        if active_route.geometry:
            try:
                geometry = json.loads(active_route.geometry)
            except (json.JSONDecodeError, TypeError):
                pass

        route_detail = RouteDetailResponse(
            id=active_route.id,
            name=active_route.name,
            agent_id=active_route.agent_id,
            status=active_route.status,
            total_distance=active_route.total_distance,
            total_risk_score=active_route.total_risk_score,
            geometry=geometry,
            created_at=active_route.created_at,
            completed_at=active_route.completed_at,
            stops=stop_infos,
        )

    return AgentDashboardResponse(
        agent=AgentResponse.model_validate(agent),
        deliveries=[DeliveryResponse.model_validate(d) for d in deliveries],
        route=route_detail,
    )


@router.post("/deliveries/{delivery_id}/complete", response_model=DeliveryResponse)
def complete_delivery(
    delivery_id: int,
    agent: DeliveryAgent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    delivery = delivery_service.get_delivery(db, delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    if delivery.agent_id != agent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This delivery is not assigned to you",
        )
    if delivery.status == DeliveryStatus.DELIVERED:
        return DeliveryResponse.model_validate(delivery)

    if delivery.status != DeliveryStatus.ASSIGNED:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot complete delivery with status '{delivery.status}'. Only assigned deliveries can be completed.",
        )

    updated = delivery_service.update_delivery_status(db, delivery_id, DeliveryStatus.DELIVERED)
    return DeliveryResponse.model_validate(updated)
