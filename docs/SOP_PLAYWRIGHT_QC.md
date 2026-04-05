# SOP: Playwright QC — gap-lens-dilution

**Version**: 1.0
**Last updated**: 2026-04-05
**Owner**: Orchestrator

---

## Purpose

The Playwright QC suite is the required final gate before any forge sprint is closed or any deployment is made. It exercises the full stack — real browser, real CORS, real HTTP, real UX flows — and catches bugs that are invisible to TypeScript compilation and manual testing.

---

## When to Run

| Trigger | Required? |
|---------|-----------|
| End of every forge sprint (all slices complete) | Yes — mandatory before sprint closure |
| Before any production deployment | Yes |
| After any change to API routes, middleware, or CORS config | Yes |
| After any change to frontend fetch logic, state management, or localStorage | Yes |
| After routine bug fixes not touching the above | Recommended |
| During standard development iteration | No — use tsc + manual testing instead |

---

## Prerequisites

1. Both services must NOT be running before the script starts (it manages them)
2. The `.env` file must be populated with API keys (ASKEDGAR_API_KEY, MASSIVE_API_KEY, FMP_API_KEY)
3. `frontend/.env.local` must have `NEXT_PUBLIC_API_BASE=http://100.70.21.69:8000`
4. Frontend must be built (`cd frontend && npx next build`)
5. Playwright + Chromium must be installed:
   ```bash
   pip3 install playwright
   playwright install chromium
   ```

---

## How to Run

```bash
cd /home/d-tuned/projects/gap-lens-dilution
bash scripts/run_playwright_qc.sh
```

The script handles the full lifecycle automatically:
1. Clears ports 8000 and 3001
2. Starts uvicorn backend on port 8000
3. Starts Next.js frontend on port 3001 (production build)
4. Polls until both services are ready (max 90s)
5. Runs browser + API tests via headless Chromium
6. Stops both services
7. Exits with pytest's exit code (0 = pass, non-zero = fail)

---

## Pass Criteria

All tests must pass. Any failure is a blocker — the sprint is not closed until all pass.

---

## What Tests Should Cover

Tests are defined per-sprint based on the features delivered. At minimum, every sprint's QC suite must verify:

| Category | What It Verifies |
|----------|-----------------|
| Page load | Dashboard loads at Tailscale IP, no JS errors |
| Layout | All expected columns/panels render |
| API health | Backend responds with correct JSON shape |
| Core interaction | Clicking a gainer loads charts + dilution data |
| New feature UX | Each new feature from the sprint's roadmap is exercised end-to-end |
| State persistence | localStorage-backed settings survive refresh |
| Edge cases | Empty states, duplicate actions, missing data |

The specific test count and test IDs are defined in `tests/test_playwright_qc.py` and updated each sprint.

---

## On Failure

1. **Read the failure message** — Playwright prints the failing assertion and a call log showing what it was waiting for.

2. **Check the service logs:**
   ```bash
   tail -50 /tmp/uvicorn_qc.log
   tail -50 /tmp/nextjs_qc.log
   ```

3. **Classify the failure:**

   | Symptom | Likely cause |
   |---------|-------------|
   | All panels show errors | CORS misconfiguration |
   | Backend crash in log | Unhandled exception or concurrency issue |
   | Element not found | API returning wrong data, or component not rendering |
   | `httpx.ConnectError` | Backend crashed mid-run |
   | `Timeout exceeded` | Slow API response or frontend rendering delay |

4. **Fix the root cause** — do not adjust test timeouts to paper over real bugs.

5. **Re-run the full suite** to confirm all pass before closing.

---

## Relation to Other Checks

| | TypeScript (`npx tsc --noEmit`) | Playwright QC |
|--|--------------------------------|---------------|
| Speed | ~5 seconds | ~30-60 seconds |
| Services required | No | Yes |
| What it catches | Type errors, import issues | CORS, runtime errors, browser rendering, multi-step UX, localStorage |
| Run frequency | Every commit / every iteration | Sprint closure gate + pre-deploy |
| Exit code drives CI | Yes | Yes (sprint gate) |

Both must pass. Neither replaces the other.

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/run_playwright_qc.sh` | Full orchestration (preferred — use this) |
| `tests/test_playwright_qc.py` | Pytest test file (called by the shell script) |
