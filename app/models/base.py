"""Base model with UUID primary key and created_at."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all models."""

    pass


class TimestampMixin:
    """Mixin adding created_at (and optional updated_at) in UTC."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class UUIDPrimaryMixin:
    """Mixin adding UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class BaseModel(Base, UUIDPrimaryMixin, TimestampMixin):
    """
    Abstract base model: UUID id + created_at.
    All app models should inherit from this (or from Base + mixins).
    """

    __abstract__ = True
