"""Application configuration via Pydantic Settings and .env."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Production-ready config loaded from environment and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = Field(default="Social Wishlist API", description="Application name")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Runtime environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # Server
    host: str = Field(default="0.0.0.0", description="Bind host")
    port: int = Field(default=8000, ge=1, le=65535, description="Bind port")

    # Database (must use async driver: postgresql+asyncpg)
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/wishlist",
        description="Async PostgreSQL URL (postgresql+asyncpg://...)",
    )

    @field_validator("database_url")
    @classmethod
    def database_url_must_be_async(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("database_url must use async driver: postgresql+asyncpg://...")
        return v
    database_echo: bool = Field(default=False, description="Echo SQL statements")
    database_pool_size: int = Field(default=5, ge=1, le=100, description="Connection pool size")
    database_max_overflow: int = Field(default=10, ge=0, le=100, description="Max overflow connections")

    # JWT & cookies
    secret_key: str = Field(
        default="change-me-in-production-use-openssl-rand-hex-32",
        min_length=32,
        description="Secret key for signing JWTs",
    )
    access_token_expire_minutes: int = Field(default=15, ge=1, description="Access JWT expiry (minutes)")
    refresh_token_expire_days: int = Field(default=7, ge=1, description="Refresh token expiry (days)")
    access_token_cookie_name: str = Field(default="access_token", description="httpOnly cookie name for access token")
    refresh_token_cookie_name: str = Field(default="refresh_token", description="httpOnly cookie name for refresh token")
    cookie_secure: bool = Field(default=False, description="Set Secure flag on cookies (True in production HTTPS)")
    cookie_same_site: Literal["lax", "strict", "none"] = Field(default="lax", description="SameSite cookie attribute")

    # Product URL fetch (auto-fill)
    product_fetch_timeout_seconds: float = Field(default=10.0, ge=1.0, le=60.0, description="Timeout for product page fetch")
    product_fetch_max_bytes: int = Field(default=512 * 1024, description="Max HTML bytes to read for parsing (512KB)")

    # Anonymous session (reserve/contribute without auth)
    session_id_cookie_name: str = Field(default="session_id", description="Cookie name for anonymous viewer session")
    session_id_cookie_max_age_days: int = Field(default=365, ge=1, description="Session cookie max age in days")
    min_contribution_amount: float | None = Field(default=None, description="Optional minimum contribution (None = no minimum)")

    # Redis (for WebSocket pub/sub across workers; if empty, single-worker mode)
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL for WS broadcast across workers")

    # CORS (comma-separated origins, or * for allow all)
    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated CORS origins (e.g. http://localhost:3000,https://app.example.com)",
    )

    # Public endpoint rate limit (per-IP, per minute; 0 = disabled)
    rate_limit_public_per_minute: int = Field(
        default=60,
        ge=0,
        description="Max requests per IP per minute for GET /wishlists/public/{token}. 0 disables.",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
