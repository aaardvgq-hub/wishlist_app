"""Contribution repository: create, sum by item, batch sums for N+1 avoidance."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contribution import Contribution


class ContributionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, item_id: UUID, anonymous_session_id: str, amount: Decimal) -> Contribution:
        """Create a new contribution."""
        c = Contribution(item_id=item_id, anonymous_session_id=anonymous_session_id, amount=amount)
        self._session.add(c)
        await self._session.flush()
        await self._session.refresh(c)
        return c

    async def get_sum_by_item(self, item_id: UUID) -> Decimal:
        """Total contributed amount for an item."""
        result = await self._session.execute(
            select(func.coalesce(func.sum(Contribution.amount), 0)).where(
                Contribution.item_id == item_id
            )
        )
        row = result.scalar_one_or_none()
        return Decimal(str(row)) if row is not None else Decimal("0")

    async def get_sums_by_item_ids(self, item_ids: list[UUID]) -> dict[UUID, Decimal]:
        """Total contributed per item for given ids (one query). Returns 0 for missing."""
        if not item_ids:
            return {}
        result = await self._session.execute(
            select(Contribution.item_id, func.sum(Contribution.amount))
            .where(Contribution.item_id.in_(item_ids))
            .group_by(Contribution.item_id)
        )
        out = {row[0]: Decimal(str(row[1])) for row in result.all()}
        for iid in item_ids:
            if iid not in out:
                out[iid] = Decimal("0")
        return out