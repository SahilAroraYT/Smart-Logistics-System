import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, SessionLocal, engine
from app.models.user import User, Role
from app.models.agent import DeliveryAgent, AgentStatus
from app.models.delivery import Delivery, DeliveryStatus
from app.models.warehouse import Warehouse
from app.models.route import Route, RouteStop
from app.models.assignment import AssignmentSession, SessionDelivery
from app.services import auth_service, ml_service
from app.services.clustering_service import haversine_km


def seed_users(db: Session):
    users = [
        ("admin@logistics.com", "admin123", "System Admin", Role.ADMIN),
        ("manager@logistics.com", "manager123", "Operations Manager", Role.OPERATIONS_MANAGER),
        ("supervisor@logistics.com", "supervisor123", "Delivery Supervisor", Role.DELIVERY_SUPERVISOR),
    ]
    for email, password, name, role in users:
        if not db.query(User).filter(User.email == email).first():
            db.add(User(
                email=email,
                password_hash=auth_service.hash_password(password),
                full_name=name,
                role=role,
            ))

    for i in range(1, 21):
        email = f"agent{i}@logistics.com"
        if not db.query(User).filter(User.email == email).first():
            db.add(User(
                email=email,
                password_hash=auth_service.hash_password("agent123"),
                full_name=f"Agent {i}",
                role=Role.DELIVERY_AGENT,
            ))

    ludhiana_users = [
        ("ldhbike1@logistics.com", "ldhbike1", "Ludhiana Bike 1"),
        ("ldhbike2@logistics.com", "ldhbike2", "Ludhiana Bike 2"),
        ("ldhcar3@logistics.com", "ldhcar3", "Ludhiana Car 3"),
        ("ldhcar4@logistics.com", "ldhcar4", "Ludhiana Car 4"),
        ("ldhvan5@logistics.com", "ldhvan5", "Ludhiana Van 5"),
    ]
    for email, password, name in ludhiana_users:
        if not db.query(User).filter(User.email == email).first():
            db.add(User(
                email=email,
                password_hash=auth_service.hash_password(password),
                full_name=name,
                role=Role.DELIVERY_AGENT,
            ))

    db.commit()
    print("  Seeded 28 users (3 staff + 25 agents)")


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
    # Add Ludhiana warehouse if not exists
    if not db.query(Warehouse).filter(Warehouse.name == "Ludhiana Warehouse").first():
        db.add(Warehouse(
            name="Ludhiana Warehouse",
            street="GT Road",
            city="Ludhiana",
            pincode="141001",
            lat=30.87381,
            lon=75.84182,
        ))
        created += 1
    db.commit()
    print(f"  Seeded {created} warehouses")


def seed_agents(db: Session):
    warehouses = db.query(Warehouse).all()
    if not warehouses:
        return

    # Clear dependent data before deleting agents
    db.query(RouteStop).delete()
    db.query(Route).delete()
    db.query(SessionDelivery).delete()
    db.query(AssignmentSession).delete()
    db.query(Delivery).delete()
    db.flush()

    existing = db.query(DeliveryAgent).count()
    if existing:
        db.query(DeliveryAgent).delete()
        db.flush()

    agent_users = (
        db.query(User)
        .filter(User.role == Role.DELIVERY_AGENT)
        .order_by(User.id)
        .all()
    )

    WH_SHORT = {w.id: w.name.split()[0] for w in warehouses}

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
            user_id = agent_users[created].id if created < len(agent_users) else None
            name = "Agent One" if created == 0 else f"{short}-{vtype.capitalize()}-{idx + 1}"

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

    warehouses = db.query(Warehouse).all()
    if not warehouses:
        print("  No warehouses found, skipping deliveries")
        return

    rng = np.random.default_rng(42)

    ml_service.load_model()
    created = 0

    for idx, (_, row) in enumerate(df.iterrows()):
        wh = warehouses[idx % len(warehouses)]

        lat_off = rng.uniform(0.01, 0.15) * (1 if rng.random() < 0.5 else -1)
        lon_off = rng.uniform(0.01, 0.15) * (1 if rng.random() < 0.5 else -1)
        cust_lat = round(wh.lat + lat_off, 6)
        cust_lon = round(wh.lon + lon_off, 6)
        dist = round(haversine_km(wh.lat, wh.lon, cust_lat, cust_lon), 2)

        pred_data = row.to_dict()
        try:
            result = ml_service.predict(pred_data)
        except Exception:
            result = {"risk_score": 50.0, "risk_category": "MEDIUM"}

        db.add(Delivery(
            order_id=str(int(row["order_id"])),
            customer_id=int(row["customer_id"]),
            customer_name=f"Customer-{int(row['customer_id'])}",
            customer_lat=cust_lat,
            customer_lon=cust_lon,
            warehouse_lat=wh.lat,
            warehouse_lon=wh.lon,
            distance_km=dist,
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
            warehouse_id=wh.id,
        ))
        created += 1
        if created % 100 == 0:
            db.flush()

    db.commit()
    print(f"  Seeded {created} deliveries (≈{created // len(warehouses)} per warehouse)")


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
