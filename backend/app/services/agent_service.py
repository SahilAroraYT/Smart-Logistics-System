from sqlalchemy.orm import Session
from app.models.agent import DeliveryAgent, AgentStatus
from app.models.delivery import Delivery, DeliveryStatus
from app.models.route import Route, RouteStatus


def get_agents(db: Session):
    return db.query(DeliveryAgent).all()


def get_agent(db: Session, agent_id: int):
    return db.query(DeliveryAgent).filter(DeliveryAgent.id == agent_id).first()


def get_available_agents(db: Session):
    return (
        db.query(DeliveryAgent)
        .filter(DeliveryAgent.is_available == True)
        .order_by(DeliveryAgent.current_load.asc(), DeliveryAgent.success_rate.desc())
        .all()
    )


def get_agents_by_warehouse(db: Session, warehouse_id: int):
    return (
        db.query(DeliveryAgent)
        .filter(DeliveryAgent.warehouse_id == warehouse_id, DeliveryAgent.is_available == True)
        .order_by(DeliveryAgent.current_load.asc(), DeliveryAgent.success_rate.desc())
        .all()
    )


def assign_delivery(db: Session, delivery_id: int, agent_id: int):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    agent = db.query(DeliveryAgent).filter(DeliveryAgent.id == agent_id).first()
    if not delivery or not agent:
        return None
    delivery.agent_id = agent_id
    delivery.status = DeliveryStatus.ASSIGNED
    agent.current_load += 1
    if agent.current_load >= agent.max_load:
        agent.is_available = False
    db.commit()
    return delivery


def batch_assign_deliveries(db: Session, delivery_ids: list[int], agent_id: int) -> list[int]:
    assigned = []
    for did in delivery_ids:
        delivery = assign_delivery(db, did, agent_id)
        if delivery:
            assigned.append(did)
    return assigned


def set_agent_offline(db: Session, agent_id: int):
    agent = get_agent(db, agent_id)
    if not agent:
        return None
    agent.is_available = False
    agent.status = AgentStatus.OFFLINE
    db.commit()

    routes = db.query(Route).filter(
        Route.agent_id == agent_id,
        Route.status == RouteStatus.PLANNED,
    ).all()

    unassigned_count = 0
    for route in routes:
        route.status = RouteStatus.CANCELLED
        for stop in route.stops:
            d = stop.delivery
            if d and d.status == DeliveryStatus.ASSIGNED:
                d.status = DeliveryStatus.UNASSIGNED
                d.agent_id = None
                d.assigned_route_id = None
                unassigned_count += 1
        db.commit()

    db.commit()
    return agent