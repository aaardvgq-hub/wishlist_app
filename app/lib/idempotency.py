"""In-memory idempotency cache for contribution endpoint. Key: (idempotency_key, session_id, item_id)."""

import time
from typing import Any

# key -> (response_body_dict, timestamp)
_contribution_cache: dict[tuple[str, str, str], tuple[dict[str, Any], float]] = {}
_TTL_SECONDS = 86400  # 24 hours
_MAX_ENTRIES = 10_000


def _prune_if_needed() -> None:
    if len(_contribution_cache) <= _MAX_ENTRIES:
        return
    now = time.time()
    to_del = [k for k, (_, ts) in _contribution_cache.items() if now - ts > _TTL_SECONDS]
    for k in to_del[: _MAX_ENTRIES // 2]:  # evict half of expired
        _contribution_cache.pop(k, None)
    if len(_contribution_cache) > _MAX_ENTRIES:
        oldest = min(_contribution_cache.items(), key=lambda x: x[1][1])
        _contribution_cache.pop(oldest[0], None)


def get_contribution_cached(idempotency_key: str, session_id: str, item_id: str) -> dict[str, Any] | None:
    key = (idempotency_key.strip()[:128], session_id, str(item_id))
    entry = _contribution_cache.get(key)
    if not entry:
        return None
    body, ts = entry
    if time.time() - ts > _TTL_SECONDS:
        _contribution_cache.pop(key, None)
        return None
    return body


def set_contribution_cached(idempotency_key: str, session_id: str, item_id: str, body: dict[str, Any]) -> None:
    _prune_if_needed()
    key = (idempotency_key.strip()[:128], session_id, str(item_id))
    _contribution_cache[key] = (body, time.time())
