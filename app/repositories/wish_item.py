"""WishItem repository: persistence and soft delete."""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wishlist import Wishlist
from app.models.wish_item import WishItem


class WishItemRepository:
    """Repository for WishItem CRUD; soft delete via is_deleted."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        wishlist_id: UUID,
        *,
        title: str,
        description: str | None = None,
        product_url: str | None = None,
        image_url: str | None = None,
        target_price: str | float = "0",
        allow_group_contribution: bool = False,
    ) -> WishItem:
        """Create a new wish item."""
        from decimal import Decimal

        item = WishItem(
            wishlist_id=wishlist_id,
            title=title,
            description=description,
            product_url=product_url,
            image_url=image_url,
            target_price=Decimal(str(target_price)),
            allow_group_contribution=allow_group_contribution,
        )
        self._session.add(item)
        await self._session.flush()
        await self._session.refresh(item)
        return item

    async def get_by_id(self, item_id: UUID, include_deleted: bool = False) -> WishItem | None:
        """Fetch item by id; by default exclude soft-deleted."""
        q = select(WishItem).where(WishItem.id == item_id)
        if not include_deleted:
            q = q.where(WishItem.is_deleted.is_(False))
        result = await self._session.execute(q)
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, item_id: UUID, include_deleted: bool = False) -> WishItem | None:
        """Fetch item by id with row lock (SELECT FOR UPDATE) for contribution concurrency."""
        q = (
            select(WishItem)
            .where(WishItem.id == item_id)
            .with_for_update()
        )
        if not include_deleted:
            q = q.where(WishItem.is_deleted.is_(False))
        result = await self._session.execute(q)
        return result.scalar_one_or_none()

    async def get_by_id_for_owner(self, item_id: UUID, owner_id: UUID) -> WishItem | None:
        """Fetch item by id only if its wishlist is owned by owner_id (include deleted for PATCH/DELETE)."""
        result = await self._session.execute(
            select(WishItem)
            .join(Wishlist, WishItem.wishlist_id == Wishlist.id)
            .where(WishItem.id == item_id, Wishlist.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        item_id: UUID,
        *,
        title: str | None = None,
        description: str | None = None,
        product_url: str | None = None,
        image_url: str | None = None,
        target_price: str | float | None = None,
        allow_group_contribution: bool | None = None,
    ) -> WishItem | None:
        """Update item by id; returns updated item or None if not found."""
        from decimal import Decimal

        values: dict = {}
        if title is not None:
            values["title"] = title
        if description is not None:
            values["description"] = description
        if product_url is not None:
            values["product_url"] = product_url
        if image_url is not None:
            values["image_url"] = image_url
        if target_price is not None:
            values["target_price"] = Decimal(str(target_price))
        if allow_group_contribution is not None:
            values["allow_group_contribution"] = allow_group_contribution
        if not values:
            result = await self._session.execute(select(WishItem).where(WishItem.id == item_id))
            return result.scalar_one_or_none()
        await self._session.execute(update(WishItem).where(WishItem.id == item_id).values(**values))
        await self._session.flush()
        result = await self._session.execute(select(WishItem).where(WishItem.id == item_id))
        item = result.scalar_one_or_none()
        if item:
            await self._session.refresh(item)
        return item

    async def soft_delete(self, item_id: UUID) -> bool:
        """Mark item as deleted. Returns True if a row was updated."""
        result = await self._session.execute(
            update(WishItem).where(WishItem.id == item_id).values(is_deleted=True)
        )
        return result.rowcount > 0
