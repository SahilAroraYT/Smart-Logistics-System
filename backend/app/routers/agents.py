from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.agent import AgentResponse, AgentAssignmentRequest, AgentAssignmentResponse
from app.services import agent_service, routing_service
from app.dependencies.auth import get_current_user
from app.models.user import User

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
    pending = ds.get_pending_deliveries(db)
    assigned = []
    for d in pending:
        agent_id = routing_service.assign_best_agent(db, d)
        if agent_id:
            agent_service.assign_delivery(db, d.id, agent_id)
            assigned.append({"delivery_id": d.id, "agent_id": agent_id})
    return {"assigned_count": len(assigned), "assignments": assigned}
