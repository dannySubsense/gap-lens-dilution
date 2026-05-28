# Roadmap: Visibility-Aware Polling (DDR-02)

**Feature:** Pause polling when browser tab is hidden; resume with immediate fetch on return.
**Status:** DRAFT
**Created:** 2026-05-28
**Author:** @planner

---

## Slice Overview

| Slice | Goal | Depends On | Parallel-safe? |
|-------|------|------------|----------------|
| 1 | Modify `GainerPanel.tsx` — add visibility handler | — | Yes (start here) |
| 2 | Modify `TopGainersSidebar.tsx` — add visibility handler | Slice 1 complete | No — sequential |
| 3 | Modify `MarketStrengthBar.tsx` — add visibility handler + extract `restartInterval` | Slice 2 complete | No — sequential |
| 4 | Write and run Playwright visibility tests (4 assertions) | Slice 3 + tsc clean | No — final gate |

---

## Sequence Rules

1. Slices are executed sequentially in order 1 → 2 → 3 → 4. None may begin until the previous slice's Done-When criteria all exit 0.
2. `GainerPanel` and `TopGainersSidebar` share an identical structural pattern (same `intervalRef`, `isMountedRef`, `startInterval`, `handleManualRefresh`). Doing them consecutively (Slices 1 → 2) lets the second be verified quickly as a structural copy of the first.
3. `MarketStrengthBar` differs in structure (no `isMountedRef`, no `startInterval`, no manual refresh, inline `load()` async pattern) and is isolated to Slice 3 to keep the error surface small.
4. `npx tsc --noEmit` must pass after each individual slice (Slices 1, 2, 3). A compilation failure in any slice is a blocker — do not proceed to the next slice until it is resolved.
5. Playwright tests (Slice 4) are written after all three components are modified and `tsc` is clean. Do not write tests against partially modified components.
6. If blocked at any slice → HALT. Do not skip ahead.

---

## Slice 1: GainerPanel.tsx — Visibility Handler

**Goal:** Add Page Visibility API integration to `GainerPanel.tsx` so that polling pauses on `'hidden'` and resumes with an immediate fetch on `'visible'`.

**Depends On:** —

**Files Touched:**
- `frontend/src/components/GainerPanel.tsx` — modify

**Pre-Change Verification**

Run all four commands and confirm counts match exactly before making any edit. If any count differs, stop and investigate.

```bash
grep -c "setInterval"         frontend/src/components/GainerPanel.tsx   # expect: 2
grep -c "clearInterval"       frontend/src/components/GainerPanel.tsx   # expect: 3
grep -c "addEventListener"    frontend/src/components/GainerPanel.tsx   # expect: 0
grep -c "removeEventListener" frontend/src/components/GainerPanel.tsx   # expect: 0
```

**Implementation Steps:**

1. At the top of the polling `useEffect` body (before any other logic), add the SSR guard:
   ```typescript
   if (typeof window === 'undefined') return;
   ```
2. Define `handleVisibilityChange` as a named function inside the `useEffect` (after the SSR guard, before the existing `startInterval` call):
   ```typescript
   function handleVisibilityChange() {
     if (document.visibilityState === 'hidden') {
       if (intervalRef.current !== null) {
         clearInterval(intervalRef.current);
         intervalRef.current = null;
       }
     } else {
       fetchAndUpdate(false);
       startInterval();
     }
   }
   ```
3. Register the listener immediately after the function definition:
   ```typescript
   document.addEventListener('visibilitychange', handleVisibilityChange);
   ```
4. Wrap the existing `fetchAndUpdate(true).then(startInterval)` mount call in a visibility branch:
   ```typescript
   if (document.visibilityState === 'hidden') {
     // Background-tab mount: defer first fetch until visible.
   } else {
     fetchAndUpdate(true).then(() => {
       if (isMountedRef.current) startInterval();
     });
   }
   ```
5. In the cleanup `return () => { ... }` block, add after the existing `clearInterval`:
   ```typescript
   document.removeEventListener('visibilitychange', handleVisibilityChange);
   ```
6. Do not touch `handleManualRefresh`, component props, JSX, or any state shape.

**Effect dependency array:** remains `[fetchFn]` — no new dependencies.

**Done When:**

All commands below must exit 0 (or produce the exact expected numeric output):

```bash
# Post-change grep counts — all four must match exactly
grep -c "setInterval"         frontend/src/components/GainerPanel.tsx   # expect: 2
grep -c "clearInterval"       frontend/src/components/GainerPanel.tsx   # expect: 4
grep -c "addEventListener"    frontend/src/components/GainerPanel.tsx   # expect: 1
grep -c "removeEventListener" frontend/src/components/GainerPanel.tsx   # expect: 1

# SSR guard present (baseline was 0; expect exactly 1 after the guard is added)
grep -c "typeof window" frontend/src/components/GainerPanel.tsx   # expect: 1

# TypeScript clean
cd frontend && npx tsc --noEmit   # exit code 0, zero errors
```

---

## Slice 2: TopGainersSidebar.tsx — Visibility Handler

**Goal:** Apply the identical six-step visibility handler pattern to `TopGainersSidebar.tsx`.

**Depends On:** Slice 1 Done-When criteria all pass.

**Files Touched:**
- `frontend/src/components/TopGainersSidebar.tsx` — modify

**Pre-Change Verification**

```bash
grep -c "setInterval"         frontend/src/components/TopGainersSidebar.tsx   # expect: 2
grep -c "clearInterval"       frontend/src/components/TopGainersSidebar.tsx   # expect: 3
grep -c "addEventListener"    frontend/src/components/TopGainersSidebar.tsx   # expect: 0
grep -c "removeEventListener" frontend/src/components/TopGainersSidebar.tsx   # expect: 0
```

**Implementation Steps:**

Apply the exact same six modifications from Slice 1 to `TopGainersSidebar.tsx`. Structure is identical — `intervalRef`, `isMountedRef`, `fetchAndUpdate`, `startInterval`, `handleManualRefresh` are all present with the same roles.

1. SSR guard at top of polling `useEffect`.
2. Define `handleVisibilityChange` inside the `useEffect`.
3. Register `document.addEventListener('visibilitychange', handleVisibilityChange)`.
4. Wrap existing mount fetch+interval call in visibility branch.
5. Add `document.removeEventListener('visibilitychange', handleVisibilityChange)` to cleanup.
6. Do not touch `handleManualRefresh`, component props, JSX, or state shape.

**Effect dependency array:** remains `[fetchAndUpdate, startInterval]` — no new dependencies.

**Done When:**

```bash
# Post-change grep counts
grep -c "setInterval"         frontend/src/components/TopGainersSidebar.tsx   # expect: 2
grep -c "clearInterval"       frontend/src/components/TopGainersSidebar.tsx   # expect: 4
grep -c "addEventListener"    frontend/src/components/TopGainersSidebar.tsx   # expect: 1
grep -c "removeEventListener" frontend/src/components/TopGainersSidebar.tsx   # expect: 1

# SSR guard present (baseline was 0; expect exactly 1 after the guard is added)
grep -c "typeof window" frontend/src/components/TopGainersSidebar.tsx   # expect: 1

# TypeScript clean
cd frontend && npx tsc --noEmit   # exit code 0, zero errors
```

---

## Slice 3: MarketStrengthBar.tsx — Visibility Handler + restartInterval Extract

**Goal:** Add Page Visibility API integration to `MarketStrengthBar.tsx`. This component differs structurally — it uses a single `useEffect([])` with an inline `async load()`, has no `isMountedRef`, no `startInterval` helper, and no manual refresh button. A local `restartInterval` helper must be extracted inside the effect.

**Depends On:** Slice 2 Done-When criteria all pass.

**Files Touched:**
- `frontend/src/components/MarketStrengthBar.tsx` — modify

**Pre-Change Verification**

```bash
grep -c "setInterval"         frontend/src/components/MarketStrengthBar.tsx   # expect: 2
grep -c "clearInterval"       frontend/src/components/MarketStrengthBar.tsx   # expect: 1
grep -c "addEventListener"    frontend/src/components/MarketStrengthBar.tsx   # expect: 0
grep -c "removeEventListener" frontend/src/components/MarketStrengthBar.tsx   # expect: 0
```

**Implementation Steps:**

1. At the top of the `useEffect` body, add SSR guard:
   ```typescript
   if (typeof window === 'undefined') return;
   ```
2. After the SSR guard (before the existing `async function load()` definition), define a local `restartInterval` helper that wraps the pump-and-dump poll interval:
   ```typescript
   function restartInterval() {
     if (intervalRef.current !== null) clearInterval(intervalRef.current);
     intervalRef.current = setInterval(async () => {
       // existing pump-and-dump poll body
     }, 300_000);
   }
   ```
   Replace the existing inline `setInterval(...)` call inside `load()` with a call to `restartInterval()`.
3. Define `handleVisibilityChange` inside the `useEffect`:
   ```typescript
   function handleVisibilityChange() {
     if (document.visibilityState === 'hidden') {
       if (intervalRef.current !== null) {
         clearInterval(intervalRef.current);
         intervalRef.current = null;
       }
     } else {
       // Resume: call the pump-and-dump poll inline function, then restart interval.
       // Do NOT call load() — that is the one-time full fetch; only the repeating
       // pump-and-dump poll fires on visibility resume.
       fetchPumpAndDumpList(/* existing args */).then(/* existing handler */);
       restartInterval();
     }
   }
   ```
4. Register the listener:
   ```typescript
   document.addEventListener('visibilitychange', handleVisibilityChange);
   ```
5. Wrap the `load()` call in a visibility branch for the interval start only:
   ```typescript
   if (document.visibilityState === 'hidden') {
     // Background-tab mount: always call load() for one-time market-strength fetch,
     // but do NOT start the repeating interval.
     load();  // populates market strength data; interval deferred until visible
   } else {
     // Normal visible mount: existing behavior — load() then interval (now via restartInterval inside load).
     load();
   }
   ```
   Note: If `load()` currently calls `setInterval` inline at its end, that call is replaced by `restartInterval()` in step 2. The visibility branch controls whether `restartInterval()` is reached inside `load()` by checking visibility there, or by restructuring `load()` to not call `restartInterval()` directly — instead, the branch above calls `restartInterval()` only in the visible case after `load()` resolves. Exact structure must follow the actual `load()` body as read.
6. Add `removeEventListener` to the existing cleanup `return () => { ... }`:
   ```typescript
   document.removeEventListener('visibilitychange', handleVisibilityChange);
   ```
   The existing `if (intervalRef.current) clearInterval(intervalRef.current)` in cleanup is preserved unchanged.

**Effect dependency array:** remains `[]`.

**No changes to:** component props, JSX, state shape, `fetchMarketStrength` or `fetchPumpAndDumpList` call signatures.

**Done When:**

```bash
# Post-change grep counts
grep -c "setInterval"         frontend/src/components/MarketStrengthBar.tsx   # expect: 2
grep -c "clearInterval"       frontend/src/components/MarketStrengthBar.tsx   # expect: 3
grep -c "addEventListener"    frontend/src/components/MarketStrengthBar.tsx   # expect: 1
grep -c "removeEventListener" frontend/src/components/MarketStrengthBar.tsx   # expect: 1

# SSR guard present (baseline was 0; expect exactly 1 after the guard is added)
grep -c "typeof window" frontend/src/components/MarketStrengthBar.tsx   # expect: 1

# TypeScript clean across all three modified files
cd frontend && npx tsc --noEmit   # exit code 0, zero errors
```

---

## Slice 4: Playwright Visibility Tests

**Goal:** Write and run four automated Playwright assertions verifying (1) polling stops when hidden, (2) immediate fetch fires on visible, (3) no interval accumulation after multiple cycles, and (4) manual refresh fires even when the tab is simulated hidden. All existing tests must continue to pass.

**Depends On:** Slice 3 Done-When criteria all pass — all three components modified, `tsc` clean.

**Files Touched:**
- `frontend/tests/` or `tests/` — add a new test file (e.g., `visibility-polling.spec.ts`) or a new `describe` block in an existing file, per the project's Playwright file conventions.

**Pre-Change Verification**

Run both checks before writing a single line of test code. Both must pass.

**Step 1 — Playwright version gate (HALT condition)**

```bash
grep '"@playwright/test"' frontend/package.json
```

Record the version. `page.clock.tick()` requires `@playwright/test >= 1.45.0`. If the installed version is below 1.45, **HALT immediately and report** — do not write tests, do not improvise an alternative API. The version discrepancy must be surfaced to the orchestrator before proceeding.

**Step 2 — Existing suite must be green**

```bash
bash scripts/run_playwright_qc.sh   # must exit 0 before new tests are added
```

If this fails, stop. Existing regressions must be resolved before adding new tests.

**Implementation Steps:**

Write a Playwright test suite containing at minimum the following four assertions:

**Assertion 1 — Hidden stops polling**

Override `document.visibilityState` to `'hidden'` and dispatch a synthetic `visibilitychange` event. Advance the Playwright clock by the full interval duration (65 000 ms covers the 60 s gainer intervals). Assert that zero fetch requests to the gainer polling endpoints fired during the hidden window.

Conceptual structure:
```typescript
// Set up route interception counting requests to /api/gainers, /api/massive-gainers
// Navigate to /test and wait for initial load
// Simulate hidden:
await page.evaluate(() => {
  Object.defineProperty(document, 'visibilityState', { value: 'hidden', configurable: true });
  document.dispatchEvent(new Event('visibilitychange'));
});
// Advance clock past full interval
await page.clock.tick(65_000);
// Assert request count === 0 for polling endpoints during hidden window
```

**Assertion 2 — Visible triggers immediate fetch**

After establishing the hidden state from Assertion 1, simulate return to visible. Assert that a fetch to the polling endpoint fires within 1 000 ms — not after the 60 000 ms interval.

Conceptual structure:
```typescript
const requestPromise = page.waitForRequest(
  url => url.includes('/api/gainers'),
  { timeout: 1_000 }  // must fire within 1s, not after 60s
);
await page.evaluate(() => {
  Object.defineProperty(document, 'visibilityState', { value: 'visible', configurable: true });
  document.dispatchEvent(new Event('visibilitychange'));
});
await requestPromise;  // resolves only if fetch fires within 1000ms; test fails if it times out
```

**Assertion 3 — No interval accumulation after multiple hide/show cycles**

Perform 3 successive hide/show cycles via `page.evaluate`. After the final visible transition, count fetch requests during a 60 s window. Assert exactly 1 request fires (the immediate resume fetch) — not 2x or 3x.

Conceptual structure:
```typescript
for (let i = 0; i < 3; i++) {
  // simulate hidden → visible
}
// Intercept and count requests over the next 60s window
// Assert count === 1
```

**Assertion 4 — Manual refresh fires regardless of visibility state**

Simulate the tab as hidden (override `visibilityState` to `'hidden'` and dispatch `visibilitychange`). With the tab in the hidden state, click the GainerPanel manual-refresh button. Assert that a fetch request to the gainer polling endpoint fires and completes — the manual refresh must not be blocked by the visibility pause.

Scope: `GainerPanel` only (the manual-refresh button rendered in the main panel). `TopGainersSidebar` may be included as a secondary assertion if convenient, but is not required. `MarketStrengthBar` has no manual refresh button and is excluded.

Conceptual structure:
```typescript
// Navigate to /test and wait for initial load
// Simulate hidden:
await page.evaluate(() => {
  Object.defineProperty(document, 'visibilityState', { value: 'hidden', configurable: true });
  document.dispatchEvent(new Event('visibilitychange'));
});
// Confirm polling is paused (advance clock, assert no automatic fetch)
// Set up request interception for the manual-refresh fetch
const requestPromise = page.waitForRequest(
  url => url.includes('/api/gainers'),
  { timeout: 3_000 }
);
// Click the manual-refresh button
await page.getByRole('button', { name: /refresh/i }).first().click();
// Assert the fetch fired — manual refresh bypasses visibility pause
await requestPromise;
```

**Done When:**

```bash
# All existing tests plus new visibility tests must pass
bash scripts/run_playwright_qc.sh   # exit code 0, all tests pass

# Design token compliance check (no regressions — no new JSX was added, but confirm)
bash scripts/check-no-raw-hex.sh   # exit code 0
```

The four new Playwright assertions (hidden-stops-polling, visible-immediate-fetch, no-accumulation, manual-refresh-while-hidden) must all be present in the test file and must pass:

```bash
# Confirm the assertion identifiers exist in the test file
grep -c "visibilitychange" tests/visibility-polling.spec.ts   # expect: >= 4
# (or the actual path to the new test file)
```

---

## Sprint Closure Gate

All three gates must exit 0 before this sprint is marked COMPLETE. Sprint status in PROGRESS.md must not be updated to COMPLETE until all three commands pass.

### Gate 1 — TypeScript Compilation

```bash
cd frontend && npx tsc --noEmit
```

Required: zero errors, exit code 0.

### Gate 2 — Playwright QC

```bash
bash scripts/run_playwright_qc.sh
```

Required: all tests pass (existing + new visibility tests), exit code 0.

### Gate 3 — Design Token Compliance

```bash
bash scripts/check-no-raw-hex.sh
```

Required: exit code 0. This sprint adds no new JSX, so this should trivially pass, but it must be confirmed.

All three gates must pass. A sprint where Gate 1 and Gate 3 pass but Gate 2 fails is not COMPLETE.

---

## Dependency Map

| Slice | Input Required | Output Produced |
|-------|---------------|-----------------|
| Slice 1 | Pre-change grep counts verified | `GainerPanel.tsx` modified; `tsc` clean |
| Slice 2 | Slice 1 Done-When passed | `TopGainersSidebar.tsx` modified; `tsc` clean |
| Slice 3 | Slice 2 Done-When passed | `MarketStrengthBar.tsx` modified; `tsc` clean |
| Slice 4 | All three files modified; `tsc` clean; existing Playwright suite green | New visibility tests written; full QC suite passes |

No circular dependencies.

---

## Deferred Items — Not In This Sprint

The following items are explicitly out of scope and must not be implemented in this sprint:

| Item | Reason | Next Step |
|------|---------|-----------|
| Stage 2: idle-timer polling pause | Deferred pending Stage 1 production data. No spec exists. | Revisit after Stage 1 ships; create DDR-02-Stage2 if warranted. |
| Centralized `useVisibility()` hook | Architecture decision (Option A chosen). Option B is not selected. | Revisit only if a third/fourth non-polling consumer of visibility state emerges — e.g., when Stage 2 idle detection ships. |
| Visual resume indicator (toast, badge, "refreshed at HH:MM") | Explicitly excluded by requirements. Silent resume is the specified behavior. | Not planned. |
| Backend changes | No backend changes required. Frontend-only sprint. | N/A |
| TradingView Advanced Chart embed | Third-party; not accessible. | N/A |
| New polling sources or watchlist quote polling | Out of scope per requirements. | N/A |
