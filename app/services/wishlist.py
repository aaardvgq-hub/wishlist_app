"""Wishlist service: list, get, get by share token, create. Single place for public/owner DTOs."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.money import progress_percent
from app.models.wishlist import Wishlist
from app.repositories.contribution import ContributionRepository
from app.repositories.reservation import ReservationRepository
from app.repositories.wishlist import WishlistRepository
from app.schemas.wishlist import (
    WishlistCreate,
    WishlistItemPublic,
    WishlistItemResponse,
    WishlistPublicResponse,
    WishlistWithItemsResponse,
)


class WishlistService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = WishlistRepository(session)
        self._reservation_repo = ReservationRepository(session)
        self._contribution_repo = ContributionRepository(session)

    async def list_by_owner(self, owner_id: UUID) -> list[Wishlist]:
        return await self._repo.list_by_owner(owner_id)

    async def get_by_id_for_owner(self, wishlist_id: UUID, owner_id: UUID) -> Wishlist | None:
        return await self._repo.get_by_id_and_owner(wishlist_id, owner_id)

    async def get_by_share_token(self, token: UUID) -> Wishlist | None:
        return await self._repo.get_by_share_token(token)

    async def create(self, owner_id: UUID, payload: WishlistCreate) -> Wishlist:
        return await self._repo.create(
            owner_id,
            title=payload.title,
            description=payload.description,
            event_date=payload.event_date,
            is_public=payload.is_public,
        )

    async def get_public_dto(self, token: UUID) -> WishlistPublicResponse | None:
        """Build public wishlist DTO (no owner identity). O(1) query group: wishlist+items, sums, active reservations."""
        w = await self._repo.get_by_share_token_with_items(token)
        if not w or not w.is_public:
            return None
        visible_items = [i for i in w.items if not i.is_deleted]
        if not visible_items:
            event_passed = w.event_date is not None and w.event_date < date.today()
            return WishlistPublicResponse(
                id=w.id,
                share_token=w.share_token,
                title=w.title,
                description=w.description,
                event_date=w.event_date,
                is_public=w.is_public,
                event_date_passed=event_passed,
                items=[],
            )
        item_ids = [i.id for i in visible_items]
        sums_map = await self._contribution_repo.get_sums_by_item_ids(item_ids)
        active_ids = await self._reservation_repo.get_active_reservation_item_ids(item_ids)
        items_out: list[WishlistItemPublic] = []
        for item in visible_items:
            total: Decimal = sums_map.get(item.id, Decimal("0"))
            target: Decimal = item.target_price
            pct_decimal = progress_percent(total, target)
            items_out.append(
                WishlistItemPublic(
                    id=item.id,
                    title=item.title,
                    description=item.description,
                    product_url=item.product_url,
                    image_url=item.image_url,
                    target_price=str(item.target_price),
                    allow_group_contribution=item.allow_group_contribution,
                    reserved=item.id in active_ids,
                    contributed_total=str(total),
                    contribution_progress_percent=float(pct_decimal),
                )
            )
        event_passed = w.event_date is not None and w.event_date < date.today()
        return WishlistPublicResponse(
            id=w.id,
            share_token=w.share_token,
            title=w.title,
            description=w.description,
            event_date=w.event_date,
            is_public=w.is_public,
            event_date_passed=event_passed,
            items=items_out,
        )

    async def get_with_items_for_owner(
        self, wishlist_id: UUID, owner_id: UUID
    ) -> WishlistWithItemsResponse | None:
        """Build wishlist-with-items DTO for owner. Returns None if not found or not owner."""
        w = await self._repo.get_by_id_and_owner(wishlist_id, owner_id)
        if not w:
            return None
        await self._session.refresh(w, ["items"])
        items = [
            WishlistItemResponse(
                id=it.id,
                wishlist_id=it.wishlist_id,
                title=it.title,
                description=it.description,
                product_url=it.product_url,
                image_url=it.image_url,
                target_price=str(it.target_price),
                allow_group_contribution=it.allow_group_contribution,
                is_deleted=it.is_deleted,
            )
            for it in w.items
        ]
        return WishlistWithItemsResponse(
            id=w.id,
            owner_id=w.owner_id,
            share_token=w.share_token,
            title=w.title,
            description=w.description,
            event_date=w.event_date,
            is_public=w.is_public,
            created_at=w.created_at,
            items=items,
        )
