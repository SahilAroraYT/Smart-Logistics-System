from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.agent import AgentResponse, AgentUpdate, AgentAssignmentRequest, AgentAssignmentResponse
from app.services import agent_service, routing_service
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.delivery import Delivery, DeliveryStatus
from app.models.route import Route, RouteStatus, RouteStop

router = APIRouter()


@router.get("/", response_model=list[AgentResponse])
def list_agents(db: Session = Depends(get_db)):
    agents = agent_service.get_agents(db)
    return [AgentResponse.model_validate(a) for a in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = agent_service.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse.model_validate(agent)


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: int, payload: AgentUpdate, db: Session = Depends(get_db)):
    agent = agent_service.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(agent, key, val)
    db.commit()
    db.refresh(agent)
    return AgentResponse.model_validate(agent)


@router.post("/assign", response_model=AgentAssignmentResponse)
def assign_deliveries(
    payload: AgentAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assigned = agent_service.batch_assign_deliveries(db, payload.delivery_ids, payload.agent_id)
    if not assigned:
        raise HTTPException(status_code=400, detail="No deliveries could be assigned")
    return AgentAssignmentResponse(
        agent_id=payload.agent_id,
        assigned_count=len(assigned),
        deliveries=assigned,
    )


@router.post("/auto-assign")
def auto_assign_all(db: Session = Depends(get_db)):
    from app.services import delivery_service as ds
    from app.services import assignment_service as asvc
    from app.services import routing_service

    pending = ds.get_pending_deliveries(db)
    if not pending:
        return {"assigned_count": 0, "routes_created": 0}

    agents = agent_service.get_available_agents(db)
    if not agents:
        raise HTTPException(status_code=400, detail="No available agents")

    agent_assignments = asvc._greedy_assign_deliveries(db, pending, agents)

    assigned = []
    routes_created = 0
    for agent_id, d_ids in agent_assignments.items():
        route = routing_service.generate_route(db, agent_id, d_ids)
        if route:
            routes_created += 1
            for did in d_ids:
                assigned.append({"delivery_id": did, "agent_id": agent_id, "route_id": route.id})

    return {"assigned_count": len(assigned), "routes_created": routes_created, "assignments": assigned}


@router.post("/{agent_id}/offline")
def set_agent_offline(agent_id: int, db: Session = Depends(get_db)):
    from app.models.route import Route, RouteStatus
    from app.models.route import RouteStop

    agent = agent_service.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.is_available = False
    agent.status = "offline"
    db.commit()

    routes = db.query(Route).filter(
        Route.agent_id == agent_id,
        Route.status == RouteStatus.PLANNED,
    ).all()

    redistributed = 0
    for route in routes:
        pending_stops = (
            db.query(RouteStop)
            .filter(RouteStop.route_id == route.id)
            .all()
        )
        for stop in pending_stops:
            delivery = db.query(Delivery).filter(Delivery.id == stop.delivery_id).first()
            if delivery and delivery.status == DeliveryStatus.ASSIGNED:
                delivery.status = DeliveryStatus.PENDING
                delivery.agent_id = None
                delivery.assigned_route_id = None
                redistributed += 1
            db.delete(stop)

        route.status = RouteStatus.CANCELLED
        db.commit()

    return {"detail": f"Agent {agent_id} set offline", "redistributed_count": redistributed}
