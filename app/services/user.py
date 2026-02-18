"""User service: business logic and orchestration."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.models.user import User


class UserService:
    """User registration and lookup."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = UserRepository(session)

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by id."""
        return await self._repo.get_by_id(user_id)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        return await self._repo.get_by_email(email)

    async def register(self, payload: UserCreate) -> User:
        """Register a new user. Caller must handle duplicate email."""
        hashed = hash_password(payload.password)
        return await self._repo.create(email=payload.email, hashed_password=hashed)

    async def email_taken(self, email: str) -> bool:
        """Check if email is already in use."""
        return await self._repo.exists_by_email(email)
