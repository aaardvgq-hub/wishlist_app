"""WishItem service: business logic and ownership checks."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wish_item import WishItem
from app.repositories.wish_item import WishItemRepository
from app.repositories.wishlist import WishlistRepository
from app.schemas.wish_item import WishItemCreate, WishItemUpdate


class WishItemService:
    """Create, update, soft-delete wish items; enforce wishlist ownership."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._item_repo = WishItemRepository(session)
        self._wishlist_repo = WishlistRepository(session)

    async def create(self, owner_id: UUID, payload: WishItemCreate) -> WishItem | None:
        """Create item in wishlist if user owns the wishlist. Returns item or None (forbidden)."""
        wishlist = await self._wishlist_repo.get_by_id_and_owner(payload.wishlist_id, owner_id)
        if not wishlist:
            return None
        return await self._item_repo.create(
            wishlist_id=payload.wishlist_id,
            title=payload.title,
            description=payload.description,
            product_url=payload.product_url,
            image_url=payload.image_url,
            target_price=payload.target_price,
            allow_group_contribution=payload.allow_group_contribution,
        )

    async def get_by_id_for_owner(self, item_id: UUID, owner_id: UUID) -> WishItem | None:
        """Get item by id if it belongs to a wishlist owned by owner (includes soft-deleted)."""
        return await self._item_repo.get_by_id_for_owner(item_id, owner_id)

    async def update(self, item_id: UUID, owner_id: UUID, payload: WishItemUpdate) -> WishItem | None:
        """Update item if user owns its wishlist. Returns updated item or None."""
        item = await self._item_repo.get_by_id_for_owner(item_id, owner_id)
        if not item:
            return None
        return await self._item_repo.update(
            item_id,
            title=payload.title,
            description=payload.description,
            product_url=payload.product_url,
            image_url=payload.image_url,
            target_price=payload.target_price,
            allow_group_contribution=payload.allow_group_contribution,
        )

    async def soft_delete(self, item_id: UUID, owner_id: UUID) -> bool:
        """Soft-delete item if user owns its wishlist. Returns True if deleted."""
        item = await self._item_repo.get_by_id_for_owner(item_id, owner_id)
        if not item:
            return False
        return await self._item_repo.soft_delete(item_id)
