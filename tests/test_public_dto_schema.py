"""Assert public DTOs never expose owner-only or identity fields."""

import pytest

from app.schemas.wishlist import WishlistItemPublic, WishlistPublicResponse


def test_public_wishlist_response_has_no_owner_id() -> None:
    """WishlistPublicResponse must not expose owner_id (owner-only)."""
    assert "owner_id" not in WishlistPublicResponse.model_fields


def test_public_wishlist_response_has_no_created_at() -> None:
    """Public response omits created_at (owner context); we only care about share_token and event_date."""
    assert "created_at" not in WishlistPublicResponse.model_fields


def test_public_item_has_no_owner_only_fields() -> None:
    """WishlistItemPublic must not expose is_deleted or wishlist_id (owner edit view)."""
    fields = set(WishlistItemPublic.model_fields)
    assert "is_deleted" not in fields
    assert "wishlist_id" not in fields


def test_no_public_schema_has_anonymous_session_id() -> None:
    """No public-facing item or wishlist schema must expose contributor/reserver identity."""
    for model in (WishlistItemPublic, WishlistPublicResponse):
        assert "anonymous_session_id" not in model.model_fields
