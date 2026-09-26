from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.auth import (
    ForgotPasswordIn,
    LoginIn,
    MessageOut,
    ResetPasswordIn,
    SignupIn,
    TokenOut,
    UserOut,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=201)
def signup(body: SignupIn, db: Session = Depends(get_db)):
    return auth_service.signup(db, body.name, body.email, body.password)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    token, user = auth_service.login(db, body.email, body.password)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/forgot-password", response_model=MessageOut)
def forgot_password(body: ForgotPasswordIn, db: Session = Depends(get_db)):
    auth_service.forgot_password(db, body.email)
    return {"message": "If this email is registered, an OTP has been sent."}


@router.post("/reset-password", response_model=MessageOut)
def reset_password(body: ResetPasswordIn, db: Session = Depends(get_db)):
    auth_service.reset_password(db, body.email, body.otp, body.new_password)
    return {"message": "Password updated. Please log in."}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
