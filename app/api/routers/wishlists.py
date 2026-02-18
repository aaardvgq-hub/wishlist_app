"""Wishlists API: list, create, get, public by token. Router → service only."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, get_wishlist_service
from app.models.user import User
from app.schemas.errors import ErrorResponse
from app.schemas.wishlist import (
    WishlistCreate,
    WishlistPublicResponse,
    WishlistResponse,
    WishlistWithItemsResponse,
)

router = APIRouter(prefix="/wishlists", tags=["wishlists"])


@router.get("/", response_model=list[WishlistResponse])
async def list_wishlists(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """List current user's wishlists."""
    service = get_wishlist_service(session)
    lists = await service.list_by_owner(current_user.id)
    return [WishlistResponse.model_validate(w) for w in lists]


@router.post("/", response_model=WishlistResponse, status_code=status.HTTP_201_CREATED)
async def create_wishlist(
    payload: WishlistCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Create a new wishlist."""
    service = get_wishlist_service(session)
    w = await service.create(current_user.id, payload)
    return WishlistResponse.model_validate(w)


@router.get(
    "/public/{token}",
    response_model=WishlistPublicResponse,
    responses={404: {"model": ErrorResponse, "description": "Wishlist not found or not public"}},
)
async def get_public_wishlist(
    token: UUID,
    session: AsyncSession = Depends(get_db),
):
    """Get wishlist by share token (no auth). Items include reserved and contribution progress. Rate-limited per IP."""
    service = get_wishlist_service(session)
    dto = await service.get_public_dto(token)
    if not dto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
    return dto


@router.get("/{wishlist_id}", response_model=WishlistWithItemsResponse)
async def get_wishlist(
    wishlist_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get one wishlist with items (owner only)."""
    service = get_wishlist_service(session)
    dto = await service.get_with_items_for_owner(wishlist_id, current_user.id)
    if not dto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
    return dto