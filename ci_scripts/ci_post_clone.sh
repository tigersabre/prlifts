#!/usr/bin/env bash
# Xcode Cloud — post-clone lifecycle script.
# Runs automatically after the repository is cloned in every Xcode Cloud build.
#
# Purpose: enforce environment parity between local development and CI.
# Without this, Xcode Cloud can compile with looser concurrency checking than
# local builds, letting data-race warnings reach the reviewer instead of the
# developer.
#
# ── Xcode Cloud workflow configuration ──────────────────────────────────────
#
# Two workflows are configured in App Store Connect:
#
#   1. "PRLifts CI" — triggered on every push and pull request
#      Test action: use test plan PRLifts/PRLiftsCITests.xctestplan
#      Runs: PRLiftsTests only (unit + integration tests)
#      Rationale: Apple infrastructure instability causes AX loaded
#      notification timeouts in PRLiftsUITests on cloud runners; this breaks
#      PRs non-deterministically. UI tests are verified locally via the
#      pre-commit hook before every commit. See ARCHITECTURE.md Decision 91.
#
#   2. "PRLifts Weekly CI" — scheduled trigger
#      Schedule: every Monday at 09:00 UTC, branch: main
#      Test action: use test plan PRLifts/PRLiftsWeeklyTests.xctestplan
#      Runs: PRLiftsTests + PRLiftsUITests (full suite)
#      Purpose: weekly signal that the full suite including UI tests is green
#      on main; catches any regressions not blocked by the pre-commit hook.
#
# Both test plans are committed at PRLifts/PRLiftsCITests.xctestplan and
# PRLifts/PRLiftsWeeklyTests.xctestplan respectively.
#
# ────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# Enforce Swift 6 complete concurrency checking on every compilation unit.
# Matches the SWIFT_STRICT_CONCURRENCY=complete setting used locally so that
# the same concurrency warnings and errors surface in both environments.
export SWIFT_STRICT_CONCURRENCY=complete
