"""Pydantic schemas for auth endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, EmailStr, Field

if TYPE_CHECKING:
    from app.models.user import User


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


class AuthUserResponse(BaseModel):
    """User + access_token for login/register; frontend can use token in Authorization header when cookies are blocked (cross-origin)."""

    id: str
    email: str
    is_active: bool = True
    created_at: str
    access_token: str

    @classmethod
    def from_user_and_token(cls, user: User, access_token: str) -> AuthUserResponse:
        return cls(
            id=str(user.id),
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            access_token=access_token,
        )
