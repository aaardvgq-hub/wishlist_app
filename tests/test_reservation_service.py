"""Unit tests for reservation service: double reserve, IntegrityError handling."""

from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.reservation import Reservation
from app.models.wish_item import WishItem
from app.services.reservation import ReservationService


@pytest.mark.asyncio
async def test_reserve_returns_none_when_active_reservation_by_other_session() -> None:
    """When another session already has an active reservation, reserve returns (None, None)."""
    item_id = uuid4()
    wishlist_id = uuid4()
    existing = Reservation(
        id=uuid4(),
        item_id=item_id,
        anonymous_session_id="other-session",
        cancelled_at=None,
    )
    mock_session = pytest.importorskip("unittest.mock").AsyncMock()
    mock_item_repo = pytest.importorskip("unittest.mock").AsyncMock()
    mock_reservation_repo = pytest.importorskip("unittest.mock").AsyncMock()

    mock_item_repo.get_by_id = pytest.importorskip("unittest.mock").AsyncMock(
        return_value=WishItem(
            id=item_id,
            wishlist_id=wishlist_id,
            title="Item",
            target_price=100,
            allow_group_contribution=False,
            is_deleted=False,
        )
    )
    mock_reservation_repo.get_active_by_item = pytest.importorskip("unittest.mock").AsyncMock(
        return_value=existing
    )

    class MockSession:
        async def rollback(self):
            pass

    svc = ReservationService(MockSession())
    svc._item_repo = mock_item_repo
    svc._reservation_repo = mock_reservation_repo
    svc._session = MockSession()

    r, wid = await svc.reserve(item_id, "my-session")
    assert r is None
    assert wid is None


@pytest.mark.asyncio
async def test_reserve_handles_integrity_error_returns_none() -> None:
    """When create raises IntegrityError (race: another active reservation), return (None, None)."""
    from unittest.mock import AsyncMock, MagicMock

    item_id = uuid4()
    wishlist_id = uuid4()
    mock_item_repo = MagicMock()
    mock_item_repo.get_by_id = AsyncMock(
        return_value=WishItem(
            id=item_id,
            wishlist_id=wishlist_id,
            title="Item",
            target_price=100,
            allow_group_contribution=False,
            is_deleted=False,
        )
    )
    mock_reservation_repo = MagicMock()
    mock_reservation_repo.get_active_by_item = AsyncMock(return_value=None)
    mock_reservation_repo.get_by_item_and_session = AsyncMock(return_value=None)
    mock_reservation_repo.create = AsyncMock(side_effect=IntegrityError("", "", None))

    class MockSession:
        async def rollback(self):
            pass

    svc = ReservationService(MockSession())
    svc._item_repo = mock_item_repo
    svc._reservation_repo = mock_reservation_repo
    svc._session = MockSession()

    r, wid = await svc.reserve(item_id, "my-session")
    assert r is None
    assert wid is None
