"""Link preview endpoint: Telegram-style preview via our parser (og:image, meta name=description, etc.)."""

from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.wish_item import ProductPreview
from app.services.product_parser import fetch_product_preview

router = APIRouter(tags=["link-preview"])


@router.get(
    "/link-preview",
    response_model=ProductPreview,
    summary="Get link preview (Telegram-style)",
)
async def link_preview(url: str = Query(..., description="URL to preview")):
    """
    Fetch URL and return preview: all og:image (//→https, prefer full URL), meta name=description (incl. data-hid).
    UX: frontend calls when user pastes link; on change — call again; on remove — clear card.
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
    return await fetch_product_preview(url)
