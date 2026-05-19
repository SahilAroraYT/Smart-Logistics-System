from sqlalchemy.orm import Session
from app.models.agent import DeliveryAgent, AgentStatus
from app.models.delivery import Delivery, DeliveryStatus


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
