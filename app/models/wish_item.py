"""WishItem model: single item in a wishlist, supports reservation and group contribution."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class WishItem(BaseModel):
    """
    Item in a wishlist. Soft-deleted via is_deleted.
    Can be reserved (one reservation per item) and/or support group contributions.
    """

    __tablename__ = "wish_items"

    wishlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wishlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    target_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
    )
    allow_group_contribution: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    wishlist: Mapped["Wishlist"] = relationship("Wishlist", back_populates="items")
    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation",
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    contributions: Mapped[list["Contribution"]] = relationship(
        "Contribution",
        back_populates="item",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"WishItem(id={self.id!r}, title={self.title!r}, "
            f"wishlist_id={self.wishlist_id!r}, is_deleted={self.is_deleted})"
        )
