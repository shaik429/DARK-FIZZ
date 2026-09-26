"""Database queries for users and password resets. No business rules here."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PasswordReset, User


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def create(db: Session, name: str, email: str, password_hash: str, role: str = "staff") -> User:
    user = User(name=name, email=email.lower(), password_hash=password_hash, role=role)
    db.add(user)
    db.flush()
    return user


def latest_reset(db: Session, user_id: int) -> PasswordReset | None:
    return db.scalar(
        select(PasswordReset)
        .where(PasswordReset.user_id == user_id, PasswordReset.used_at.is_(None))
        .order_by(PasswordReset.id.desc())
        .limit(1)
    )


def add_reset(db: Session, reset: PasswordReset) -> None:
    db.add(reset)
    db.flush()
