#!/usr/bin/env bash
# install_hooks.sh — one-time dev setup to point git at the tracked hooks.
# Run once after cloning:
#   bash backend/scripts/install_hooks.sh

set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

git -C "$REPO_ROOT" config core.hooksPath .githooks
chmod +x "$REPO_ROOT/.githooks/pre-commit"

echo "Git hooks installed. Pre-commit will now run ruff check and ruff format --check."
