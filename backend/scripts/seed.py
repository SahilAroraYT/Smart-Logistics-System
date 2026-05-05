import sys
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, SessionLocal, engine
from app.models.user import User, Role
from app.models.agent import DeliveryAgent, AgentStatus
from app.models.delivery import Delivery, DeliveryStatus
from app.services import auth_service, ml_service


def seed_users(db: Session):
    users = [
        ("admin@logistics.com", "admin123", "System Admin", Role.ADMIN),
        ("manager@logistics.com", "manager123", "Operations Manager", Role.OPERATIONS_MANAGER),
        ("supervisor@logistics.com", "supervisor123", "Delivery Supervisor", Role.DELIVERY_SUPERVISOR),
        ("agent1@logistics.com", "agent123", "Agent One", Role.DELIVERY_AGENT),
    ]
    for email, password, name, role in users:
        if not db.query(User).filter(User.email == email).first():
            user = User(
                email=email,
                password_hash=auth_service.hash_password(password),
                full_name=name,
                role=role,
            )
            db.add(user)
    db.commit()
    print(f"  Seeded {len(users)} users")


def seed_agents(db: Session):
    agents = db.query(User).filter(User.role == Role.DELIVERY_AGENT).all()
    created = 0
    for user in agents:
        if not db.query(DeliveryAgent).filter(DeliveryAgent.user_id == user.id).first():
            agent = DeliveryAgent(
                user_id=user.id,
                name=user.full_name,
                vehicle_type="bike",
                current_lat=28.7,
                current_lon=77.1,
                current_load=0,
                max_load=50,
                success_rate=0.85,
                is_available=True,
                status=AgentStatus.AVAILABLE,
            )
            db.add(agent)
            created += 1

    for i in range(5):
        if not db.query(DeliveryAgent).filter(DeliveryAgent.name == f"Agent {i+2}").first():
            agent = DeliveryAgent(
                name=f"Agent {i+2}",
                phone=f"98765432{i}0",
                vehicle_type=["bike", "car", "bike", "van", "bike"][i],
                current_lat=28.6 + i * 0.1,
                current_lon=77.0 + i * 0.1,
                current_load=i * 5,
                max_load=50,
                success_rate=0.7 + i * 0.05,
                is_available=True,
                status=AgentStatus.AVAILABLE,
            )
            db.add(agent)
            created += 1
    db.commit()
    print(f"  Seeded {created} agents")


def seed_deliveries(db: Session):
    csv_path = Path(__file__).parent.parent / "data" / "logistics_dataset_v3.csv"
    df = pd.read_csv(csv_path).head(500)

    existing = {r[0] for r in db.query(Delivery.order_id).all()}
    df = df[~df["order_id"].astype(str).isin(existing)]

    ml_service.load_model()
    created = 0

    for _, row in df.iterrows():
        pred_data = row.to_dict()
        result = ml_service.predict(pred_data)

        db.add(Delivery(
            order_id=str(int(row["order_id"])),
            customer_id=int(row["customer_id"]),
            customer_lat=row["customer_lat"],
            customer_lon=row["customer_lon"],
            warehouse_lat=row["warehouse_lat"],
            warehouse_lon=row["warehouse_lon"],
            distance_km=row["distance_km"],
            delivery_zone=row["delivery_zone"],
            time_slot=row["time_slot"],
            day_of_week=row["day_of_week"],
            month=int(row["month"]),
            is_weekend=bool(row["is_weekend"]),
            is_holiday=bool(row["is_holiday"]),
            location_type=row["location_type"],
            building_type=row["building_type"],
            floor_number=int(row["floor_number"]),
            lift_available=bool(row["lift_available"]),
            payment_type=row["payment_type"],
            order_value=row["order_value"],
            package_weight=row["package_weight"],
            package_size=row["package_size"],
            weather=row["weather"],
            traffic_level=row["traffic_level"],
            customer_past_orders=int(row["customer_past_orders"]),
            past_success_rate=row["past_success_rate"],
            customer_cancellation_rate=row["customer_cancellation_rate"],
            customer_return_rate=row["customer_return_rate"],
            phone_reachable=bool(row["phone_reachable"]),
            customer_available=bool(row["customer_available"]),
            preferred_slot_match=bool(row["preferred_slot_match"]),
            otp_required=bool(row["otp_required"]),
            agent_experience_years=row["agent_experience_years"],
            agent_success_rate=row["agent_success_rate"],
            agent_daily_load=int(row["agent_daily_load"]),
            delivery_attempts=int(row["delivery_attempts"]),
            previous_failed_attempt_same_order=int(row["previous_failed_attempt_same_order"]),
            status=DeliveryStatus.PENDING,
            risk_score=result["risk_score"],
            risk_category=result["risk_category"],
        ))
        created += 1
        if created % 100 == 0:
            db.flush()

    db.commit()
    print(f"  Seeded {created} deliveries")


def main():
    print("Starting database seed...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users(db)
        seed_agents(db)
        seed_deliveries(db)
        print("Seed complete!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
