"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_html_with_og():
    """HTML with og:title, og:image, and title tag."""
    return """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:title" content="Cool Product Name">
    <meta property="og:image" content="https://example.com/image.jpg">
    <meta property="og:price:amount" content="99.99">
    <title>Fallback Page Title</title>
</head>
<body></body>
</html>
"""


@pytest.fixture
def sample_html_title_only():
    """HTML with only <title> (no og)."""
    return """
<!DOCTYPE html>
<html>
<head><title>Only Title Here</title></head>
<body></body>
</html>
"""


@pytest.fixture
def sample_html_price_variants():
    """HTML with different price meta patterns."""
    return """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:title" content="Product">
    <meta itemprop="price" content="42.50">
</head>
<body></body>
</html>
"""


@pytest.fixture
def sample_html_empty():
    """Minimal HTML with no product data."""
    return "<html><head></head><body></body></html>"
