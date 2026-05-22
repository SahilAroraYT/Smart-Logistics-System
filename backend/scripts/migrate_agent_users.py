"""
Create user accounts for all delivery agents that don't have one.
Links each DeliveryAgent to a User so they can log in.
Credentials: agent{N}@logistics.com / agent123
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.user import User, Role
from app.models.agent import DeliveryAgent
from app.services.auth_service import hash_password


def main():
    db = SessionLocal()
    try:
        agents = db.query(DeliveryAgent).order_by(DeliveryAgent.id).all()
        all_agent_users = (
            db.query(User)
            .filter(User.role == Role.DELIVERY_AGENT)
            .order_by(User.id)
            .all()
        )
        used_user_ids = {u.id for u in all_agent_users}
        next_user_number = len(all_agent_users) + 1

        created = 0
        linked = 0

        for agent in agents:
            if agent.user_id:
                print(f"  Agent #{agent.id} \"{agent.name}\" already has user_id={agent.user_id}")
                continue

            # Find an unused email slot
            while True:
                email = f"agent{next_user_number}@logistics.com"
                existing = db.query(User).filter(User.email == email).first()
                if not existing:
                    break
                next_user_number += 1

            user = User(
                email=email,
                password_hash=hash_password("agent123"),
                full_name=agent.name,
                role=Role.DELIVERY_AGENT,
            )
            db.add(user)
            db.flush()

            agent.user_id = user.id
            created += 1
            next_user_number += 1
            print(f"  Created user {email} -> Agent #{agent.id} \"{agent.name}\"")
            linked += 1

        db.commit()
        print(f"\nDone: created {created} users, linked {linked} agents")

        agents_after = db.query(DeliveryAgent).order_by(DeliveryAgent.id).all()
        for a in agents_after:
            u = db.query(User).filter(User.id == a.user_id).first()
            email = u.email if u else "NONE"
            print(f"  Agent #{a.id} \"{a.name}\" -> {email}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
