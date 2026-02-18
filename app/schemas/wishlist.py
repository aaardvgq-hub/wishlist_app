"""Pydantic schemas for Wishlist."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WishlistBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    event_date: date | None = None
    is_public: bool = True


class WishlistCreate(WishlistBase):
    pass


class WishlistUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    event_date: date | None = None
    is_public: bool | None = None


class WishlistItemPublic(BaseModel):
    """Item as shown on public view (no owner-only fields)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    product_url: str | None
    image_url: str | None
    target_price: str
    allow_group_contribution: bool
    reserved: bool = False
    contributed_total: str = "0"
    contribution_progress_percent: float = 0.0


class WishlistResponse(WishlistBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    share_token: UUID
    created_at: datetime


class WishlistItemResponse(BaseModel):
    """Single item in wishlist (owner edit view)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    wishlist_id: UUID
    title: str
    description: str | None
    product_url: str | None
    image_url: str | None
    target_price: str
    allow_group_contribution: bool
    is_deleted: bool = False


class WishlistWithItemsResponse(WishlistResponse):
    """Wishlist with items for owner edit view."""

    items: list[WishlistItemResponse] = []


class WishlistPublicResponse(WishlistBase):
    """Public wishlist by share token (with items, no owner identity)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    share_token: UUID
    title: str
    description: str | None
    event_date: date | None
    event_date_passed: bool = False
    items: list[WishlistItemPublic] = []
