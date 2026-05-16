#!/usr/bin/env python3
"""
smoke_test_rate_limiting.py
PRLifts — Manual Verification Scripts

Verifies that rate limiting is active and returns correct headers on the
Railway deployment. Authenticates via Supabase, then hammers two endpoints
until each returns HTTP 429, and confirms the Retry-After header is present.

Rate limit tiers exercised:
  POST /v1/jobs      — AI tier:      10 req/min per user (hits 429 at request 11)
  POST /v1/workouts  — General tier: 100 req/min per user (hits 429 at request 101)

Usage:
    export SUPABASE_URL=https://your-project.supabase.co
    export SUPABASE_ANON_KEY=eyJ...
    export RAILWAY_URL=https://prlifts-production.up.railway.app
    export TEST_EMAIL=smoke@example.com
    export TEST_PASSWORD=your-test-password
    python scripts/smoke_test_rate_limiting.py  # run from backend/

All five environment variables are required. See docs/ENV_CONFIG.md for
the canonical variable reference and the Railway dashboard for current values.

Exit codes:
    0 — all checks passed
    1 — one or more checks failed or a required variable is missing
"""

import os
import sys
import uuid
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_REQUIRED_VARS = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "RAILWAY_URL",
    "TEST_EMAIL",
    "TEST_PASSWORD",
]

# AI tier: 10 req/min. Stop after this many requests (11 triggers the 429).
_AI_MAX_REQUESTS = 15
# General tier: 100 req/min. Stop early — 105 is enough to reliably hit 429.
_GENERAL_MAX_REQUESTS = 110

_TIMEOUT = httpx.Timeout(15.0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_env() -> dict[str, str] | None:
    missing = False
    cfg: dict[str, str] = {}
    for var in _REQUIRED_VARS:
        val = os.environ.get(var, "").strip()
        if not val:
            print(f"  ERROR: required variable {var!r} is not set", flush=True)
            missing = True
        else:
            cfg[var] = val
    return None if missing else cfg


def _print_result(label: str, passed: bool, detail: str) -> None:
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {label}: {detail}", flush=True)


# ---------------------------------------------------------------------------
# Step 1 — Supabase authentication
# ---------------------------------------------------------------------------


def authenticate(
    supabase_url: str, anon_key: str, email: str, password: str
) -> str | None:
    """Returns a JWT access token or None on failure."""
    print("\n── Step 1: Supabase authentication ──", flush=True)
    url = f"{supabase_url}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": anon_key,
        "Content-Type": "application/json",
    }
    body = {"email": email, "password": password}

    try:
        resp = httpx.post(url, headers=headers, json=body, timeout=_TIMEOUT)
    except httpx.RequestError as exc:
        _print_result("Supabase auth", False, f"request error: {exc}")
        return None

    if resp.status_code != 200:
        _print_result(
            "Supabase auth",
            False,
            f"HTTP {resp.status_code} — {resp.text[:200]}",
        )
        return None

    data: Any = resp.json()
    token: str | None = data.get("access_token")
    if not token:
        _print_result("Supabase auth", False, f"no access_token in response: {data}")
        return None

    _print_result("Supabase auth", True, f"got access_token ({len(token)} chars)")
    return token


# ---------------------------------------------------------------------------
# Step 2 — AI endpoint rate limit check (POST /v1/jobs)
# ---------------------------------------------------------------------------


def check_ai_rate_limit(railway_url: str, token: str) -> bool:
    """
    Fires POST /v1/jobs up to _AI_MAX_REQUESTS times.
    Expects a 429 with a Retry-After header before the limit is reached.

    Uses a random workout_id — the 422 / 404 responses before the rate limit
    kicks in are fine; we only care about seeing a 429.
    """
    print("\n── Step 2: AI rate limit — POST /v1/jobs (limit: 10/min) ──", flush=True)
    url = f"{railway_url}/v1/jobs"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {
        "job_type": "insight",
        "workout_id": str(uuid.uuid4()),
    }

    hit_429 = False
    retry_after_present = False
    last_status = None
    last_body = ""

    for i in range(1, _AI_MAX_REQUESTS + 1):
        try:
            resp = httpx.post(url, headers=headers, json=body, timeout=_TIMEOUT)
        except httpx.RequestError as exc:
            _print_result(
                "AI rate limit — request",
                False,
                f"request error on attempt {i}: {exc}",
            )
            return False

        last_status = resp.status_code
        last_body = resp.text[:120]

        print(f"    attempt {i:>3}: HTTP {resp.status_code}", flush=True)

        if resp.status_code == 429:
            hit_429 = True
            retry_after = resp.headers.get("Retry-After", "")
            retry_after_present = bool(retry_after)
            print(f"             Retry-After: {retry_after!r}", flush=True)
            print(f"             body: {resp.text[:120]}", flush=True)
            break

    if hit_429:
        ai_detail = f"got 429 after ≤{_AI_MAX_REQUESTS} requests"
    else:
        ai_detail = f"last response was HTTP {last_status}: {last_body}"
    _print_result("AI 429 received", hit_429, ai_detail)
    _print_result(
        "AI Retry-After header present",
        retry_after_present,
        "header present" if retry_after_present else "header missing on 429 response",
    )

    return hit_429 and retry_after_present


# ---------------------------------------------------------------------------
# Step 3 — General endpoint rate limit check (POST /v1/workouts)
# ---------------------------------------------------------------------------


def check_general_rate_limit(railway_url: str, token: str) -> bool:
    """
    Fires POST /v1/workouts up to _GENERAL_MAX_REQUESTS times.
    Expects a 429 with a Retry-After header within 101 requests.

    Each call creates a real workout — the test user should be cleaned up
    after this smoke test or run against a dedicated test account.
    """
    print(
        "\n── Step 3: General rate limit — POST /v1/workouts (limit: 100/min) ──",
        flush=True,
    )
    url = f"{railway_url}/v1/workouts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {"type": "ad_hoc", "format": "weightlifting"}

    hit_429 = False
    retry_after_present = False
    last_status = None
    last_body = ""

    for i in range(1, _GENERAL_MAX_REQUESTS + 1):
        try:
            resp = httpx.post(url, headers=headers, json=body, timeout=_TIMEOUT)
        except httpx.RequestError as exc:
            _print_result(
                "General rate limit — request",
                False,
                f"request error on attempt {i}: {exc}",
            )
            return False

        last_status = resp.status_code
        last_body = resp.text[:120]

        # Print every 10 requests to show progress without flooding output
        if i % 10 == 0 or resp.status_code == 429:
            print(f"    attempt {i:>3}: HTTP {resp.status_code}", flush=True)

        if resp.status_code == 429:
            hit_429 = True
            retry_after = resp.headers.get("Retry-After", "")
            retry_after_present = bool(retry_after)
            print(f"             Retry-After: {retry_after!r}", flush=True)
            print(f"             body: {resp.text[:120]}", flush=True)
            break

    if hit_429:
        gen_detail = f"got 429 after ≤{_GENERAL_MAX_REQUESTS} requests"
    else:
        gen_detail = f"last response was HTTP {last_status}: {last_body}"
    _print_result("General 429 received", hit_429, gen_detail)
    _print_result(
        "General Retry-After header present",
        retry_after_present,
        "header present" if retry_after_present else "header missing on 429 response",
    )

    return hit_429 and retry_after_present


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print("PRLifts — Rate Limiting Smoke Test", flush=True)
    print("=" * 50, flush=True)

    cfg = _load_env()
    if cfg is None:
        print(
            "\nABORTED: set all required environment variables and retry.",
            flush=True,
        )
        return 1

    token = authenticate(
        supabase_url=cfg["SUPABASE_URL"],
        anon_key=cfg["SUPABASE_ANON_KEY"],
        email=cfg["TEST_EMAIL"],
        password=cfg["TEST_PASSWORD"],
    )
    if token is None:
        print("\nABORTED: authentication failed.", flush=True)
        return 1

    ai_ok = check_ai_rate_limit(cfg["RAILWAY_URL"], token)
    general_ok = check_general_rate_limit(cfg["RAILWAY_URL"], token)

    print("\n" + "=" * 50, flush=True)
    print("Summary:", flush=True)
    _print_result("AI rate limit (POST /v1/jobs)", ai_ok, "10 req/min tier")
    _print_result(
        "General rate limit (POST /v1/workouts)", general_ok, "100 req/min tier"
    )

    if ai_ok and general_ok:
        print("\nResult: ALL CHECKS PASSED", flush=True)
        return 0
    else:
        print("\nResult: ONE OR MORE CHECKS FAILED", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
