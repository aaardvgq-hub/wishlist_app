"""Reservation service: reserve (prevent double), cancel. Group mode allowed (override).

Transaction: reserve/cancel run inside the request session; get_db commits after the handler
returns. The partial unique index (reservations item_id WHERE cancelled_at IS NULL) enforces
one active reservation per item at DB level; concurrent inserts cause IntegrityError, which we handle.
"""

import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reservation import Reservation
from app.models.wish_item import WishItem
from app.repositories.reservation import ReservationRepository
from app.repositories.wish_item import WishItemRepository

logger = logging.getLogger(__name__)


class ReservationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._item_repo = WishItemRepository(session)
        self._reservation_repo = ReservationRepository(session)

    async def reserve(
        self, item_id: UUID, anonymous_session_id: str
    ) -> tuple[Reservation | None, UUID | None]:
        """
        Create reservation if item exists, not deleted, and no active reservation (any session).
        Group mode override: reserving is allowed even when allow_group_contribution is true.
        Returns (reservation, wishlist_id) or (None, None). IntegrityError from unique index
        (concurrent reserve) is caught and returns (None, None).
        """
        item = await self._item_repo.get_by_id(item_id, include_deleted=False)
        if not item:
            return None, None
        wishlist_id = item.wishlist_id
        active = await self._reservation_repo.get_active_by_item(item_id)
        if active:
            if active.anonymous_session_id == anonymous_session_id:
                return active, wishlist_id
            return None, None
        existing = await self._reservation_repo.get_by_item_and_session(
            item_id, anonymous_session_id
        )
        if existing and existing.cancelled_at is None:
            return existing, wishlist_id
        try:
            r = await self._reservation_repo.create(item_id, anonymous_session_id)
            logger.info(
                "reservation_created",
                extra={"item_id": str(item_id), "wishlist_id": str(wishlist_id), "reservation_id": str(r.id)},
            )
            return r, wishlist_id
        except IntegrityError:
            await self._session.rollback()
            logger.info("reservation_race_lost", extra={"item_id": str(item_id)})
            return None, None

    async def cancel(self, item_id: UUID, anonymous_session_id: str) -> tuple[bool, UUID | None]:
        """Cancel this session's reservation. Returns (True, wishlist_id) or (False, None)."""
        r = await self._reservation_repo.get_by_item_and_session(item_id, anonymous_session_id)
        if not r or r.cancelled_at is not None:
            return False, None
        item = await self._item_repo.get_by_id(item_id, include_deleted=False)
        wishlist_id = item.wishlist_id if item else None
        ok = await self._reservation_repo.cancel(r.id, anonymous_session_id)
        if ok:
            logger.info("reservation_cancelled", extra={"item_id": str(item_id), "wishlist_id": str(wishlist_id)})
        return ok, wishlist_id