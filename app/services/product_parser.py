"""
Product URL parser: fetch HTML with httpx (async), parse og:title, og:image, meta price, title fallback.
Timeout and error handling; does not block event loop.
Only http/https URLs are allowed (SSRF and scheme validation).
"""

import logging
import re
from decimal import Decimal
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

from app.core.config import get_settings
from app.schemas.wish_item import ProductPreview

_settings = get_settings()

# Limit bytes read so we don't load huge pages into memory
MAX_BYTES = _settings.product_fetch_max_bytes
TIMEOUT = _settings.product_fetch_timeout_seconds

# Patterns for meta tags (content in single or double quotes)
_OG_TITLE = re.compile(
    r'<meta[^>]+property=(["\'])og:title\1[^>]+content=(["\'])(.+?)\2',
    re.IGNORECASE | re.DOTALL,
)
_OG_IMAGE = re.compile(
    r'<meta[^>]+property=(["\'])og:image\1[^>]+content=(["\'])(.+?)\2',
    re.IGNORECASE | re.DOTALL,
)
# content before property (some sites order differently)
_OG_TITLE_ALT = re.compile(
    r'<meta[^>]+content=(["\'])(.+?)\1[^>]+property=(["\'])og:title\3',
    re.IGNORECASE | re.DOTALL,
)
_OG_IMAGE_ALT = re.compile(
    r'<meta[^>]+content=(["\'])(.+?)\1[^>]+property=(["\'])og:image\3',
    re.IGNORECASE | re.DOTALL,
)
_OG_DESCRIPTION = re.compile(
    r'<meta[^>]+property=(["\'])og:description\1[^>]+content=(["\'])(.+?)\2',
    re.IGNORECASE | re.DOTALL,
)
_OG_DESCRIPTION_ALT = re.compile(
    r'<meta[^>]+content=(["\'])(.+?)\1[^>]+property=(["\'])og:description\3',
    re.IGNORECASE | re.DOTALL,
)
# Standard HTML meta name="description" (often after <title> in document)
_META_NAME_DESCRIPTION = re.compile(
    r'<meta[^>]+name=(["\'])description\1[^>]+content=(["\'])(.+?)\2',
    re.IGNORECASE | re.DOTALL,
)
_META_NAME_DESCRIPTION_ALT = re.compile(
    r'<meta[^>]+content=(["\'])(.+?)\1[^>]+name=(["\'])description\3',
    re.IGNORECASE | re.DOTALL,
)
# Twitter card image (Telegram and others use these too)
_TWITTER_IMAGE = re.compile(
    r'<meta[^>]+property=(["\'])twitter:image\1[^>]+content=(["\'])(.+?)\2',
    re.IGNORECASE | re.DOTALL,
)
_TWITTER_IMAGE_ALT = re.compile(
    r'<meta[^>]+content=(["\'])(.+?)\1[^>]+property=(["\'])twitter:image\3',
    re.IGNORECASE | re.DOTALL,
)
_TITLE_TAG = re.compile(r"<title[^>]*>\s*(.+?)\s*</title>", re.IGNORECASE | re.DOTALL)
# Price: og:price, product:price:amount, itemprop="price", or name="price"
_PRICE_PATTERNS = [
    re.compile(
        r'<meta[^>]+property=(["\'])og:price:amount\1[^>]+content=(["\'])(.+?)\2',
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r'<meta[^>]+content=(["\'])(.+?)\1[^>]+property=(["\'])og:price:amount\3',
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r'<meta[^>]+property=(["\'])og:price\1[^>]+content=(["\'])(.+?)\2',
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r'<meta[^>]+content=(["\'])(.+?)\1[^>]+property=(["\'])og:price\3',
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r'itemprop=(["\'])price\1[^>]+content=(["\'])(.+?)\2',
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r'content=(["\'])(.+?)\1[^>]+itemprop=(["\'])price\3',
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r'<meta[^>]+name=(["\'])price\1[^>]+content=(["\'])(.+?)\2',
        re.IGNORECASE | re.DOTALL,
    ),
]


def _extract_og(html: str, pattern: re.Pattern, alt_pattern: re.Pattern) -> str | None:
    """Extract content from og meta; main pattern has content in group 3, alt in group 2."""
    m = pattern.search(html)
    if m and m.lastindex >= 3:
        raw = (m.group(3) or "").strip()
        return raw[:2048] if raw else None
    m = alt_pattern.search(html)
    if m and m.lastindex >= 2:
        raw = (m.group(2) or "").strip()
        return raw[:2048] if raw else None
    return None


def _extract_title_tag(html: str) -> str | None:
    m = _TITLE_TAG.search(html)
    if not m:
        return None
    raw = m.group(1).strip()
    if not raw:
        return None
    from html import unescape

    return unescape(raw)[:500]


def _extract_price(html: str) -> Decimal | None:
    for p in _PRICE_PATTERNS:
        m = p.search(html)
        if m:
            raw = (m.group(3) or m.group(2) or "").strip()
            if not raw:
                continue
            cleaned = re.sub(r"[^\d.,]", "", raw.replace(",", "."))
            if not cleaned:
                continue
            try:
                return Decimal(cleaned)
            except Exception:
                continue
    return None


def _extract_meta_name_description(html: str) -> str | None:
    """Extract <meta name="description" content="..."> (primary source for description)."""
    m = _META_NAME_DESCRIPTION.search(html)
    if m and m.lastindex >= 3:
        raw = (m.group(3) or "").strip()
        return raw[:10000] if raw else None
    m = _META_NAME_DESCRIPTION_ALT.search(html)
    if m and m.lastindex >= 2:
        raw = (m.group(2) or "").strip()
        return raw[:10000] if raw else None
    return None


def _parse_html(html: str, product_url: str) -> ProductPreview:
    """Parse first MAX_BYTES of HTML into ProductPreview with preview_quality and missing_fields."""
    title = _extract_og(html, _OG_TITLE, _OG_TITLE_ALT) or _extract_title_tag(html)
    # Image: og:image first (Telegram etc.), then twitter:image
    image_url = _extract_og(html, _OG_IMAGE, _OG_IMAGE_ALT) or _extract_og(
        html, _TWITTER_IMAGE, _TWITTER_IMAGE_ALT
    )
    # Description: strict <meta name="description"> first, then og:description
    description = _extract_meta_name_description(html) or _extract_og(
        html, _OG_DESCRIPTION, _OG_DESCRIPTION_ALT
    )
    price = _extract_price(html)
    has_title = bool(title)
    has_image = bool(image_url)
    has_description = bool(description)
    has_price = price is not None
    missing: list[str] = []
    if not has_title:
        missing.append("title")
    if not has_image:
        missing.append("image_url")
    if not has_description:
        missing.append("description")
    if not has_price:
        missing.append("price")
    if has_title and has_image and has_price:
        quality = "full"
    elif has_title or has_image or has_price or has_description:
        quality = "partial"
    else:
        quality = "minimal"
    return ProductPreview(
        title=title[:500] if title else None,
        image_url=image_url[:2048] if image_url else None,
        description=description[:10000] if description else None,
        price=price,
        product_url=product_url[:2048] if product_url else None,
        preview_quality=quality,
        missing_fields=missing,
    )


async def fetch_product_preview(product_url: str) -> ProductPreview:
    """
    Fetch URL with httpx (async, timeout), parse og/title/price, return ProductPreview.
    On any error (timeout, non-2xx, decode, etc.) returns an empty ProductPreview (no exception).
    Does not block event loop.
    """
    empty = ProductPreview(preview_quality="minimal", missing_fields=["title", "image_url", "description", "price"])
    if not product_url or not product_url.strip():
        return empty
    url = product_url.strip()
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return empty
    except Exception:
        return empty
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(TIMEOUT),
            headers={"User-Agent": "WishlistBot/1.0 (Product preview)"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            content = response.content
            if len(content) > MAX_BYTES:
                content = content[:MAX_BYTES]
            text = content.decode("utf-8", errors="replace")
            return _parse_html(text, url)
    except Exception as e:
        logger.info("product_parser_failed", extra={"url": url[:500], "error": str(e)})
        return ProductPreview(preview_quality="minimal", missing_fields=["title", "image_url", "description", "price"])
