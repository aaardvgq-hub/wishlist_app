"""FastAPI dependencies."""

from app.dependencies.auth import get_current_user
from app.dependencies.database import (
    get_db,
    get_user_repository,
    get_user_service,
    get_wishlist_repository,
    get_wishlist_service,
    get_wish_item_repository,
    get_wish_item_service,
    get_reservation_service,
    get_contribution_service,
)
from app.dependencies.session import get_anonymous_session_id

__all__ = [
    "get_db",
    "get_user_repository",
    "get_user_service",
    "get_wishlist_repository",
    "get_wish_item_repository",
    "get_wish_item_service",
    "get_reservation_service",
    "get_contribution_service",
    "get_wishlist_service",
    "get_current_user",
    "get_anonymous_session_id",
]
