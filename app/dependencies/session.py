"""Anonymous session_id for reserve/contribute (cookie)."""

import secrets

from fastapi import Request, Response

from app.core.config import get_settings

_settings = get_settings()


def get_anonymous_session_id(request: Request, response: Response) -> str:
    """
    Get session_id from cookie or generate and set it.
    Caller must inject Response to allow setting cookie when generating.
    """
    session_id = request.cookies.get(_settings.session_id_cookie_name)
    if session_id and len(session_id) <= 255:
        return session_id
    new_id = secrets.token_urlsafe(32)
    response.set_cookie(
        key=_settings.session_id_cookie_name,
        value=new_id,
        httponly=True,
        secure=_settings.cookie_secure,
        samesite=_settings.cookie_same_site,
        max_age=_settings.session_id_cookie_max_age_days * 24 * 3600,
        path="/",
    )
    return new_id
