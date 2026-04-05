#!/usr/bin/env bash
# =============================================================================
# run_playwright_qc.sh — Full Playwright QC gate for gap-lens-dilution
#
# Steps:
#   1. Kill any processes on ports 8000 and 3001
#   2. Build the frontend (production)
#   3. Start uvicorn backend on port 8000
#   4. Start Next.js frontend on port 3001
#   5. Poll until both services are ready (max 90s each)
#   6. Run pytest against tests/test_playwright_qc.py
#   7. Stop both services
#   8. Exit with pytest's exit code
#
# Usage:
#   cd /home/d-tuned/projects/gap-lens-dilution
#   bash scripts/run_playwright_qc.sh
# =============================================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
LOG_BACKEND="/tmp/uvicorn_qc.log"
LOG_FRONTEND="/tmp/nextjs_qc.log"
BACKEND_PORT=8000
FRONTEND_PORT=3001
WAIT_MAX=90  # seconds to wait for each service

BACKEND_PID=""
FRONTEND_PID=""
PYTEST_EXIT=0

# ── Cleanup on exit ─────────────────────────────────────────────────────────

cleanup() {
    echo ""
    echo "[QC] Stopping services..."

    if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
        wait "$FRONTEND_PID" 2>/dev/null || true
        echo "[QC] Frontend stopped (pid $FRONTEND_PID)"
    fi

    if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
        echo "[QC] Backend stopped (pid $BACKEND_PID)"
    fi
}

trap cleanup EXIT

# ── 1. Clear ports ──────────────────────────────────────────────────────────

echo "[QC] Clearing ports $BACKEND_PORT and $FRONTEND_PORT..."

for PORT in $BACKEND_PORT $FRONTEND_PORT; do
    PIDS="$(lsof -ti tcp:"$PORT" 2>/dev/null || true)"
    if [[ -n "$PIDS" ]]; then
        echo "[QC]   Killing processes on port $PORT: $PIDS"
        echo "$PIDS" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
done

# ── 2. Build frontend ────────────────────────────────────────────────────────

echo "[QC] Building frontend (production)..."
cd "$FRONTEND_DIR"
npx next build 2>&1 | tail -20
echo "[QC] Frontend build complete."

# ── 3. Start backend ────────────────────────────────────────────────────────

cd "$PROJECT_ROOT"
echo "[QC] Starting uvicorn backend on port $BACKEND_PORT..."

if [[ -f "$PROJECT_ROOT/venv/bin/activate" ]]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" >"$LOG_BACKEND" 2>&1 &
BACKEND_PID=$!
echo "[QC] Backend pid: $BACKEND_PID (log: $LOG_BACKEND)"

# ── 4. Start frontend ────────────────────────────────────────────────────────

cd "$FRONTEND_DIR"
echo "[QC] Starting Next.js frontend on port $FRONTEND_PORT..."
npx next start -p "$FRONTEND_PORT" -H 0.0.0.0 >"$LOG_FRONTEND" 2>&1 &
FRONTEND_PID=$!
echo "[QC] Frontend pid: $FRONTEND_PID (log: $LOG_FRONTEND)"

# ── 5. Wait for services ─────────────────────────────────────────────────────

wait_for_service() {
    local url="$1"
    local label="$2"
    local elapsed=0
    echo "[QC] Waiting for $label at $url..."
    while ! curl -sf "$url" -o /dev/null 2>/dev/null; do
        sleep 2
        elapsed=$((elapsed + 2))
        if [[ $elapsed -ge $WAIT_MAX ]]; then
            echo "[QC] ERROR: $label did not become ready within ${WAIT_MAX}s"
            echo "[QC] Last 20 lines of log:"
            tail -20 "${3:-/dev/null}" 2>/dev/null || true
            exit 1
        fi
        echo "[QC]   ...still waiting ($elapsed/${WAIT_MAX}s)"
    done
    echo "[QC] $label is ready."
}

wait_for_service "http://localhost:$BACKEND_PORT/health" "Backend" "$LOG_BACKEND"
wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend" "$LOG_FRONTEND"

# ── 6. Run Playwright QC ─────────────────────────────────────────────────────

cd "$PROJECT_ROOT"
echo ""
echo "[QC] =============================================="
echo "[QC] Running Playwright QC suite..."
echo "[QC] =============================================="
echo ""

python3 -m pytest tests/test_playwright_qc.py -v || PYTEST_EXIT=$?

echo ""
echo "[QC] =============================================="
if [[ $PYTEST_EXIT -eq 0 ]]; then
    echo "[QC] ALL TESTS PASSED — sprint gate: PASS"
else
    echo "[QC] TESTS FAILED (exit code $PYTEST_EXIT) — sprint gate: FAIL"
    echo "[QC] Backend log tail:"
    tail -20 "$LOG_BACKEND" 2>/dev/null || true
    echo "[QC] Frontend log tail:"
    tail -20 "$LOG_FRONTEND" 2>/dev/null || true
fi
echo "[QC] =============================================="

# cleanup() runs via trap EXIT
exit $PYTEST_EXIT
