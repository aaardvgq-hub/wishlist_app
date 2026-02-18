"""
Redis pub/sub for WebSocket broadcast across multiple workers.
Publish from API; subscriber task in each worker broadcasts to local connections.
"""

import asyncio
import json
import logging
from uuid import UUID

from app.websocket.manager import ConnectionManager, WS_CHANNEL

logger = logging.getLogger(__name__)


def _make_message(event: str, wishlist_id: UUID, payload: dict) -> dict:
    return {"event": event, "wishlist_id": str(wishlist_id), "payload": payload}


async def run_subscriber(manager: ConnectionManager, redis_url: str) -> asyncio.Task[None]:
    """
    Start a background task that subscribes to Redis and broadcasts to local rooms.
    Returns the task so it can be cancelled on shutdown.
    """
    try:
        from redis.asyncio import Redis
    except ImportError:
        logger.warning("redis not installed; WebSocket broadcast will be single-worker only")
        return asyncio.create_task(asyncio.sleep(999999))

    async def listen() -> None:
        r = Redis.from_url(redis_url, decode_responses=True)
        try:
            pubsub = r.pubsub()
            await pubsub.subscribe(WS_CHANNEL)
            while True:
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg is None:
                    continue
                if msg.get("type") != "message":
                    continue
                data = msg.get("data")
                if not data:
                    continue
                try:
                    obj = json.loads(data)
                    wid = obj.get("wishlist_id")
                    if not wid:
                        continue
                    wishlist_id = UUID(wid)
                    # Broadcast in background so we don't block the listener
                    asyncio.create_task(manager.broadcast_to_room(wishlist_id, obj))
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning("WS Redis message parse error: %s", e)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(WS_CHANNEL)
            await r.aclose()

    task = asyncio.create_task(listen())
    return task


async def publish_event(
    redis_client: "redis.asyncio.Redis | None",
    manager: ConnectionManager,
    event: str,
    wishlist_id: UUID,
    payload: dict,
) -> None:
    """
    Publish event to Redis (so all workers broadcast) and, if no Redis, broadcast locally.
    Failures are logged; never raise (guard when redis/pubsub unavailable or broadcast fails).
    """
    message = _make_message(event, wishlist_id, payload)
    if redis_client:
        try:
            await redis_client.publish(WS_CHANNEL, json.dumps(message, default=str))
        except Exception as e:
            logger.warning("WS Redis publish error: %s", e)
            try:
                await manager.broadcast_to_room(wishlist_id, message)
            except Exception as e2:
                logger.warning("WS local broadcast fallback failed: %s", e2)
    else:
        try:
            await manager.broadcast_to_room(wishlist_id, message)
        except Exception as e:
            logger.warning("WS broadcast failed (no Redis): %s", e)
