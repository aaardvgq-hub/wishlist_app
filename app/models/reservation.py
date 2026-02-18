"""Reservation model: anonymous reservation of a wish item."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Reservation(BaseModel):
    """
    Reservation of an item by an anonymous viewer (session id).
    cancelled_at set for soft cancel; owner must not see anonymous_session_id.
    """

    __tablename__ = "reservations"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wish_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    anonymous_session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    item: Mapped["WishItem"] = relationship("WishItem", back_populates="reservations")

    def __repr__(self) -> str:
        return (
            f"Reservation(id={self.id!r}, item_id={self.item_id!r}, "
            f"cancelled_at={self.cancelled_at!r})"
        )
