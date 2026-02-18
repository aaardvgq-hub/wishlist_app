"""Pydantic schemas for auth endpoints."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Email + password for registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Email + password for login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenMessage(BaseModel):
    """Generic message when tokens are set via httpOnly cookies (no token in body)."""

    message: str = "ok"
