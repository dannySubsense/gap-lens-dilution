#!/usr/bin/env bash
# run_backend_qc.sh — Backend/unit pytest gate for gap-lens-dilution.
#
# Purpose:
#   Runs the full backend/unit test suite under tests/ and exits non-zero on any
#   failure or collection error. This is the companion to scripts/run_playwright_qc.sh
#   (which owns the browser/Playwright gate). It exists because the backend test
#   corpus silently rotted once — 40 stale failures + 3 uncollectable files accreted
#   while no gate ran them (see the 2026-06-03 tests-audit). This script is the guard
#   against a repeat.
#
# Scope:
#   Excludes the browser-driven suites, which require a live frontend + backend and
#   Playwright, and are run separately by run_playwright_qc.sh:
#     - tests/test_playwright_qc.py      (Playwright QC gate)
#     - tests/test_visibility_polling.py (Playwright)
#     - tests/test_tradingview_chart.py  (Playwright; currently untracked/unverified)
#
# Usage:
#   bash scripts/run_backend_qc.sh
#
# Exit code: pytest's exit code (0 = all passed; non-zero = failure or collection error).

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

PYTHON="${PYTHON:-python3}"

exec "$PYTHON" -m pytest tests/ \
  --ignore=tests/test_playwright_qc.py \
  --ignore=tests/test_visibility_polling.py \
  --ignore=tests/test_tradingview_chart.py \
  -p no:cacheprovider \
  "$@"
