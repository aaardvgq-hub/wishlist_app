"""
WebSocket manager: room per wishlist_id, subscribe on connect, broadcast to room.
Non-blocking; supports multiple workers via Redis pub/sub.
"""

import asyncio
import json
import logging
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Event names for broadcast payloads
EVENT_RESERVATION_CREATED = "reservation_created"
EVENT_RESERVATION_CANCELLED = "reservation_cancelled"
EVENT_CONTRIBUTION_ADDED = "contribution_added"
EVENT_ITEM_UPDATED = "item_updated"

# Redis channel for cross-worker broadcast
WS_CHANNEL = "wishlist:ws_events"


class ConnectionManager:
    """In-process room per wishlist_id; subscribe on connect, broadcast to room."""

    def __init__(self) -> None:
        # wishlist_id -> set of WebSockets
        self._rooms: dict[UUID, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, wishlist_id: UUID) -> None:
        """Accept connection and add to room for wishlist_id."""
        await websocket.accept()
        async with self._lock:
            if wishlist_id not in self._rooms:
                self._rooms[wishlist_id] = set()
            self._rooms[wishlist_id].add(websocket)
        logger.debug("WS connect wishlist_id=%s total=%d", wishlist_id, len(self._rooms.get(wishlist_id, [])))

    async def disconnect(self, websocket: WebSocket, wishlist_id: UUID) -> None:
        """Remove from room."""
        async with self._lock:
            s = self._rooms.get(wishlist_id)
            if s:
                s.discard(websocket)
                if not s:
                    del self._rooms[wishlist_id]

    async def broadcast_to_room(self, wishlist_id: UUID, message: dict) -> None:
        """
        Send message to all clients in the room. Non-blocking: each send is not awaited
        so we don't block the caller; errors are logged.
        """
        async with self._lock:
            sockets = set(self._rooms.get(wishlist_id) or [])
        if not sockets:
            return
        text = json.dumps(message, default=str)
        async def send_one(ws: WebSocket) -> None:
            try:
                await ws.send_text(text)
            except Exception as e:
                logger.warning("WS send error: %s", e)

        await asyncio.gather(*[send_one(ws) for ws in sockets], return_exceptions=True)
