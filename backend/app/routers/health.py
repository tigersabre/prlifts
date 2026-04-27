"""
health.py
PRLifts Backend

Health check endpoint consumed by Railway to verify service liveness.
Returns HTTP 200 with the current environment so Railway monitoring
can confirm the correct configuration is loaded.
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Response body for the health check endpoint."""

    status: str
    environment: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
    description=(
        "Returns HTTP 200 when the service is running. "
        "Consumed by Railway to verify service liveness. "
        "Responds within 500ms under normal conditions."
    ),
)
async def health_check() -> HealthResponse:
    """
    Returns service health status and current environment.

    Returns:
        HealthResponse with status 'ok' and the current environment name.
    """
    settings = get_settings()
    logger.info("Health check")
    return HealthResponse(status="ok", environment=settings.environment)
