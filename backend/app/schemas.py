"""
schemas.py
PRLifts Backend

Shared Pydantic response schemas used across all API endpoints.
Putting them here keeps routers thin and avoids circular imports —
auth, routers, and middleware can all reference these without depending
on each other.

See docs/ERROR_CATALOG.md for all valid error codes and user-facing messages.
See docs/STANDARDS.md § 7.5 API Error Response Standard.
"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """
    Standard error response body for all backend error responses.

    error_code is machine-readable and drives client-side behaviour (e.g. sign-out).
    message is safe to display directly to users — never contains internal detail.
    request_id is the correlation_id so users can quote it to support.

    See docs/ERROR_CATALOG.md for every valid error_code and its matching message.
    """

    error_code: str
    message: str
    request_id: str
