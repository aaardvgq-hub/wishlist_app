"""RefreshToken repository: persistence for JWT refresh token rotation."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Repository for refresh token CRUD and lookups."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: UUID, token_hash: str, expires_at: datetime) -> RefreshToken:
        """Store a new refresh token hash."""
        row = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """Find a valid (non-expired) refresh token by hash."""
        result = await self._session.execute(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .where(RefreshToken.expires_at > datetime.now(UTC))
        )
        return result.scalar_one_or_none()

    async def delete_by_token_hash(self, token_hash: str) -> None:
        """Remove refresh token by hash (for rotation or logout)."""
        await self._session.execute(delete(RefreshToken).where(RefreshToken.token_hash == token_hash))

    async def delete_all_for_user(self, user_id: UUID) -> None:
        """Revoke all refresh tokens for a user (e.g. logout all devices)."""
        await self._session.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
