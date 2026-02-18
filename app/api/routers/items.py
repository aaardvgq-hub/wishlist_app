"""Wishlist items CRUD, product URL preview, reserve and contribute."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_anonymous_session_id,
    get_contribution_service,
    get_current_user,
    get_db,
    get_reservation_service,
    get_wish_item_service,
)
from app.models.user import User
from app.schemas.contribution import ContributeRequest, ContributeResponse
from app.schemas.errors import ErrorResponse
from app.schemas.reservation import ReserveResponse
from app.schemas.wish_item import (
    ProductPreview,
    ProductPreviewRequest,
    WishItemCreate,
    WishItemResponse,
    WishItemUpdate,
)
from app.services.contribution import ContributionService
from app.services.product_parser import fetch_product_preview
from app.services.reservation import ReservationService
from app.services.wish_item import WishItemService
from app.lib.idempotency import get_contribution_cached, set_contribution_cached
from app.websocket.events import (
    run_emit_contribution_added,
    run_emit_item_updated,
    run_emit_reservation_cancelled,
    run_emit_reservation_created,
)

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/", response_model=WishItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: WishItemCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> WishItemResponse:
    """Create a wish item in a wishlist (must own the wishlist)."""
    service = get_wish_item_service(session)
    item = await service.create(current_user.id, payload)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Wishlist not found or access denied",
        )
    return WishItemResponse.model_validate(item)


@router.patch("/{item_id}", response_model=WishItemResponse)
async def update_item(
    item_id: UUID,
    payload: WishItemUpdate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> WishItemResponse:
    """Update a wish item (must own the wishlist)."""
    service = get_wish_item_service(session)
    item = await service.update(item_id, current_user.id, payload)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or access denied",
        )
    background_tasks.add_task(
        run_emit_item_updated,
        request.app,
        item.wishlist_id,
        {"item_id": str(item_id), "title": item.title, "target_price": str(item.target_price)},
    )
    return WishItemResponse.model_validate(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a wish item (must own the wishlist)."""
    service = get_wish_item_service(session)
    deleted = await service.soft_delete(item_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or access denied",
        )


@router.post(
    "/preview",
    response_model=ProductPreview,
    summary="Preview product metadata from URL",
    response_description="Extracted title, image, price plus preview_quality and missing_fields.",
)
async def product_preview(payload: ProductPreviewRequest) -> ProductPreview:
    """
    Fetch product URL and return structured preview (title, image, price).
    **preview_quality**: `full` (all three), `partial` (1–2), `minimal` (none or error).
    **missing_fields**: list of fields we could not extract (`title`, `image_url`, `price`).
    Timeout and errors return minimal preview with all missing_fields.
    """
    return await fetch_product_preview(payload.product_url)


# ---- Reserve / Contribute (anonymous, session_id cookie). Owner never sees identities. ----


@router.post("/{item_id}/reserve", response_model=ReserveResponse, status_code=status.HTTP_201_CREATED)
async def reserve_item(
    item_id: UUID,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
) -> ReserveResponse:
    """
    Reserve an item (anonymous, identified by session_id cookie).
    Prevents double reservation; one active reservation per item. Group mode override: allowed even if item has group contribution.
    """
    session_id = get_anonymous_session_id(request, response)
    reservation_service = get_reservation_service(session)
    reservation, wishlist_id = await reservation_service.reserve(item_id, session_id)
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item not found, already reserved by someone else, or already reserved by you",
        )
    if wishlist_id:
        background_tasks.add_task(
            run_emit_reservation_created,
            request.app,
            wishlist_id,
            {"item_id": str(item_id), "reservation_id": str(reservation.id), "created_at": str(reservation.created_at)},
        )
    return ReserveResponse.model_validate(reservation)


@router.delete("/{item_id}/reserve", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_reservation(
    item_id: UUID,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
) -> None:
    """Cancel your reservation for this item (session_id cookie)."""
    session_id = get_anonymous_session_id(request, response)
    reservation_service = get_reservation_service(session)
    cancelled, wishlist_id = await reservation_service.cancel(item_id, session_id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active reservation found for this item and session",
        )
    if wishlist_id:
        background_tasks.add_task(
            run_emit_reservation_cancelled, request.app, wishlist_id, {"item_id": str(item_id)}
        )


@router.post(
    "/{item_id}/contribute",
    response_model=ContributeResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Contribution recorded (or idempotent replay with same Idempotency-Key)"},
        400: {"model": ErrorResponse, "description": "Invalid amount, item fully funded, or would exceed target"},
    },
)
async def contribute_to_item(
    item_id: UUID,
    payload: ContributeRequest,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
) -> ContributeResponse | JSONResponse:
    """
    Contribute to an item (anonymous, session_id cookie).
    Send **Idempotency-Key** header (same key + session + item) to get previous result without double-charging.
    """
    session_id = get_anonymous_session_id(request, response)
    idempotency_key = request.headers.get("Idempotency-Key", "").strip()
    if idempotency_key:
        cached = get_contribution_cached(idempotency_key, session_id, str(item_id))
        if cached is not None:
            return JSONResponse(status_code=201, content=cached)
    contribution_service = get_contribution_service(session)
    contribution, contributed_total, target_price, progress_percent, wishlist_id, reject_reason = await contribution_service.contribute(
        item_id, session_id, payload.amount
    )
    if contribution is None:
        detail = (
            "Item is already fully funded"
            if reject_reason == "fully_funded"
            else "Item not found, does not allow group contribution, amount invalid, or would exceed target price"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    if wishlist_id:
        background_tasks.add_task(
            run_emit_contribution_added,
            request.app,
            wishlist_id,
            {
                "item_id": str(item_id),
                "contributed_total": str(contributed_total),
                "target_price": str(target_price),
                "progress_percent": progress_percent,
            },
        )
    resp = ContributeResponse(
        item_id=item_id,
        contributed_total=contributed_total,
        target_price=target_price,
        progress_percent=progress_percent,
        amount_added=payload.amount,
    )
    if idempotency_key:
        set_contribution_cached(idempotency_key, session_id, str(item_id), resp.model_dump(mode="json"))
    return resp
