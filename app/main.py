"""FastAPI application entrypoint."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import auth, health, items, users, wishlists, ws
from app.core.config import get_settings
from app.core.database import close_db
from app.middleware.rate_limit import PublicWishlistRateLimitMiddleware
from app.schemas.errors import ErrorResponse, error_code_from_status
from app.websocket.manager import ConnectionManager
from app.websocket.redis_broadcast import run_subscriber

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown: DB, Redis pub/sub, WebSocket manager."""
    app.state.ws_manager = ConnectionManager()
    app.state.redis_pub = None
    subscriber_task = None
    try:
        if settings.redis_url:
            try:
                from redis.asyncio import Redis

                app.state.redis_pub = Redis.from_url(settings.redis_url, decode_responses=True)
                subscriber_task = await run_subscriber(app.state.ws_manager, settings.redis_url)
                app.state.ws_subscriber_task = subscriber_task
                logger.info("WebSocket Redis pub/sub enabled")
            except Exception as e:
                logger.warning("Redis connect failed, WS single-worker only: %s", e)
    except Exception as e:
        logger.warning("WebSocket setup: %s", e)
    yield
    if subscriber_task and not subscriber_task.done():
        subscriber_task.cancel()
        try:
            await subscriber_task
        except asyncio.CancelledError:
            pass
    if getattr(app.state, "redis_pub", None) is not None:
        await app.state.redis_pub.aclose()
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="""Social wishlist API: share lists, reserve gifts, contribute to expensive items.

**Error responses** all use the same schema: `{ "detail": "...", "error_code": "..." }`.

**Error codes:** `validation_error` (422), `invalid_request` (400), `unauthorized` (401), `forbidden` (403), `not_found` (404), `conflict` (409), `rate_limited` (429), `internal_error` (500).
""",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "wishlists", "description": "List, create, get wishlists; public view by share token."},
        {"name": "items", "description": "Wish items CRUD, product preview, reserve and contribute."},
        {"name": "auth", "description": "Register, login, refresh, logout."},
        {"name": "users", "description": "Current user profile."},
        {"name": "health", "description": "Liveness and readiness."},
        {"name": "websocket", "description": "WebSocket for realtime wishlist updates."},
    ],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return 422 with unified error schema."""
    detail = exc.errors()[0].get("msg", "Validation error") if exc.errors() else "Validation error"
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(detail=detail, error_code="validation_error").model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    """All HTTPException responses use ErrorResponse schema."""
    code = error_code_from_status(exc.status_code)
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=detail, error_code=code).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions."""
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail="Internal server error", error_code="internal_error").model_dump(),
    )

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if "*" in origins or (len(origins) == 1 and origins[0] == "*"):
    origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(PublicWishlistRateLimitMiddleware)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(ws.router, prefix="/api")
app.include_router(wishlists.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(users.router, prefix="/api")
