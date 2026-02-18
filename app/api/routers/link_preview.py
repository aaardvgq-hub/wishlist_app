"""Link preview endpoint: Telegram-style preview via linkpreview library."""

import asyncio
import logging
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.wish_item import ProductPreview

logger = logging.getLogger(__name__)

router = APIRouter(tags=["link-preview"])


def _fetch_preview_sync(url: str) -> ProductPreview:
    """Sync fetch using linkpreview (run in thread)."""
    from linkpreview import link_preview

    try:
        preview = link_preview(url)
        title = (preview.title or preview.force_title or "").strip() or None
        description = (preview.description or "").strip() or None
        image_url = (preview.absolute_image or preview.image or "").strip() or None
        if image_url and len(image_url) > 2048:
            image_url = image_url[:2048]
        if title and len(title) > 500:
            title = title[:500]
        if description and len(description) > 10000:
            description = description[:10000]
        return ProductPreview(
            title=title,
            image_url=image_url,
            description=description,
            price=None,
            product_url=url[:2048] if url else None,
            preview_quality="full" if (title and image_url) else "partial" if (title or image_url or description) else "minimal",
            missing_fields=[] if image_url else ["image_url"],
        )
    except Exception as e:
        logger.info("linkpreview_failed", extra={"url": url[:500], "error": str(e)})
        return ProductPreview(
            preview_quality="minimal",
            missing_fields=["title", "image_url", "description", "price"],
        )


@router.get(
    "/link-preview",
    response_model=ProductPreview,
    summary="Get link preview (Telegram-style)",
)
async def link_preview(url: str = Query(..., description="URL to preview")):
    """
    Fetch URL and return preview (title, description, image) using linkpreview library.
    UX: frontend calls this when user pastes a link; on link change — call again; on link remove — clear card.
    """
    url = (url or "").strip()
    if not url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="url is required")
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL")
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL")
    result = await asyncio.to_thread(_fetch_preview_sync, url)
    return result
