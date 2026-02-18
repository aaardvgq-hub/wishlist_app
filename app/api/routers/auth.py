"""Auth API: register, login, refresh (with rotation), logout. Tokens in httpOnly cookies."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenMessage
from app.schemas.user import UserResponse
from app.services.auth import AuthService

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set httpOnly cookies for access and refresh tokens (path=/ for whole app)."""
    response.set_cookie(
        key=settings.access_token_cookie_name,
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_same_site,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_same_site,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    """Clear access and refresh token cookies (path=/ so they clear everywhere)."""
    response.delete_cookie(settings.access_token_cookie_name, path="/")
    response.delete_cookie(settings.refresh_token_cookie_name, path="/")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user and set auth cookies (logged in after register)."""
    service = AuthService(session)
    if await service.email_taken(payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = await service.register(payload)
    access, refresh, _ = await service.create_tokens_for_user(user)
    _set_auth_cookies(response, access, refresh)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=UserResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Authenticate and set auth cookies."""
    service = AuthService(session)
    user = await service.authenticate_user(payload)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    access, refresh, _ = await service.create_tokens_for_user(user)
    _set_auth_cookies(response, access, refresh)
    return UserResponse.model_validate(user)


@router.post("/refresh", response_model=TokenMessage)
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> TokenMessage:
    """Rotate refresh token: validate cookie, issue new access + refresh, set new cookies."""
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
    service = AuthService(session)
    tokens = await service.refresh_tokens(refresh_token)
    if not tokens:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    access, new_refresh, _ = tokens
    _set_auth_cookies(response, access, new_refresh)
    return TokenMessage()


@router.post("/logout", response_model=TokenMessage)
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> TokenMessage:
    """Clear auth cookies and revoke the refresh token (if present)."""
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name)
    service = AuthService(session)
    await service.logout(refresh_token)
    _clear_auth_cookies(response)
    return TokenMessage(message="Logged out")


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return current authenticated user (from cookie or Authorization header)."""
    return UserResponse.model_validate(current_user)
