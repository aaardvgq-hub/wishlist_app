"""Security: bcrypt password hashing and JWT (access + refresh) with secure defaults."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
_settings = get_settings()

# Token types for payload "type" claim (prevents access token being used as refresh and vice versa)
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def hash_password(plain_password: str) -> str:
    """Hash a plain password with bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str | Any) -> str:
    """Create JWT access token (short-lived). Subject must be user id string."""
    expire = datetime.now(UTC) + timedelta(minutes=_settings.access_token_expire_minutes)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": ACCESS_TOKEN_TYPE,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(to_encode, _settings.secret_key, algorithm="HS256")


def create_refresh_token(subject: str | Any) -> tuple[str, str]:
    """
    Create JWT refresh token (long-lived) with unique jti for rotation.
    Returns (token_string, token_hash_for_storage).
    """
    expire = datetime.now(UTC) + timedelta(days=_settings.refresh_token_expire_days)
    jti = secrets.token_urlsafe(32)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": REFRESH_TOKEN_TYPE,
        "jti": jti,
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(to_encode, _settings.secret_key, algorithm="HS256")
    token_hash = hash_refresh_token(token)
    return token, token_hash


def hash_refresh_token(token: str) -> str:
    """Hash refresh token for storage (do not store raw token in DB)."""
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> str | None:
    """Decode access JWT and return subject (user id) or None if invalid."""
    try:
        payload = jwt.decode(token, _settings.secret_key, algorithms=["HS256"])
        if payload.get("type") != ACCESS_TOKEN_TYPE:
            return None
        return payload.get("sub")
    except JWTError:
        return None


def decode_refresh_token(token: str) -> tuple[str | None, str | None]:
    """
    Decode refresh JWT. Returns (subject, jti) or (None, None) if invalid.
    Caller uses jti/hash to find and revoke the token in DB for rotation.
    """
    try:
        payload = jwt.decode(token, _settings.secret_key, algorithms=["HS256"])
        if payload.get("type") != REFRESH_TOKEN_TYPE:
            return None, None
        return payload.get("sub"), payload.get("jti")
    except JWTError:
        return None, None
