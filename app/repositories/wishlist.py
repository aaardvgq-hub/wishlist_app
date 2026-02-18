"""Wishlist repository: persistence and lookups."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.wishlist import Wishlist


class WishlistRepository:
    """Repository for Wishlist CRUD and ownership checks."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, wishlist_id: UUID) -> Wishlist | None:
        """Fetch wishlist by primary key."""
        result = await self._session.execute(select(Wishlist).where(Wishlist.id == wishlist_id))
        return result.scalar_one_or_none()

    async def get_by_id_and_owner(self, wishlist_id: UUID, owner_id: UUID) -> Wishlist | None:
        """Fetch wishlist by id only if owned by given user."""
        result = await self._session.execute(
            select(Wishlist).where(Wishlist.id == wishlist_id, Wishlist.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def list_by_owner(self, owner_id: UUID) -> list[Wishlist]:
        """List wishlists owned by user."""
        result = await self._session.execute(
            select(Wishlist).where(Wishlist.owner_id == owner_id).order_by(Wishlist.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_share_token(self, token: UUID) -> Wishlist | None:
        """Fetch wishlist by share_token (for public link)."""
        result = await self._session.execute(select(Wishlist).where(Wishlist.share_token == token))
        return result.scalar_one_or_none()

    async def get_by_share_token_with_items(self, token: UUID) -> Wishlist | None:
        """Fetch wishlist by share_token with items eagerly loaded (O(1) query group for public DTO)."""
        result = await self._session.execute(
            select(Wishlist)
            .where(Wishlist.share_token == token)
            .options(selectinload(Wishlist.items))
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        owner_id: UUID,
        *,
        title: str,
        description: str | None = None,
        event_date: date | None = None,
        is_public: bool = True,
    ) -> Wishlist:
        w = Wishlist(
            owner_id=owner_id,
            title=title,
            description=description,
            event_date=event_date,
            is_public=is_public,
        )
        self._session.add(w)
        await self._session.flush()
        await self._session.refresh(w)
        return w
