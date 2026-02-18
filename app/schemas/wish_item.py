"""Pydantic schemas for WishItem and product preview."""

from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WishItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=10000)
    product_url: str | None = Field(None, max_length=2048)
    image_url: str | None = Field(None, max_length=2048)
    target_price: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    allow_group_contribution: bool = False


class WishItemCreate(WishItemBase):
    """Payload for creating a wish item (wishlist_id required)."""

    wishlist_id: UUID


class WishItemUpdate(BaseModel):
    """Partial update for PATCH."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    product_url: str | None = Field(None, max_length=2048)
    image_url: str | None = Field(None, max_length=2048)
    target_price: Decimal | None = Field(None, ge=Decimal("0"))
    allow_group_contribution: bool | None = None


class WishItemResponse(WishItemBase):
    """Wish item in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    wishlist_id: UUID
    is_deleted: bool = False


class ProductPreviewRequest(BaseModel):
    """Input for product URL auto-fill."""

    product_url: str = Field(..., max_length=2048)


class ProductPreview(BaseModel):
    """Structured product preview from URL (og:title, og:image, price, title fallback)."""

    title: str | None = None
    image_url: str | None = None
    price: Decimal | None = None
    product_url: str | None = None
    preview_quality: Literal["full", "partial", "minimal"] = "minimal"
    missing_fields: list[str] = Field(default_factory=list, description="Fields we could not extract (title, image_url, price)")
