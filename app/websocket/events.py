"""
Emit WebSocket events from the service layer (reservation, contribution, item updated).
Use run_* async functions with FastAPI BackgroundTasks so broadcast runs after DB commit.
Emit failures are logged and never crash the request.
"""

import logging
from uuid import UUID

from app.websocket.manager import (
    EVENT_CONTRIBUTION_ADDED,
    EVENT_ITEM_UPDATED,
    EVENT_RESERVATION_CANCELLED,
    EVENT_RESERVATION_CREATED,
)
from app.websocket.redis_broadcast import publish_event

logger = logging.getLogger(__name__)


def _get_state(app: object) -> tuple:
    """Return (redis_pub, ws_manager) from app.state."""
    state = getattr(app, "state", None)
    if not state:
        return None, None
    redis_pub = getattr(state, "redis_pub", None)
    ws_manager = getattr(state, "ws_manager", None)
    return redis_pub, ws_manager


async def run_emit_reservation_created(app: object, wishlist_id: UUID, payload: dict) -> None:
    """Awaitable: broadcast reservation created. Use with BackgroundTasks.add_task after commit."""
    try:
        redis_pub, ws_manager = _get_state(app)
        if not ws_manager:
            return
        await publish_event(redis_pub, ws_manager, EVENT_RESERVATION_CREATED, wishlist_id, payload)
    except Exception as e:
        logger.warning("emit_reservation_created_failed", extra={"wishlist_id": str(wishlist_id), "error": str(e)})


async def run_emit_reservation_cancelled(app: object, wishlist_id: UUID, payload: dict) -> None:
    """Awaitable: broadcast reservation cancelled. Use with BackgroundTasks.add_task after commit."""
    try:
        redis_pub, ws_manager = _get_state(app)
        if not ws_manager:
            return
        await publish_event(redis_pub, ws_manager, EVENT_RESERVATION_CANCELLED, wishlist_id, payload)
    except Exception as e:
        logger.warning("emit_reservation_cancelled_failed", extra={"wishlist_id": str(wishlist_id), "error": str(e)})


async def run_emit_contribution_added(app: object, wishlist_id: UUID, payload: dict) -> None:
    """Awaitable: broadcast contribution added. Use with BackgroundTasks.add_task after commit."""
    try:
        redis_pub, ws_manager = _get_state(app)
        if not ws_manager:
            return
        await publish_event(redis_pub, ws_manager, EVENT_CONTRIBUTION_ADDED, wishlist_id, payload)
    except Exception as e:
        logger.warning("emit_contribution_added_failed", extra={"wishlist_id": str(wishlist_id), "error": str(e)})


async def run_emit_item_updated(app: object, wishlist_id: UUID, payload: dict) -> None:
    """Awaitable: broadcast item updated. Use with BackgroundTasks.add_task after commit."""
    try:
        redis_pub, ws_manager = _get_state(app)
        if not ws_manager:
            return
        await publish_event(redis_pub, ws_manager, EVENT_ITEM_UPDATED, wishlist_id, payload)
    except Exception as e:
        logger.warning("emit_item_updated_failed", extra={"wishlist_id": str(wishlist_id), "error": str(e)})
