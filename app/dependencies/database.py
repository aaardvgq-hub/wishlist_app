"""Dependencies for DB session and derived services."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db as _get_db
from app.repositories.user import UserRepository
from app.repositories.wish_item import WishItemRepository
from app.repositories.wishlist import WishlistRepository
from app.repositories.reservation import ReservationRepository
from app.repositories.contribution import ContributionRepository
from app.services.user import UserService
from app.services.wish_item import WishItemService
from app.services.reservation import ReservationService
from app.services.contribution import ContributionService
from app.services.wishlist import WishlistService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Inject async DB session (re-export from core)."""
    async for session in _get_db():
        yield session


def get_user_repository(session: AsyncSession) -> UserRepository:
    """Build UserRepository from session."""
    return UserRepository(session)


def get_user_service(session: AsyncSession) -> UserService:
    """Build UserService from session."""
    return UserService(session)


def get_wishlist_repository(session: AsyncSession) -> WishlistRepository:
    """Build WishlistRepository from session."""
    return WishlistRepository(session)


def get_wish_item_repository(session: AsyncSession) -> WishItemRepository:
    """Build WishItemRepository from session."""
    return WishItemRepository(session)


def get_wish_item_service(session: AsyncSession) -> WishItemService:
    """Build WishItemService from session."""
    return WishItemService(session)


def get_reservation_service(session: AsyncSession) -> ReservationService:
    """Build ReservationService from session."""
    return ReservationService(session)


def get_contribution_service(session: AsyncSession) -> ContributionService:
    """Build ContributionService from session."""
    return ContributionService(session)


def get_wishlist_service(session: AsyncSession) -> WishlistService:
    """Build WishlistService from session."""
    return WishlistService(session)
