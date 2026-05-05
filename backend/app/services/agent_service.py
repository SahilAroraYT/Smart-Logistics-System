from sqlalchemy.orm import Session
from app.models.agent import DeliveryAgent


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
