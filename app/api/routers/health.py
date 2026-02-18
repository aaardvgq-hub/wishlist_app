"""Healthcheck and readiness endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.dependencies import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness: app is running."""
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@router.get("/health/ready")
async def ready(session: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Readiness: app and DB are reachable."""
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
