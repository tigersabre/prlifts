#!/usr/bin/env bash
# Xcode Cloud — post-xcodebuild lifecycle script.
# Runs automatically after the xcodebuild step in every Xcode Cloud build that
# produces an archive (i.e., builds with an Archive action).
#
# Exports the .xcarchive using the ExportOptions plist that matches the active
# workflow. Uses non-deprecated method values per Apple's 2025 deprecation notice:
#   app-store → app-store-connect
#   ad-hoc    → release-testing
#   development → debugging
#
# ── Workflow → export method mapping ────────────────────────────────────────────
#
#   "PRLifts CI"         → app-store-connect  (ExportOptions-AppStore.plist)
#   "PRLifts Weekly CI"  → app-store-connect  (ExportOptions-AppStore.plist)
#   Workflows containing "Ad Hoc" or "Release Testing" in their name
#                        → release-testing    (ExportOptions-AdHoc.plist)
#   Workflows containing "Development" or "Debug" in their name
#                        → debugging          (ExportOptions-Development.plist)
#
# To add a new workflow, add a case to the case statement below.
#
# ────────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPORT_PATH="${CI_DERIVED_DATA_PATH}/Export"

# Select the ExportOptions plist based on the active Xcode Cloud workflow name.
case "${CI_WORKFLOW:-}" in
  *"Ad Hoc"* | *"AdHoc"* | *"Release Testing"* | *"release-testing"*)
    EXPORT_OPTIONS="${SCRIPT_DIR}/ExportOptions-AdHoc.plist"
    ;;
  *"Development"* | *"Debug"* | *"debugging"*)
    EXPORT_OPTIONS="${SCRIPT_DIR}/ExportOptions-Development.plist"
    ;;
  *)
    # Default: App Store Connect distribution.
    # Covers "PRLifts CI", "PRLifts Weekly CI", and any unrecognised workflow name.
    EXPORT_OPTIONS="${SCRIPT_DIR}/ExportOptions-AppStore.plist"
    ;;
esac

echo "ci_post_xcodebuild: workflow=${CI_WORKFLOW:-unknown}"
echo "ci_post_xcodebuild: archive=${CI_ARCHIVE_PATH}"
echo "ci_post_xcodebuild: export_options=${EXPORT_OPTIONS}"
echo "ci_post_xcodebuild: export_path=${EXPORT_PATH}"

xcodebuild -exportArchive \
  -archivePath "${CI_ARCHIVE_PATH}" \
  -exportPath "${EXPORT_PATH}" \
  -exportOptionsPlist "${EXPORT_OPTIONS}"
