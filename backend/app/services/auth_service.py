"""Signup, login and OTP password reset rules."""

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core import security
from app.core.errors import AppError
from app.models import PasswordReset, User
from app.repositories import user_repository as users
from app.services import email_service

OTP_MINUTES = 10
OTP_MAX_ATTEMPTS = 5


def invalid_login() -> AppError:
    return AppError(401, "INVALID_CREDENTIALS", "Email or password is incorrect.")


def now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)  # stored as naive UTC


def signup(db: Session, name: str, email: str, password: str) -> User:
    if users.get_by_email(db, email):
        raise AppError(409, "EMAIL_ALREADY_EXISTS", "An account with this email already exists.")
    user = users.create(db, name, email, security.hash_password(password), role="staff")
    db.commit()
    return user


def login(db: Session, email: str, password: str) -> tuple[str, User]:
    user = users.get_by_email(db, email)
    # Same answer for unknown email and wrong password, so emails can't be guessed.
    if user is None or not security.verify_password(password, user.password_hash):
        raise invalid_login()
    return security.create_access_token(user), user


def forgot_password(db: Session, email: str) -> None:
    user = users.get_by_email(db, email)
    if user is None:
        return  # don't reveal whether the email is registered
    otp = f"{secrets.randbelow(1_000_000):06d}"
    users.add_reset(
        db,
        PasswordReset(
            user_id=user.id,
            otp_hash=security.hash_password(otp),
            expires_at=now() + timedelta(minutes=OTP_MINUTES),
            attempts=0,
        ),
    )
    db.commit()
    email_service.send_otp(user.email, otp)


def reset_password(db: Session, email: str, otp: str, new_password: str) -> None:
    user = users.get_by_email(db, email)
    reset = users.latest_reset(db, user.id) if user else None
    if reset is None:
        raise AppError(400, "INVALID_OTP", "The code is incorrect. Request a new one.")
    if reset.attempts >= OTP_MAX_ATTEMPTS:
        raise AppError(429, "TOO_MANY_ATTEMPTS", "Too many wrong codes. Request a new one.")
    if reset.expires_at < now():
        raise AppError(400, "OTP_EXPIRED", "This code has expired. Request a new one.")
    if not security.verify_password(otp, reset.otp_hash):
        reset.attempts += 1
        db.commit()
        raise AppError(400, "INVALID_OTP", "The code is incorrect.")
    user.password_hash = security.hash_password(new_password)
    reset.used_at = now()
    db.commit()
