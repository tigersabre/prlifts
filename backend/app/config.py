"""
config.py
PRLifts Backend

Application configuration loaded from environment variables.
Single source of truth for all backend configuration — no direct os.environ
calls elsewhere in the codebase. Loads .env in development; Railway injects
variables directly in staging/production. See docs/ENV_CONFIG.md.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv


class Settings:
    """
    Application settings loaded from environment variables.

    All variables are documented in docs/ENV_CONFIG.md.
    ENVIRONMENT is required; the application will not start without it.
    """

    def __init__(self) -> None:
        self.environment: str = os.environ["ENVIRONMENT"]
        self.log_level: str = os.environ.get("LOG_LEVEL", "INFO")
        self.app_version: str = os.environ.get("APP_VERSION", "0.1.0")
        self.sentry_dsn: str = os.environ.get("SENTRY_DSN", "")
        self.api_host: str = os.environ.get("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.environ.get("API_PORT", "8000"))
        # Used to verify Supabase JWTs — never log this value.
        self.supabase_jwt_secret: str = os.environ.get("SUPABASE_JWT_SECRET", "")
        # AI provider settings — see docs/ENV_CONFIG.md AI Provider Variables.
        self.claude_api_key: str = os.environ.get("CLAUDE_API_KEY", "")
        # Set true in test environment to skip real API calls.
        self.ai_providers_mocked: bool = (
            os.environ.get("AI_PROVIDERS_MOCKED", "false").lower() == "true"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns cached application settings loaded from environment.

    Loads .env if present (development only — not present in Railway).

    Returns:
        Cached Settings instance.

    Raises:
        KeyError: If ENVIRONMENT is not set.
    """
    load_dotenv()
    return Settings()
