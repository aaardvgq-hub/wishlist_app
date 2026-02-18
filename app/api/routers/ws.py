"""WebSocket: subscribe to wishlist room by wishlist_id."""

from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket.manager import ConnectionManager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{wishlist_id}")
async def websocket_wishlist(
    websocket: WebSocket,
    wishlist_id: UUID,
) -> None:
    """
    Connect to real-time updates for a wishlist.
    Clients subscribe to the room for this wishlist_id on connect.
    Broadcasts: reservation_created, reservation_cancelled, contribution_added, item_updated.
    """
    manager: ConnectionManager = websocket.app.state.ws_manager
    await manager.connect(websocket, wishlist_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, wishlist_id)
