import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PASSWORD_RULE = "Password must be at least 8 characters with at least 1 letter and 1 number."


def check_password(value: str) -> str:
    if len(value) < 8 or not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise ValueError(PASSWORD_RULE)
    return value


class SignupIn(BaseModel):
    name: str = Field(max_length=100)
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty.")
        return v.strip()

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return check_password(v)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    email: EmailStr
    otp: str = Field(pattern=r"^\d{6}$")
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return check_password(v)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class MessageOut(BaseModel):
    message: str
