"""Auth service: registration, login, refresh (with rotation), logout."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest

_settings = get_settings()


class AuthService:
    """Authentication: register, login, refresh with rotation, logout."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._refresh_repo = RefreshTokenRepository(session)

    async def register(self, payload: RegisterRequest) -> User:
        """Create a new user. Caller must check email_taken before."""
        from app.core.security import hash_password

        user = await self._user_repo.create(
            email=payload.email,
            hashed_password=hash_password(payload.password),
        )
        return user

    async def email_taken(self, email: str) -> bool:
        """Check if email is already registered."""
        return await self._user_repo.exists_by_email(email)

    async def authenticate_user(self, payload: LoginRequest) -> User | None:
        """Verify email/password and return user or None."""
        user = await self._user_repo.get_by_email(payload.email)
        if not user or not user.is_active:
            return None
        if not verify_password(payload.password, user.hashed_password):
            return None
        return user

    async def create_tokens_for_user(self, user: User) -> tuple[str, str, str]:
        """
        Create access token and refresh token; store refresh hash.
        Returns (access_token, refresh_token, refresh_token_hash).
        """
        access = create_access_token(str(user.id))
        refresh, refresh_hash = create_refresh_token(str(user.id))
        expires_at = datetime.now(UTC) + timedelta(days=_settings.refresh_token_expire_days)
        await self._refresh_repo.create(user_id=user.id, token_hash=refresh_hash, expires_at=expires_at)
        return access, refresh, refresh_hash

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str, str] | None:
        """
        Validate refresh token, rotate (delete old, create new), return new pair.
        Returns (access_token, refresh_token, refresh_token_hash) or None if invalid.
        """
        sub, _ = decode_refresh_token(refresh_token)
        if not sub:
            return None
        token_hash = hash_refresh_token(refresh_token)
        stored = await self._refresh_repo.get_by_token_hash(token_hash)
        if not stored:
            return None
        await self._refresh_repo.delete_by_token_hash(token_hash)
        try:
            user_id = UUID(sub)
        except ValueError:
            return None
        user = await self._user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            return None
        access, new_refresh, new_hash = await self.create_tokens_for_user(user)
        return access, new_refresh, new_hash

    async def logout(self, refresh_token: str | None) -> None:
        """Revoke the given refresh token (by hash). If token is None, no-op."""
        if not refresh_token:
            return
        token_hash = hash_refresh_token(refresh_token)
        await self._refresh_repo.delete_by_token_hash(token_hash)
