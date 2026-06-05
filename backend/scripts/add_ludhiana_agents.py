"""
Add 5 delivery agents (2 bike, 2 car, 1 van) for the Ludhiana warehouse.
Credentials: ldh{type}{n}@logistics.com / ldh{type}{n}
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.user import User, Role
from app.models.agent import DeliveryAgent, AgentStatus
from app.services.auth_service import hash_password


LUDHIANA_WAREHOUSE_ID = 5
LUDHIANA_LAT = 30.87381
LUDHIANA_LON = 75.84182

AGENTS = [
    {"name": "Ludhiana-Bike-1", "vtype": "bike", "lat_off": 0.002, "lon_off": 0.002, "succ": 0.90, "max_ld": 20, "login": "ldhbike1", "phone_suffix": "0021"},
    {"name": "Ludhiana-Bike-2", "vtype": "bike", "lat_off": -0.002, "lon_off": -0.002, "succ": 0.80, "max_ld": 20, "login": "ldhbike2", "phone_suffix": "0022"},
    {"name": "Ludhiana-Car-3", "vtype": "car", "lat_off": 0.001, "lon_off": -0.001, "succ": 0.85, "max_ld": 30, "login": "ldhcar1", "phone_suffix": "0023"},
    {"name": "Ludhiana-Car-4", "vtype": "car", "lat_off": -0.001, "lon_off": 0.001, "succ": 0.88, "max_ld": 30, "login": "ldhcar2", "phone_suffix": "0024"},
    {"name": "Ludhiana-Van-5", "vtype": "van", "lat_off": 0.003, "lon_off": 0.000, "succ": 0.75, "max_ld": 40, "login": "ldhvan1", "phone_suffix": "0025"},
]


def main():
    db = SessionLocal()
    try:
        created_users = 0
        created_agents = 0

        for a in AGENTS:
            email = f"{a['login']}@logistics.com"

            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                print(f"  User {email} already exists — skipping")
                continue

            user = User(
                email=email,
                password_hash=hash_password(a["login"]),
                full_name=a["name"],
                role=Role.DELIVERY_AGENT,
            )
            db.add(user)
            db.flush()
            created_users += 1

            existing_agent = db.query(DeliveryAgent).filter(
                DeliveryAgent.user_id == user.id
            ).first()
            if existing_agent:
                print(f"  Agent for user {email} already exists — skipping")
                continue

            agent = DeliveryAgent(
                user_id=user.id,
                name=a["name"],
                phone=f"98765{a['phone_suffix']}",
                vehicle_type=a["vtype"],
                warehouse_id=LUDHIANA_WAREHOUSE_ID,
                current_lat=LUDHIANA_LAT + a["lat_off"],
                current_lon=LUDHIANA_LON + a["lon_off"],
                current_load=0,
                max_load=a["max_ld"],
                success_rate=a["succ"],
                is_available=True,
                status=AgentStatus.AVAILABLE,
            )
            db.add(agent)
            created_agents += 1
            print(f"  Created user {email} / {a['login']} -> Agent \"{a['name']}\"")

        db.commit()
        print(f"\nDone: {created_users} users + {created_agents} agents created")

        print("\nNew agents:")
        for a in db.query(DeliveryAgent).filter(
            DeliveryAgent.warehouse_id == LUDHIANA_WAREHOUSE_ID
        ).all():
            u = db.query(User).filter(User.id == a.user_id).first()
            email = u.email if u else "NONE"
            print(f"  Agent #{a.id} \"{a.name}\" ({a.vehicle_type}) -> {email}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
