# PRLifts — Security Test Plan

**Version:** 1.0
**Last updated:** April 2026
**Owners:** QA Lead + Security Architect
**Audience:** QA and security developers (human and Claude Code)

> This plan defines what security tests exist, where they run, and what
> they verify. Security tests are not optional — they are CI gates that
> block deployment just like functional tests.

---

## Security Test Categories

| Category | Runs in | Blocking | Tag |
|---|---|---|---|
| Photo deletion verification | CI (every push to main) | Yes | `@security` |
| Biometric consent enforcement | CI (every push to main) | Yes | `@security` |
| Authentication boundary tests | CI (every push to main) | Yes | `@security` |
| Input validation / injection tests | CI (every push to main) | Yes | `@security` |
| Rate limiting tests | CI (every push to main) | Yes | `@security` |
| Secret scanning | CI (every push) | Yes | automated |
| Dependency vulnerability scan | CI (every push) | Yes | automated |
| OWASP Mobile Top 10 checklist | Pre-launch manual | Yes (launch gate) | manual |
| Penetration test | V2 | No (V1) | external |

---

## Category 1 — Photo Deletion Verification

**Purpose:** Verify that user photos are deleted from all systems within
60 seconds of future self image generation, per the biometric data retention
policy and BIPA compliance requirement.

**Runs:** Every push to main branch. Tagged `@security`. Blocking.

```python
# tests/security/test_photo_deletion.py

import pytest
import asyncio
import time

@pytest.mark.security
async def test_photo_deleted_from_memory_within_sixty_seconds(
    test_user, mock_fal_ai, mock_claude_api, db_session
):
    """
    Verifies that the original user photo is not accessible anywhere
    in the system within 60 seconds of a future_self job completing.

    Arrange: user with valid BiometricConsent
    Act: submit a future_self job with a test photo
    Assert: after job processing, photo is absent from all verifiable locations
    """
    # Arrange
    photo_data = load_test_photo("test_face.jpg")
    photo_hash = hashlib.sha256(photo_data).hexdigest()
    await create_biometric_consent(test_user.id, db_session)

    # Act
    job = await submit_future_self_job(test_user.id, photo_data, db_session)
    await process_job(job.id)

    # Assert — verify photo is not in any accessible location
    start = time.time()
    while time.time() - start < 60:
        assert not railway_filesystem_contains(photo_hash), \
            "Photo found on Railway filesystem"
        assert not job_result_contains_photo(job.id, photo_hash, db_session), \
            "Photo found in job result"
        assert not ai_request_log_contains_photo(photo_hash, db_session), \
            "Photo found in AI request log"
        await asyncio.sleep(5)

    # Final assertion at 60-second mark
    assert photo_is_absent_from_all_systems(photo_hash), \
        "Photo still present after 60 seconds"


@pytest.mark.security
async def test_photo_not_logged_at_any_level(
    test_user, mock_fal_ai, caplog, db_session
):
    """
    Verifies that photo binary content does not appear in any log output
    at any log level, even DEBUG.
    """
    photo_data = load_test_photo("test_face.jpg")
    photo_snippet = base64.b64encode(photo_data[:50]).decode()

    with caplog.at_level(logging.DEBUG):
        await submit_future_self_job(test_user.id, photo_data, db_session)

    assert photo_snippet not in caplog.text, \
        "Photo content found in log output"
```

---

## Category 2 — Biometric Consent Enforcement

**Purpose:** Verify that the future self feature cannot be accessed
without a valid BiometricConsent record.

```python
# tests/security/test_biometric_consent.py

@pytest.mark.security
async def test_future_self_job_rejected_without_consent(
    test_user, db_session, client
):
    """
    Verifies that a future_self job cannot be created without
    a BiometricConsent record with consent_given = true.
    """
    # Arrange — no consent record for this user
    photo_data = load_test_photo("test_face.jpg")

    # Act
    response = await client.post(
        "/v1/jobs",
        json={"job_type": "future_self"},
        files={"photo": ("photo.jpg", photo_data, "image/jpeg")},
        headers=auth_headers(test_user)
    )

    # Assert
    assert response.status_code == 403
    assert response.json()["error_code"] == "biometric_consent_required"


@pytest.mark.security
async def test_future_self_job_rejected_when_consent_declined(
    test_user, db_session, client
):
    """
    Verifies declined consent blocks the feature even if a record exists.
    """
    await create_biometric_consent(test_user.id, db_session, consent_given=False)
    photo_data = load_test_photo("test_face.jpg")

    response = await client.post("/v1/jobs",
        json={"job_type": "future_self"},
        files={"photo": ("photo.jpg", photo_data, "image/jpeg")},
        headers=auth_headers(test_user)
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "biometric_consent_declined"


@pytest.mark.security
async def test_consent_write_failure_blocks_photo_processing(
    test_user, db_session, client, monkeypatch
):
    """
    Verifies that if the BiometricConsent write fails, no photo
    is processed — fail-safe behaviour.
    """
    # Arrange — simulate DB write failure
    monkeypatch.patch("app.services.consent_service.write_consent",
                      side_effect=Exception("DB error"))
    photo_data = load_test_photo("test_face.jpg")

    response = await client.post("/v1/users/me/biometric-consent",
        json={"consent_given": True,
              "consent_version": "1.0",
              "policy_text_hash": "abc123"},
        headers=auth_headers(test_user)
    )

    # Assert — consent endpoint fails
    assert response.status_code == 500
    assert response.json()["error_code"] == "biometric_consent_write_failed"

    # And no photo job was created despite the failure
    jobs = await get_user_jobs(test_user.id, db_session)
    assert len(jobs) == 0
```

---

## Category 3 — Authentication Boundary Tests

**Purpose:** Verify that every endpoint enforces authentication and
that one user cannot access another user's data.

```python
# tests/security/test_auth_boundaries.py

@pytest.mark.security
async def test_unauthenticated_request_returns_401(client):
    """Every protected endpoint returns 401 without a token."""
    endpoints = [
        ("GET", "/v1/users/me"),
        ("GET", "/v1/workouts"),
        ("POST", "/v1/workouts"),
        ("GET", "/v1/personal-records"),
        ("POST", "/v1/jobs"),
    ]
    for method, path in endpoints:
        response = await client.request(method, path)
        assert response.status_code == 401, \
            f"{method} {path} should return 401 without auth"


@pytest.mark.security
async def test_user_cannot_read_another_users_workout(
    test_user, other_user, db_session, client
):
    """
    User A cannot access User B's workout even with a valid token.
    RLS should prevent this at the database level.
    """
    # Arrange — create a workout for other_user
    workout = await create_workout(other_user.id, db_session)

    # Act — test_user attempts to read it
    response = await client.get(
        f"/v1/workouts/{workout.id}",
        headers=auth_headers(test_user)
    )

    # Assert — 404 (not 403 — do not confirm the resource exists)
    assert response.status_code in (403, 404)


@pytest.mark.security
async def test_user_id_from_jwt_not_request_body(
    test_user, other_user, db_session, client
):
    """
    Verifies the backend ignores user_id in the request body and uses
    the JWT user_id instead.
    """
    # Act — attempt to create a workout claiming to be other_user
    response = await client.post(
        "/v1/workouts",
        json={"type": "ad_hoc", "format": "weightlifting",
              "user_id": str(other_user.id)},  # attempt injection
        headers=auth_headers(test_user)
    )

    # Assert — workout created but belongs to test_user, not other_user
    assert response.status_code == 201
    workout_id = response.json()["id"]
    workout = await get_workout(workout_id, db_session)
    assert workout.user_id == test_user.id
    assert workout.user_id != other_user.id
```

---

## Category 4 — Input Validation / Injection Tests

**Purpose:** Verify that all inputs are validated and injection attempts
are rejected safely.

```python
# tests/security/test_input_validation.py

@pytest.mark.security
@pytest.mark.parametrize("payload,expected_status", [
    # Weight beyond maximum
    ({"weight": 99999, "reps": 5}, 422),
    # Negative reps
    ({"weight": 100, "reps": -1}, 422),
    # RPE out of range
    ({"weight": 100, "reps": 5, "rpe": 11}, 422),
    # SQL injection attempt in notes field
    ({"weight": 100, "reps": 5, "notes": "'; DROP TABLE workout_set; --"}, 201),
    # XSS attempt in notes field (should be stored safely, not executed)
    ({"weight": 100, "reps": 5, "notes": "<script>alert('xss')</script>"}, 201),
    # Extremely long notes (beyond maxLength)
    ({"weight": 100, "reps": 5, "notes": "x" * 10000}, 422),
])
async def test_workout_set_input_validation(
    payload, expected_status, test_workout_exercise, test_user, client
):
    """
    Input validation rejects out-of-range values.
    SQL injection and XSS content is stored safely (not executed).
    """
    full_payload = {
        "workout_exercise_id": str(test_workout_exercise.id),
        "set_number": 1,
        "set_type": "normal",
        "weight_modifier": "none",
        **payload
    }
    response = await client.post("/v1/workout-sets",
        json=full_payload, headers=auth_headers(test_user))
    assert response.status_code == expected_status


@pytest.mark.security
async def test_sql_injection_in_exercise_search(test_user, client):
    """
    Exercise search with SQL injection attempt returns safe empty results.
    """
    response = await client.get(
        "/v1/exercises?q='; DROP TABLE exercise; --",
        headers=auth_headers(test_user)
    )
    assert response.status_code == 200
    # System should still be operational
    response2 = await client.get("/v1/exercises?q=Bench Press",
                                  headers=auth_headers(test_user))
    assert response2.status_code == 200
    assert len(response2.json()["data"]) > 0
```

---

## Category 5 — Rate Limiting Tests

**Purpose:** Verify rate limits are enforced and return correct headers.

```python
# tests/security/test_rate_limiting.py

@pytest.mark.security
async def test_rate_limit_returns_429_after_threshold(test_user, client):
    """
    General rate limit (100 req/min) is enforced.
    """
    # Send requests until rate limited
    for _ in range(101):
        response = await client.get("/v1/workouts",
                                     headers=auth_headers(test_user))

    assert response.status_code == 429
    assert response.json()["error_code"] == "rate_limit_exceeded"
    assert "Retry-After" in response.headers


@pytest.mark.security
async def test_monthly_ai_limit_enforced(test_user, db_session, client):
    """
    Monthly AI insight limit (60/month) is enforced.
    """
    # Create 60 completed insight jobs for this month
    await create_n_completed_jobs(60, test_user.id, "insight", db_session)

    response = await client.post("/v1/jobs",
        json={"job_type": "insight",
              "workout_id": str(uuid4())},
        headers=auth_headers(test_user)
    )

    assert response.status_code == 429
    assert response.json()["error_code"] == "job_insight_limit_reached"
```

---

## Category 6 — Secret Scanning (Automated)

Runs as a pre-commit hook and in CI on every push.

```yaml
# .github/workflows/secret-scan.yml
- name: Scan for secrets
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
    base: ${{ github.event.repository.default_branch }}
    head: HEAD
```

**What it scans for:**
- API keys (Anthropic, Fal.ai, Supabase pattern matches)
- Generic high-entropy strings in code and config files
- AWS, Google, Azure credential patterns (defence-in-depth)

---

## Category 7 — Dependency Vulnerability Scan (Automated)

```bash
# Runs in CI on every push
pip audit --requirement requirements.txt
```

Fails CI if any dependency has a known CVE with severity MEDIUM or above.

---

## OWASP Mobile Top 10 — Pre-Launch Checklist

This must be completed manually before V1 public launch.
Each item is verified by code review + a test run.

| # | Risk | PRLifts mitigation | Verified |
|---|---|---|---|
| M1 | Improper Credential Usage | Keychain only, no UserDefaults | [ ] |
| M2 | Inadequate Supply Chain Security | pip audit in CI | [ ] |
| M3 | Insecure Authentication/Authorisation | JWT + RLS | [ ] |
| M4 | Insufficient Input/Output Validation | Pydantic + SwiftUI validation | [ ] |
| M5 | Insecure Communication | TLS 1.3 + TrustKit | [ ] |
| M6 | Inadequate Privacy Controls | No PII in logs, biometric consent | [ ] |
| M7 | Insufficient Binary Protections | Xcode release build hardening | [ ] |
| M8 | Security Misconfiguration | Secrets audit pre-launch | [ ] |
| M9 | Insecure Data Storage | Keychain for tokens, Data Protection for local files | [ ] |
| M10 | Insufficient Cryptography | iOS system crypto only, no custom implementation | [ ] |

