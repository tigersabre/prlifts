#!/usr/bin/env bash
# Xcode Cloud — post-clone lifecycle script.
# Runs automatically after the repository is cloned in every Xcode Cloud build.
#
# Purpose: enforce environment parity between local development and CI.
# Without this, Xcode Cloud can compile with looser concurrency checking than
# local builds, letting data-race warnings reach the reviewer instead of the
# developer.

set -euo pipefail

# Enforce Swift 6 complete concurrency checking on every compilation unit.
# Matches the SWIFT_STRICT_CONCURRENCY=complete setting used locally so that
# the same concurrency warnings and errors surface in both environments.
export SWIFT_STRICT_CONCURRENCY=complete
