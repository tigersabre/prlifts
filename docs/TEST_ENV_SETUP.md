# PRLifts — Test Environment Setup Guide

**Version:** 1.0
**Last updated:** April 2026
**Owners:** DevOps Lead + QA Lead
**Audience:** All developers (human and Claude Code)

> This guide gets a new developer (or a new Claude Code session) from
> zero to a running test suite in a single sitting.
> Follow every step in order. Do not skip steps.

---

## Prerequisites

You need the following installed before starting:

| Tool | Version | Install |
|---|---|---|
| Xcode | 16+ | Mac App Store |
| Python | 3.12+ | `brew install python@3.12` |
| PostgreSQL client | 15+ | `brew install postgresql@15` |
| Git | Any | Included with Xcode CLI tools |
| Homebrew | Any | `brew.sh` |

---

## Repository Setup

```bash
# Clone the repository
git clone https://github.com/your-org/prlifts.git
cd prlifts

# Verify structure
ls
# ios-app/    core-library/    backend/    docs/
```

---

## iOS / Core Library Test Environment

### 1. Open the Xcode project

```bash
open ios-app/PRLifts.xcodeproj
```

Xcode will resolve Swift Package Manager dependencies automatically.
Wait for "Resolving packages" to complete in the status bar before proceeding.

### 2. Verify scheme configuration

1. Select the `PRLifts` scheme from the scheme selector
2. Product → Scheme → Edit Scheme
3. Under **Test**, confirm:
   - Code coverage is enabled
   - The `PRLiftsTests` and `PRLiftsCoreLibraryTests` targets are checked
   - `PRLiftsUITests` is checked

### 3. Run the Core Library tests

```bash
# From the repository root
xcodebuild test \
  -scheme PRLifts \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  -testPlan CoreLibraryTests \
  | xcpretty
```

Or in Xcode: `Cmd + U` with a simulator selected.

### 4. Verify test coverage

After tests run:
1. Xcode → Product → Show Build Folder in Finder
2. Open the `.xcresult` bundle
3. Coverage should be at or above 90% for the Core Library targets

---

## Backend Test Environment

### 1. Create a Python virtual environment

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows (not recommended for this project)
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt   # test dependencies
pip audit                             # verify no known vulnerabilities
```

### 3. Set up the test database

The test suite uses a separate PostgreSQL database from development.
Never run tests against the development or staging database.

**Option A — Local PostgreSQL (recommended)**

```bash
# Start PostgreSQL (if using Homebrew)
brew services start postgresql@15

# Create the test database and user
psql postgres << 'SQL'
CREATE DATABASE prlifts_test;
CREATE USER prlifts_test_user WITH PASSWORD 'prlifts_test_password';
GRANT ALL PRIVILEGES ON DATABASE prlifts_test TO prlifts_test_user;
SQL
```

**Option B — Docker PostgreSQL**

```bash
docker run -d \
  --name prlifts-test-db \
  -e POSTGRES_DB=prlifts_test \
  -e POSTGRES_USER=prlifts_test_user \
  -e POSTGRES_PASSWORD=prlifts_test_password \
  -p 5432:5432 \
  postgres:15
```

### 4. Configure test environment variables

```bash
# Create test environment file (never commit this file)
cp .env.test.example .env.test
```

Edit `.env.test`:

```env
# Test database
DATABASE_URL=postgresql+asyncpg://prlifts_test_user:prlifts_test_password@localhost:5432/prlifts_test

# Test Redis (Upstash test instance or local)
REDIS_URL=redis://localhost:6379/1    # use DB 1 to separate from dev

# AI providers — use mock by default, real only for integration tests
CLAUDE_API_KEY=test_key               # mocked in unit tests
FAL_AI_API_KEY=test_key               # mocked in unit tests
EXERCISEDB_API_KEY=test_key           # mocked in unit tests

# Supabase — test project (separate from dev/staging)
SUPABASE_URL=https://your-test-project.supabase.co
SUPABASE_SERVICE_KEY=your-test-service-key

# Test configuration
ENVIRONMENT=test
LOG_LEVEL=WARNING                     # suppress INFO logs during tests
AI_PROVIDERS_MOCKED=true              # all AI calls use mocks by default
```

**Note on AI keys in tests:**
Unit tests never call real AI providers — `pytest-mock` intercepts all calls.
Integration tests use a separate configuration flag `AI_PROVIDERS_MOCKED=false`.
Never run integration tests that call real providers in CI — the cost and
non-determinism make them unsuitable for automated gates.

### 5. Run database migrations in test database

```bash
# Apply migrations to the test database
DATABASE_URL=postgresql+asyncpg://prlifts_test_user:prlifts_test_password@localhost:5432/prlifts_test \
python seeds/run_migrations.py

# Seed exercise library for tests (required for exercise-dependent tests)
DATABASE_URL=... \
python seeds/seed_exercises.py --env test

# Seed prompt templates
DATABASE_URL=... \
python seeds/seed_prompt_templates.py --env test
```

### 6. Start test Redis (if using local)

```bash
# If not using Docker Redis from step 3
brew services start redis

# Verify Redis is running
redis-cli ping
# Expected: PONG
```

### 7. Run the test suite

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=term-missing --cov-fail-under=90

# Run specific test file
pytest tests/services/test_pr_detection.py -v

# Run tests by marker
pytest -m "not integration" -v      # unit tests only
pytest -m "security" -v             # security-tagged tests only
pytest -m "integration" -v         # integration tests (requires real services)

# Run with verbose output and no coverage (faster for development)
pytest -v --no-cov
```

### 8. Verify the coverage gate

```bash
pytest --cov=app --cov-fail-under=90
# Exit code 0: coverage >= 90%, all tests pass
# Exit code 1: tests failed
# Exit code 2: coverage below 90%
```

---

## Running Both iOS and Backend Tests

For a full V1 test run before submitting a PR:

```bash
# Backend (from backend/)
source .venv/bin/activate
pytest --cov=app --cov-fail-under=90

# iOS Core Library (from repo root)
xcodebuild test \
  -scheme PRLifts \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  -testPlan CoreLibraryTests \
  | xcpretty
```

---

## CI Environment (GitHub Actions)

The CI pipeline runs these steps automatically on every PR.
You should not need to configure this — it is already set up.
This section explains what CI does so you can reproduce it locally.

```yaml
# .github/workflows/backend-ci.yml (simplified)
- name: Run migrations
  run: python seeds/run_migrations.py
  env:
    DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}

- name: Seed test data
  run: python seeds/seed_exercises.py --env test

- name: Run tests with coverage
  run: pytest --cov=app --cov-fail-under=90
```

```yaml
# Xcode Cloud workflow (simplified)
- xcodebuild test
  -scheme PRLifts
  -testPlan CoreLibraryTests
  -enableCodeCoverage YES
```

---

## Common Issues

### "No module named 'app'"

You are not in the `backend/` directory, or the virtual environment is
not activated. Run `source .venv/bin/activate` and `cd backend`.

### "Database connection refused"

PostgreSQL is not running. Run `brew services start postgresql@15`
or start the Docker container.

### "Exercise not found" in tests

The exercise seed has not been run for the test database.
Run `python seeds/seed_exercises.py --env test`.

### Xcode "No such module 'XCTest'"

The test target is not correctly configured. Verify the scheme includes
the test targets (step 2 of iOS setup).

### Tests fail with "API key invalid"

AI provider calls are leaking through the mock. Verify
`AI_PROVIDERS_MOCKED=true` is set in `.env.test` and that the mock
is applied at the correct injection point.

### Coverage below 90%

Run `pytest --cov=app --cov-report=html` and open `htmlcov/index.html`
to see exactly which lines are not covered. Add tests for uncovered paths
before opening the PR.

