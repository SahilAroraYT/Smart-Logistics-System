from sqlalchemy.orm import Session

from app.models.user import User
from app.services import auth_service


def create_user(db: Session, email: str, password: str, full_name: str, role: str) -> User:
    user = User(
        email=email,
        password_hash=auth_service.hash_password(password),
        full_name=full_name,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not auth_service.verify_password(password, user.password_hash):
        return None
    return user
