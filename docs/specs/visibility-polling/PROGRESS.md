# Progress: visibility-polling

## Status: COMPLETE

## Slices
- [x] Slice 1: GainerPanel.tsx — visibility handler — COMPLETE (2026-05-28)
- [x] Slice 2: TopGainersSidebar.tsx — visibility handler — COMPLETE (2026-05-28)
- [x] Slice 3: MarketStrengthBar.tsx — visibility handler + restartInterval extract — COMPLETE (2026-05-28)
- [x] Slice 4: Playwright visibility tests — COMPLETE (2026-05-28)

## Current
All slices complete. Sprint gates pass.

Last updated: 2026-05-28

## Fix Attempts
| Test/File | Attempts | Last Error |
|-----------|----------|------------|
| test_visibility_polling.py | 3 | localStorage.clear() on about:blank; wait_for_request() API; old prod build |

## Notes
- Spec approved 2026-05-28, Frank verdict SHIP with Playwright version gate condition
- Playwright 1.58.0 confirmed (> 1.45 required for page.clock)
- Tests run via Python pytest-playwright, not Node.js — spec pseudo-code was TypeScript
- Production build must be rebuilt before visibility tests can pass (run_playwright_qc.sh handles this)
- run_playwright_qc.sh updated to include test_visibility_polling.py
- Roadmap Done-When corrected: MarketStrengthBar clearInterval expect: 3 (not 2) — restartInterval adds a net-new clearInterval that GainerPanel/TopGainersSidebar didn't need

## Sprint Closure Gates — ALL PASS
- Gate 1 (tsc --noEmit): PASS
- Gate 2 (run_playwright_qc.sh): PASS — 38/39 tests pass (1 skip: market hours guard)
- Gate 3 (check-no-raw-hex.sh): PASS
