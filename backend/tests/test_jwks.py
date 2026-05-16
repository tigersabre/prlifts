"""
test_jwks.py
PRLifts Backend Tests

Unit tests for app/jwks.py: cache staleness, key lookup, and the
single-refetch behaviour on a kid miss.
"""

import json
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from app.jwks import _TTL, JWKSCache

# ── Helpers ───────────────────────────────────────────────────────────────────

_KID_A = "key-id-a"
_KID_B = "key-id-b"
_FAKE_KEY_A = object()
_FAKE_KEY_B = object()


def _make_cache(
    *,
    keys: dict[str, Any] | None = None,
    fetched_at: datetime | None = None,
) -> JWKSCache:
    """Returns a JWKSCache pre-seeded with the given state."""
    cache = JWKSCache()
    cache._keys = keys or {}
    cache._fetched_at = fetched_at
    return cache


def _fresh_ts() -> datetime:
    return datetime.now(UTC) - timedelta(minutes=30)


def _stale_ts() -> datetime:
    return datetime.now(UTC) - (_TTL + timedelta(seconds=1))


def _mock_fetch(cache: JWKSCache, keys: dict[str, Any]) -> AsyncMock:
    """Patches cache._fetch to populate keys without hitting the network."""

    async def _fake_fetch() -> None:
        cache._keys = keys
        cache._fetched_at = datetime.now(UTC)

    return AsyncMock(side_effect=_fake_fetch)


# ── Staleness ─────────────────────────────────────────────────────────────────


def test_is_stale_returns_true_when_never_fetched() -> None:
    cache = _make_cache()
    assert cache._is_stale() is True


def test_is_stale_returns_false_within_ttl() -> None:
    cache = _make_cache(fetched_at=_fresh_ts())
    assert cache._is_stale() is False


def test_is_stale_returns_true_after_ttl_elapses() -> None:
    cache = _make_cache(fetched_at=_stale_ts())
    assert cache._is_stale() is True


# ── get_key: cache hit on fresh cache ─────────────────────────────────────────


async def test_get_key_returns_key_without_refetch_when_fresh_and_present() -> None:
    cache = _make_cache(keys={_KID_A: _FAKE_KEY_A}, fetched_at=_fresh_ts())
    fetch_mock = _mock_fetch(cache, {_KID_A: _FAKE_KEY_A})
    cache._fetch = fetch_mock  # type: ignore[method-assign]

    result = await cache.get_key(_KID_A)

    assert result is _FAKE_KEY_A
    fetch_mock.assert_not_called()


# ── get_key: stale cache triggers one fetch ───────────────────────────────────


async def test_get_key_fetches_when_cache_is_stale() -> None:
    cache = _make_cache(fetched_at=_stale_ts())
    fetch_mock = _mock_fetch(cache, {_KID_A: _FAKE_KEY_A})
    cache._fetch = fetch_mock  # type: ignore[method-assign]

    result = await cache.get_key(_KID_A)

    assert result is _FAKE_KEY_A
    assert fetch_mock.call_count == 1


# ── get_key: kid miss on fresh cache triggers one refetch ─────────────────────


async def test_get_key_refetches_once_on_kid_miss_against_fresh_cache() -> None:
    cache = _make_cache(keys={_KID_A: _FAKE_KEY_A}, fetched_at=_fresh_ts())
    fetch_mock = _mock_fetch(cache, {_KID_A: _FAKE_KEY_A, _KID_B: _FAKE_KEY_B})
    cache._fetch = fetch_mock  # type: ignore[method-assign]

    result = await cache.get_key(_KID_B)

    assert result is _FAKE_KEY_B
    assert fetch_mock.call_count == 1


async def test_get_key_returns_none_when_kid_absent_after_refetch() -> None:
    cache = _make_cache(keys={_KID_A: _FAKE_KEY_A}, fetched_at=_fresh_ts())
    fetch_mock = _mock_fetch(cache, {_KID_A: _FAKE_KEY_A})
    cache._fetch = fetch_mock  # type: ignore[method-assign]

    result = await cache.get_key(_KID_B)

    assert result is None
    assert fetch_mock.call_count == 1


# ── _fetch: parses JWK keys ───────────────────────────────────────────────────


async def test_fetch_populates_keys_from_jwks_response() -> None:
    """Verifies _fetch stores parsed public keys keyed by kid."""
    from cryptography.hazmat.primitives.asymmetric import ec

    private_key = ec.generate_private_key(ec.SECP256R1())
    import jwt as _jwt

    jwk_dict = json.loads(_jwt.algorithms.ECAlgorithm.to_jwk(private_key.public_key()))
    jwk_dict["kid"] = "my-test-kid"
    jwk_dict["use"] = "sig"

    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {"keys": [jwk_dict]}

    cache = JWKSCache()
    with patch("app.jwks.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await cache._fetch()

    assert "my-test-kid" in cache._keys
    assert cache._fetched_at is not None


async def test_fetch_skips_keys_without_kid() -> None:
    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {"keys": [{"kty": "EC"}]}  # no kid

    cache = JWKSCache()
    with patch("app.jwks.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await cache._fetch()

    assert cache._keys == {}


async def test_fetch_skips_unparseable_keys() -> None:
    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {
        "keys": [{"kid": "bad-key", "kty": "EC", "crv": "INVALID"}]
    }

    cache = JWKSCache()
    with patch("app.jwks.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=fake_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await cache._fetch()

    assert cache._keys == {}
