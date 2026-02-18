"""Unit tests for contribution service: over-contribution rejected."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.wish_item import WishItem
from app.services.contribution import ContributionService


@pytest.mark.asyncio
async def test_contribute_over_target_returns_none() -> None:
    """When amount would exceed target price, contribute returns (None, ...)."""
    from unittest.mock import AsyncMock, MagicMock

    item_id = uuid4()
    wishlist_id = uuid4()
    item = WishItem(
        id=item_id,
        wishlist_id=wishlist_id,
        title="Item",
        target_price=Decimal("100"),
        allow_group_contribution=True,
        is_deleted=False,
    )
    mock_item_repo = MagicMock()
    mock_item_repo.get_by_id_for_update = AsyncMock(return_value=item)
    mock_contribution_repo = MagicMock()
    mock_contribution_repo.get_sum_by_item = AsyncMock(return_value=Decimal("95"))

    class MockSession:
        pass

    svc = ContributionService(MockSession())
    svc._item_repo = mock_item_repo
    svc._contribution_repo = mock_contribution_repo

    # 10 would make total 105 > 100
    result = await svc.contribute(item_id, "session-1", Decimal("10"))
    contribution, total, target, progress, wid, reject_reason = result
    assert contribution is None
    assert total == Decimal("95")
    assert target == Decimal("100")
    assert wid is None
    assert reject_reason is None
