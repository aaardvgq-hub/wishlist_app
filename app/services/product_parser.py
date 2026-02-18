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
# meta name="description" — разные порядки атрибутов, допускаем data-hid и др.
_META_NAME_DESCRIPTION = re.compile(
    r'<meta[^>]*\bname\s*=\s*(["\'])description\1[^>]*\bcontent\s*=\s*\1([^\1]*?)\1',
    re.IGNORECASE | re.DOTALL,
)
_META_NAME_DESCRIPTION_ALT = re.compile(
    r'<meta[^>]*\bcontent\s*=\s*(["\'])(.+?)\1[^>]*\bname\s*=\s*(["\'])description\3',
    re.IGNORECASE | re.DOTALL,
)
# Все og:image (несколько тегов на странице — WB, Ozon и т.д.)
_OG_IMAGE_ALL = re.compile(
    r'<meta[^>]*\bproperty\s*=\s*(["\'])og:image\1[^>]*\bcontent\s*=\s*(["\'])(.+?)\2',
    re.IGNORECASE | re.DOTALL,
)
_OG_IMAGE_ALL_ALT = re.compile(
    r'<meta[^>]*\bcontent\s*=\s*(["\'])(.+?)\1[^>]*\bproperty\s*=\s*(["\'])og:image\3',
    re.IGNORECASE | re.DOTALL,
)
# Запасной вариант: тег содержит og:image и content= в любом порядке (WB, Ozon и др.)
_OG_IMAGE_LOOSE_A = re.compile(
    r'<meta[^>]*\bog:image\b[^>]*\bcontent\s*=\s*(["\'])(.+?)\1',
    re.IGNORECASE | re.DOTALL,
)
_OG_IMAGE_LOOSE_B = re.compile(
    r'<meta[^>]*\bcontent\s*=\s*(["\'])(.+?)\1[^>]*\bog:image\b',
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


def _normalize_image_url(raw: str) -> str:
    """Protocol-relative // → https:; trim to 2048."""
    s = (raw or "").strip()
    if not s:
        return ""
    if s.startswith("//"):
        s = "https:" + s
    return s[:2048]


def _extract_content_from_meta_tag(tag: str) -> str | None:
    """Из атрибута content= в произвольном теге meta извлечь значение (кавычки любые)."""
    m = re.search(r'\bcontent\s*=\s*"([^"]*)"', tag, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"\bcontent\s*=\s*'([^']*)'", tag, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def _extract_all_og_images_fallback(html: str) -> list[str]:
    """Грубый проход: все <meta ... >, в которых есть og:image — вытащить content= (Ozon, WB и др.)."""
    urls: list[str] = []
    # Разбиваем по <meta и берём кусок до следующего >
    parts = re.split(r"<meta\s", html, flags=re.IGNORECASE)
    for i, part in enumerate(parts):
        if i == 0:
            continue
        end = part.find(">")
        if end == -1:
            continue
        tag = part[:end]
        if "og:image" not in tag.lower():
            continue
        raw = _extract_content_from_meta_tag(tag)
        if raw:
            u = _normalize_image_url(raw)
            if u and u not in urls:
                urls.append(u)
    return urls


def _extract_all_og_images(html: str) -> list[str]:
    """Все og:image из страницы (несколько тегов — WB, Ozon). Возвращаем нормализованные URL."""
    urls: list[str] = []
    seen: set[str] = set()
    for pattern, content_group in (
        (_OG_IMAGE_ALL, 3),
        (_OG_IMAGE_ALL_ALT, 2),
        (_OG_IMAGE_LOOSE_A, 2),
        (_OG_IMAGE_LOOSE_B, 2),
    ):
        for m in pattern.finditer(html):
            if m.lastindex >= content_group:
                raw = (m.group(content_group) or "").strip()
                if raw:
                    u = _normalize_image_url(raw)
                    if u and u not in seen:
                        seen.add(u)
                        urls.append(u)
    if not urls:
        for u in _extract_all_og_images_fallback(html):
            if u not in seen:
                seen.add(u)
                urls.append(u)
    return urls


def _best_image(urls: list[str]) -> str | None:
    """Предпочитаем полный https URL (часто товар), не // (часто лого)."""
    if not urls:
        return None
    for u in urls:
        if u.startswith("https://") and len(u) > 30:
            return u
    return urls[0]


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


def _extract_meta_name_description_fallback(html: str) -> str | None:
    """Грубый проход: <meta> с name=description — вытащить content= (Ozon, WB)."""
    parts = re.split(r"<meta\s", html, flags=re.IGNORECASE)
    for i, part in enumerate(parts):
        if i == 0:
            continue
        end = part.find(">")
        if end == -1:
            continue
        tag = part[:end]
        # name="description" или name='description' или data-hid и т.д.
        if "description" not in tag.lower():
            continue
        # проверяем, что это именно name=description (а не og:description и т.д.)
        if not re.search(r"\bname\s*=\s*([\"'])description\1", tag, re.IGNORECASE):
            continue
        raw = _extract_content_from_meta_tag(tag)
        if raw:
            return raw[:10000]
    return None


def _extract_meta_name_description(html: str) -> str | None:
    """<meta name="description" content="..."> (в т.ч. data-hid). Сначала после <title, иначе в любом месте."""
    after_title = html
    idx = html.lower().find("<title")
    if idx != -1:
        after_title = html[idx + len("<title") :]
    for haystack in (after_title, html):
        m = _META_NAME_DESCRIPTION.search(haystack)
        if m and m.lastindex >= 2:
            raw = (m.group(2) or "").strip()
            if raw:
                return raw[:10000]
        m = _META_NAME_DESCRIPTION_ALT.search(haystack)
        if m and m.lastindex >= 2:
            raw = (m.group(2) or "").strip()
            if raw:
                return raw[:10000]
    return _extract_meta_name_description_fallback(html)


def _parse_html(html: str, product_url: str) -> ProductPreview:
    """Parse first MAX_BYTES of HTML into ProductPreview with preview_quality and missing_fields."""
    title = _extract_og(html, _OG_TITLE, _OG_TITLE_ALT) or _extract_title_tag(html)
    # Image: все og:image, // → https, предпочитаем полный https URL (товар, не лого)
    all_images = _extract_all_og_images(html)
    image_url = _best_image(all_images) if all_images else None
    if not image_url:
        raw = _extract_og(html, _OG_IMAGE, _OG_IMAGE_ALT)
        image_url = _normalize_image_url(raw) if raw else None
    # Description: ONLY <meta name="description"> and only after </title>
    description = _extract_meta_name_description(html)
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
    timeout = min(TIMEOUT, 6.0)  # не ждём дольше 6 сек
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(timeout),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
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
