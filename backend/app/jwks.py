"""
jwks.py
PRLifts Backend

JWKS key cache for ES256 JWT verification against Supabase's asymmetric
signing keys. Fetches and caches the Supabase JWKS endpoint with a 1-hour TTL.
On a kid miss against a fresh cache, refetches once to handle key rotation.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import jwt

logger = logging.getLogger(__name__)

_JWKS_URL = "https://kgrwxdmmycqdongqewzr.supabase.co/auth/v1/.well-known/jwks.json"
_TTL = timedelta(hours=1)
_FETCH_TIMEOUT = httpx.Timeout(10.0)


class JWKSCache:
    """In-process cache of Supabase EC public keys keyed by kid."""

    def __init__(self) -> None:
        self._keys: dict[str, Any] = {}
        self._fetched_at: datetime | None = None
        self._lock = asyncio.Lock()

    def _is_stale(self) -> bool:
        if self._fetched_at is None:
            return True
        return datetime.now(UTC) - self._fetched_at >= _TTL

    async def _fetch(self) -> None:
        """Fetches the JWKS endpoint and repopulates the key cache."""
        logger.info("Fetching JWKS from Supabase")
        async with httpx.AsyncClient() as client:
            resp = await client.get(_JWKS_URL, timeout=_FETCH_TIMEOUT)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()

        new_keys: dict[str, Any] = {}
        for jwk in data.get("keys", []):
            kid: str = jwk.get("kid", "")
            if not kid:
                continue
            try:
                new_keys[kid] = jwt.algorithms.ECAlgorithm.from_jwk(jwk)
            except Exception:
                logger.warning("Failed to parse JWK", extra={"kid": kid})

        self._keys = new_keys
        self._fetched_at = datetime.now(UTC)
        logger.info("JWKS cache refreshed", extra={"key_count": len(new_keys)})

    async def get_key(self, kid: str) -> Any | None:
        """
        Returns the public key for kid.

        Fetches if the cache is stale. On a kid miss against a fresh cache,
        refetches once to handle key rotation before returning None.

        Args:
            kid: The key ID from the JWT header.

        Returns:
            EC public key, or None if kid is not found after one refetch.
        """
        async with self._lock:
            if self._is_stale():
                await self._fetch()

            if kid in self._keys:
                return self._keys[kid]

            # kid not in a fresh cache — refetch once for key rotation
            await self._fetch()
            return self._keys.get(kid)


# Module-level singleton shared across all requests.
_cache = JWKSCache()


async def get_public_key(kid: str) -> Any | None:
    """Returns the EC public key for kid, or None after one refetch."""
    return await _cache.get_key(kid)
