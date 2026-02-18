"""Pydantic schemas for User."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Shared user fields."""

    email: EmailStr


class UserCreate(UserBase):
    """Payload for user registration."""

    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Payload for partial user update."""

    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8, max_length=128)


class UserInDB(UserBase):
    """User as stored (id + timestamps + is_active)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool = True
    created_at: datetime


class UserResponse(UserInDB):
    """User in API responses (no password)."""

    pass
