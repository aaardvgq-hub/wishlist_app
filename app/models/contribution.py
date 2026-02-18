"""Contribution model: anonymous monetary contribution to an item."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Contribution(BaseModel):
    """
    Contribution toward an item by an anonymous viewer (session id).
    Owner must not see anonymous_session_id or who contributed how much.
    """

    __tablename__ = "contributions"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wish_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    anonymous_session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    item: Mapped["WishItem"] = relationship("WishItem", back_populates="contributions")

    def __repr__(self) -> str:
        return f"Contribution(id={self.id!r}, item_id={self.item_id!r}, amount={self.amount})"
