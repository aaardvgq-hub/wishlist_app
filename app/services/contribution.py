"""Contribution service: amount > 0, cap at target, progress %, optional minimum. Lock item for concurrency."""

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.money import progress_percent as money_progress_percent
from app.models.contribution import Contribution
from app.models.wish_item import WishItem
from app.repositories.contribution import ContributionRepository
from app.repositories.wish_item import WishItemRepository

_settings = get_settings()
logger = logging.getLogger(__name__)


class ContributionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._item_repo = WishItemRepository(session)
        self._contribution_repo = ContributionRepository(session)

    def _progress_percent_float(self, contributed: Decimal, target: Decimal) -> float:
        return float(money_progress_percent(contributed, target))

    async def contribute(
        self, item_id: UUID, anonymous_session_id: str, amount: Decimal
    ) -> tuple[Contribution | None, Decimal, Decimal, float, UUID | None, str | None]:
        """
        Add contribution if item exists, not deleted, allow_group_contribution, and
        amount > 0, sum + amount <= target_price. Uses SELECT FOR UPDATE on item for concurrent safety.
        Returns (contribution, contributed_total, target_price, progress_percent, wishlist_id, reject_reason).
        reject_reason is "fully_funded" when item is already at or over target; None on success.
        """
        item = await self._item_repo.get_by_id_for_update(item_id, include_deleted=False)
        if not item or not item.allow_group_contribution:
            return None, Decimal("0"), Decimal("0"), 0.0, None, None
        wishlist_id = item.wishlist_id
        target = item.target_price
        if amount <= 0:
            return None, Decimal("0"), target, 0.0, None, None
        if _settings.min_contribution_amount is not None:
            if amount < Decimal(str(_settings.min_contribution_amount)):
                return None, Decimal("0"), target, 0.0, None, None
        current = await self._contribution_repo.get_sum_by_item(item_id)
        if current >= target:
            logger.info("contribution_rejected", extra={"reason": "already_fully_funded", "item_id": str(item_id)})
            return None, current, target, self._progress_percent_float(current, target), None, "fully_funded"
        if current + amount > target:
            return None, current, target, self._progress_percent_float(current, target), None, None
        c = await self._contribution_repo.create(item_id, anonymous_session_id, amount)
        new_total = current + amount
        logger.info(
            "contribution_added",
            extra={"item_id": str(item_id), "wishlist_id": str(wishlist_id), "amount": str(amount), "new_total": str(new_total)},
        )
        return c, new_total, target, self._progress_percent_float(new_total, target), wishlist_id, None