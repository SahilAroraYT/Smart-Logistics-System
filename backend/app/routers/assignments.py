from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.assignment import (
    AssignmentSessionResponse,
    AssignmentSessionDetail,
    AssignmentSessionCreate,
    AddDeliveriesRequest,
    ManualDeliveryRequest,
    GenerateRoutesResponse,
    SessionDeliveryInfo,
    AgentGroupInfo,
    RouteInSession,
)
from app.services import assignment_service
from app.models.route import Route

router = APIRouter()


@router.get("/", response_model=list[AssignmentSessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    sessions = assignment_service.get_sessions(db)
    result = []
    for s in sessions:
        result.append(AssignmentSessionResponse(
            id=s.id,
            name=s.name,
            date=s.date,
            status=s.status,
            created_at=s.created_at,
            updated_at=s.updated_at,
            delivery_count=len(s.deliveries) if s.deliveries else 0,
            agent_count=len({sd.agent_id for sd in s.deliveries if sd.agent_id}),
            routes_count=len(s.routes) if s.routes else 0,
        ))
    return result


@router.post("/", response_model=AssignmentSessionResponse)
def create_session(payload: AssignmentSessionCreate, db: Session = Depends(get_db)):
    session = assignment_service.create_session(db, payload.name, payload.delivery_ids)
    return AssignmentSessionResponse(
        id=session.id,
        name=session.name,
        date=session.date,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
        delivery_count=len(session.deliveries) if session.deliveries else 0,
        agent_count=0,
        routes_count=0,
    )


@router.get("/{session_id}", response_model=AssignmentSessionDetail)
def get_session(session_id: int, db: Session = Depends(get_db)):
    detail = assignment_service.get_session_detail(db, session_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Session not found")
    return AssignmentSessionDetail(
        id=detail["id"],
        name=detail["name"],
        date=detail["date"],
        status=detail["status"],
        created_at=detail["created_at"],
        updated_at=detail["updated_at"],
        deliveries=[SessionDeliveryInfo(**d) for d in detail["deliveries"]],
        agents=[AgentGroupInfo(**a) for a in detail["agents"]],
        routes=[RouteInSession(**r) for r in detail["routes"]],
    )


@router.delete("/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    if not assignment_service.delete_session(db, session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"detail": "Session deleted"}


@router.post("/{session_id}/deliveries")
def add_deliveries(session_id: int, payload: AddDeliveriesRequest, db: Session = Depends(get_db)):
    session = assignment_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    count = assignment_service.add_deliveries_to_session(db, session_id, payload.delivery_ids)
    return {"added": count}


@router.delete("/{session_id}/deliveries/{delivery_id}")
def remove_delivery(session_id: int, delivery_id: int, db: Session = Depends(get_db)):
    if not assignment_service.remove_delivery_from_session(db, session_id, delivery_id):
        raise HTTPException(status_code=404, detail="Delivery not in session")
    return {"detail": "Delivery removed from session"}


@router.post("/{session_id}/deliveries/manual")
def add_manual_delivery(session_id: int, payload: ManualDeliveryRequest, db: Session = Depends(get_db)):
    session = assignment_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    delivery = assignment_service.create_manual_delivery(
        db, session_id,
        customer_name=payload.customer_name,
        delivery_street=payload.delivery_street,
        delivery_city=payload.delivery_city,
        delivery_pincode=payload.delivery_pincode,
        customer_lat=payload.customer_lat,
        customer_lon=payload.customer_lon,
        package_weight=payload.package_weight,
    )
    return {
        "id": delivery.id,
        "order_id": delivery.order_id,
        "customer_name": delivery.customer_name,
        "delivery_street": delivery.delivery_street,
        "delivery_city": delivery.delivery_city,
        "delivery_pincode": delivery.delivery_pincode,
        "customer_lat": delivery.customer_lat,
        "customer_lon": delivery.customer_lon,
        "risk_score": delivery.risk_score,
        "risk_category": delivery.risk_category,
        "status": delivery.status,
    }


@router.post("/{session_id}/generate", response_model=GenerateRoutesResponse)
def generate_routes(session_id: int, db: Session = Depends(get_db)):
    result = assignment_service.generate_routes_for_session(db, session_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    routes = db.query(Route).filter(Route.session_id == session_id).all()
    return GenerateRoutesResponse(
        session_id=session_id,
        routes_created=result["routes_created"],
        unassigned_count=result["unassigned_count"],
        routes=[
            RouteInSession(
                id=r.id,
                name=r.name,
                agent_id=r.agent_id,
                status=r.status,
                total_distance=r.total_distance,
                total_risk_score=r.total_risk_score,
            )
            for r in routes
        ],
    )
