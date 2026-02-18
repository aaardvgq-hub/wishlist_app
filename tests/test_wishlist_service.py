"""Unit tests for wishlist service: permission and public DTO."""

from uuid import uuid4

import pytest

from app.services.wishlist import WishlistService


@pytest.mark.asyncio
async def test_get_with_items_for_owner_returns_none_when_not_owner() -> None:
    """When wishlist does not exist or user is not owner, returns None."""
    from unittest.mock import AsyncMock, MagicMock

    mock_repo = MagicMock()
    mock_repo.get_by_id_and_owner = AsyncMock(return_value=None)

    class MockSession:
        pass

    svc = WishlistService(MockSession())
    svc._repo = mock_repo
    svc._reservation_repo = MagicMock()
    svc._contribution_repo = MagicMock()

    result = await svc.get_with_items_for_owner(uuid4(), uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_public_dto_returns_none_for_invalid_token() -> None:
    """When share token has no wishlist or not public, get_public_dto returns None."""
    from unittest.mock import AsyncMock, MagicMock

    mock_repo = MagicMock()
    mock_repo.get_by_share_token_with_items = AsyncMock(return_value=None)

    class MockSession:
        pass

    svc = WishlistService(MockSession())
    svc._repo = mock_repo
    svc._reservation_repo = MagicMock()
    svc._contribution_repo = MagicMock()

    result = await svc.get_public_dto(uuid4())
    assert result is None
