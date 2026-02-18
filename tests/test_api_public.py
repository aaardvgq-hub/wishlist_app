"""API tests: public wishlist endpoint (no auth)."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Skip API tests that need DB if no DATABASE_URL (e.g. in CI without test DB)
needs_db = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL", "").strip().startswith("postgresql+asyncpg"),
    reason="DATABASE_URL not set or not asyncpg (API test needs real DB)",
)


@needs_db
def test_public_wishlist_invalid_token_returns_404() -> None:
    """GET /api/wishlists/public/{token} with non-existent token returns 404."""
    client = TestClient(app)
    random_uuid = uuid4()
    response = client.get(f"/api/wishlists/public/{random_uuid}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    detail = data["detail"] if isinstance(data["detail"], str) else str(data.get("detail", ""))
    assert "not found" in detail.lower()
