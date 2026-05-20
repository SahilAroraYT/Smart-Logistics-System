import sys
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, SessionLocal, engine
from app.models.user import User, Role
from app.models.agent import DeliveryAgent, AgentStatus
from app.models.delivery import Delivery, DeliveryStatus
from app.models.warehouse import Warehouse
from app.services import auth_service, ml_service
from app.services.clustering_service import haversine_km


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


def seed_warehouses(db: Session):
    warehouses_data = [
        {"name": "Delhi North Hub", "street": "GT Karnal Road", "city": "Delhi", "pincode": "110033", "lat": 28.72, "lon": 77.12},
        {"name": "Gurgaon Hub", "street": "Golf Course Road", "city": "Gurgaon", "pincode": "122002", "lat": 28.46, "lon": 77.03},
        {"name": "Noida Hub", "street": "Sector 62", "city": "Noida", "pincode": "201301", "lat": 28.59, "lon": 77.33},
        {"name": "South Delhi Hub", "street": "Mehrauli Road", "city": "New Delhi", "pincode": "110030", "lat": 28.54, "lon": 77.20},
    ]
    created = 0
    for w in warehouses_data:
        if not db.query(Warehouse).filter(Warehouse.name == w["name"]).first():
            db.add(Warehouse(**w))
            created += 1
    db.commit()
    print(f"  Seeded {created} warehouses")


def seed_agents(db: Session):
    warehouses = db.query(Warehouse).all()
    if not warehouses:
        return

    # Delete existing agents for clean re-seed
    existing = db.query(DeliveryAgent).count()
    if existing:
        db.query(DeliveryAgent).delete()
        db.flush()

    user_agent_user = db.query(User).filter(User.role == Role.DELIVERY_AGENT).first()
    wh_user_idx = 0

    WH_SHORT = {w.id: w.name.split()[0] for w in warehouses}

    # Each warehouse: 2 bikes, 2 cars, 1 van
    wh_template = [
        ("bike", 0.002, 0.002, 0.90, 20),
        ("bike", -0.002, -0.002, 0.80, 20),
        ("car", 0.001, -0.001, 0.85, 30),
        ("car", -0.001, 0.001, 0.88, 30),
        ("van", 0.003, 0.000, 0.75, 40),
    ]

    created = 0
    for wh in warehouses:
        short = WH_SHORT.get(wh.id, f"W{wh.id}")
        for idx, (vtype, lat_off, lon_off, succ_rate, max_ld) in enumerate(wh_template):
            user_id = None
            name = f"{short}-{vtype.capitalize()}-{idx + 1}"

            # Link user to first agent at Delhi North Hub (wh 1)
            if wh.id == 1 and idx == 0 and user_agent_user:
                user_id = user_agent_user.id
                name = "Agent One"

            agent = DeliveryAgent(
                user_id=user_id,
                name=name,
                phone=f"98765{created + 1:05d}",
                vehicle_type=vtype,
                warehouse_id=wh.id,
                current_lat=wh.lat + lat_off,
                current_lon=wh.lon + lon_off,
                current_load=0,
                max_load=max_ld,
                success_rate=succ_rate,
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

    warehouses = db.query(Warehouse).all()

    ml_service.load_model()
    created = 0

    for _, row in df.iterrows():
        pred_data = row.to_dict()
        result = ml_service.predict(pred_data)

        nearest_wh_id = None
        if warehouses and row["customer_lat"] and row["customer_lon"]:
            nearest_wh = min(
                warehouses,
                key=lambda w: haversine_km(w.lat, w.lon, row["customer_lat"], row["customer_lon"]),
            )
            nearest_wh_id = nearest_wh.id

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
            warehouse_id=nearest_wh_id,
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
        seed_warehouses(db)
        seed_agents(db)
        seed_deliveries(db)
        print("Seed complete!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
