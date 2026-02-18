"""Reservation repository: create, get active, cancel."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.reservation import Reservation


class ReservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, item_id: UUID, anonymous_session_id: str) -> Reservation:
        """Create a new reservation."""
        r = Reservation(item_id=item_id, anonymous_session_id=anonymous_session_id)
        self._session.add(r)
        await self._session.flush()
        await self._session.refresh(r)
        return r

    async def get_active_by_item(self, item_id: UUID) -> Reservation | None:
        """Get the single active (non-cancelled) reservation for an item, if any."""
        result = await self._session.execute(
            select(Reservation)
            .where(Reservation.item_id == item_id)
            .where(Reservation.cancelled_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_active_reservation_item_ids(self, item_ids: list[UUID]) -> set[UUID]:
        """Item ids that have an active reservation (one query)."""
        if not item_ids:
            return set()
        result = await self._session.execute(
            select(Reservation.item_id)
            .where(Reservation.item_id.in_(item_ids))
            .where(Reservation.cancelled_at.is_(None))
            .distinct()
        )
        return {row[0] for row in result.all()}

    async def get_by_item_and_session(
        self, item_id: UUID, anonymous_session_id: str
    ) -> Reservation | None:
        """Get reservation for this item by this session (any status)."""
        result = await self._session.execute(
            select(Reservation).where(
                Reservation.item_id == item_id,
                Reservation.anonymous_session_id == anonymous_session_id,
            )
        )
        return result.scalar_one_or_none()

    async def cancel(self, reservation_id: UUID, anonymous_session_id: str) -> bool:
        """Set cancelled_at for this reservation if it belongs to this session. Returns True if updated."""
        from datetime import UTC, datetime

        result = await self._session.execute(
            select(Reservation).where(
                Reservation.id == reservation_id,
                Reservation.anonymous_session_id == anonymous_session_id,
                Reservation.cancelled_at.is_(None),
            )
        )
        r = result.scalar_one_or_none()
        if not r:
            return False
        r.cancelled_at = datetime.now(UTC)
        await self._session.flush()
        return True
