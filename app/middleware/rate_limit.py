"""Per-IP rate limit for public wishlist endpoint."""

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings

# In-memory: ip -> list of request timestamps in the last minute
_store: dict[str, list[float]] = defaultdict(list)
_cleanup_after = 120  # drop entries older than 2 minutes


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _prune(ip: str) -> None:
    now = time.monotonic()
    cutoff = now - 60
    _store[ip] = [t for t in _store[ip] if t > cutoff]
    if not _store[ip]:
        del _store[ip]


class PublicWishlistRateLimitMiddleware(BaseHTTPMiddleware):
    """Limit requests to GET /api/wishlists/public/* per IP per minute."""

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/wishlists/public/"):
            return await call_next(request)
        settings = get_settings()
        if settings.rate_limit_public_per_minute <= 0:
            return await call_next(request)
        ip = _get_client_ip(request)
        now = time.monotonic()
        _prune(ip)
        if len(_store[ip]) >= settings.rate_limit_public_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests", "error_code": "rate_limited"},
            )
        _store[ip].append(now)
        return await call_next(request)
