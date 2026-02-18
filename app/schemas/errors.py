"""Unified error response schema and error codes."""

from pydantic import BaseModel, Field

# Documented error codes (for OpenAPI and clients)
ERROR_CODES = {
    "validation_error": "Request body or query invalid (422).",
    "invalid_request": "Bad request, e.g. invalid input or business rule (400).",
    "unauthorized": "Missing or invalid auth (401).",
    "forbidden": "Authenticated but not allowed (403).",
    "not_found": "Resource not found (404).",
    "conflict": "State conflict, e.g. already reserved (409).",
    "rate_limited": "Too many requests (429).",
    "internal_error": "Server error (500).",
}


def error_code_from_status(status_code: int) -> str:
    if status_code == 400:
        return "invalid_request"
    if status_code == 401:
        return "unauthorized"
    if status_code == 403:
        return "forbidden"
    if status_code == 404:
        return "not_found"
    if status_code == 409:
        return "conflict"
    if status_code == 422:
        return "validation_error"
    if status_code == 429:
        return "rate_limited"
    if status_code >= 500:
        return "internal_error"
    return "invalid_request"


class ErrorResponse(BaseModel):
    """All API errors use this shape."""

    detail: str = Field(..., description="Human-readable error message")
    error_code: str = Field(..., description="Machine-readable code; see error codes in docs")
