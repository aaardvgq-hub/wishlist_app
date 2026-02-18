"""Unit tests for product URL parser with mocked HTML."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.wish_item import ProductPreview
from app.services.product_parser import fetch_product_preview


@pytest.mark.asyncio
async def test_parse_og_title_image_price(sample_html_with_og: str) -> None:
    """Parse og:title, og:image, og:price:amount from mocked response."""
    mock_response = MagicMock()
    mock_response.content = sample_html_with_og.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    mock_get = AsyncMock(return_value=mock_response)
    mock_client = MagicMock()
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.product_parser.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_product_preview("https://example.com/product")

    assert result.title == "Cool Product Name"
    assert result.image_url == "https://example.com/image.jpg"
    assert result.price == Decimal("99.99")
    assert result.product_url == "https://example.com/product"


@pytest.mark.asyncio
async def test_parse_fallback_title(sample_html_title_only: str) -> None:
    """When no og:title, fallback to <title> tag."""
    mock_response = MagicMock()
    mock_response.content = sample_html_title_only.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.product_parser.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_product_preview("https://example.com/page")

    assert result.title == "Only Title Here"
    assert result.image_url is None
    assert result.price is None
    assert result.product_url == "https://example.com/page"


@pytest.mark.asyncio
async def test_parse_itemprop_price(sample_html_price_variants: str) -> None:
    """Parse itemprop='price' meta."""
    mock_response = MagicMock()
    mock_response.content = sample_html_price_variants.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.product_parser.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_product_preview("https://example.com/item")

    assert result.title == "Product"
    assert result.price == Decimal("42.50")


@pytest.mark.asyncio
async def test_empty_html_returns_empty_preview(sample_html_empty: str) -> None:
    """HTML with no product data returns empty preview fields."""
    mock_response = MagicMock()
    mock_response.content = sample_html_empty.encode("utf-8")
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.product_parser.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_product_preview("https://example.com/empty")

    assert result.title is None
    assert result.image_url is None
    assert result.price is None
    assert result.product_url == "https://example.com/empty"


@pytest.mark.asyncio
async def test_fetch_error_returns_empty_preview() -> None:
    """On network/HTTP error, return minimal preview with missing_fields set (no exception)."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=Exception("Connection error"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.product_parser.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_product_preview("https://example.com/bad")

    assert result.title is None
    assert result.product_url is None
    assert result.preview_quality == "minimal"
    assert set(result.missing_fields) == {"title", "image_url", "price"}


@pytest.mark.asyncio
async def test_invalid_url_returns_empty_preview() -> None:
    """Non-http URL or empty string returns minimal preview without fetching."""
    result = await fetch_product_preview("")
    assert result.preview_quality == "minimal"
    assert set(result.missing_fields) == {"title", "image_url", "price"}

    result = await fetch_product_preview("ftp://example.com/file")
    assert result.preview_quality == "minimal"
    assert set(result.missing_fields) == {"title", "image_url", "price"}

    result = await fetch_product_preview("file:///etc/passwd")
    assert result.preview_quality == "minimal"
    assert set(result.missing_fields) == {"title", "image_url", "price"}


