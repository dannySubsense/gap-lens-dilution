# Spec Review: tradingview-chart-widget

**Version:** 3.0 (Re-review after v1.2 updates)
**Date:** 2026-04-04
**Reviewer:** @spec-reviewer (automated)
**Status:** COMPLETE -- 1 critical gap, 3 minor gaps, 3 risks, 1 open question

**Previous reviews:**
- v1.0: 3 gaps, 5 open questions. All resolved in v1.1.
- v2.0: Verified v1.1 fixes. 0 gaps, 0 open questions. Recommended retryKey additions.
- v3.0 (this review): Full re-review after v1.2 replaces retryKey with selectCount. 1 critical gap found.

---

## Review Summary

This is the third review pass. The v1.2 update replaces the internal `retryKey` mechanism with a `selectCount` prop from `page.tsx`. The change is architecturally sound: it correctly solves the problem that React suppresses re-renders when `setSelectedTicker("AAPL")` is called while the value is already `"AAPL"`. By moving the counter to `page.tsx` and passing it as a prop, every user action (gainer click or search) is visible to the component regardless of whether the ticker value changed.

The `selectCount` mechanism is specified consistently across all four documents. No stale `retryKey` references remain outside of change log entries. However, this review identified one critical gap in the interaction between the `useEffect` cleanup function and the ref-based dedup logic (GAP-01) that would cause a user-facing bug if implemented as written.

---

## Stale retryKey Verification

All `retryKey` references in documents 01-04 were audited. Every occurrence is within a change log entry that explains what was replaced. No operational (non-change-log) references to `retryKey` remain in any of the four spec documents.

| Document | retryKey Occurrences | Location | Allowed? |
|----------|---------------------|----------|----------|
| 01-REQUIREMENTS | 1 | Line 8: change note | Yes (change log) |
| 02-ARCHITECTURE | 1 | Line 9: change log | Yes (change log) |
| 03-UI-SPEC | 1 | Line 14: change log | Yes (change log) |
| 04-ROADMAP | 1 | Line 8: change log | Yes (change log) |

**Verdict: CLEAN.** No stale references.

---

## selectCount Consistency Across All Documents

### Check 1: selectCount Specification

| Document | selectCount Specification | Consistent? |
|----------|--------------------------|-------------|
| 01-REQUIREMENTS line 146 | Constraint: one new state variable (`selectCount`) permitted in `page.tsx` | Yes |
| 01-REQUIREMENTS edge case (line 117) | Same-ticker error retry triggers re-initialization | Yes |
| 02-ARCHITECTURE Props interface (line 105) | `selectCount: number` in `TradingViewChartProps` | Yes |
| 02-ARCHITECTURE Integration Points (lines 161-163) | `useState(0)`, increment in both handlers, passed as prop | Yes |
| 02-ARCHITECTURE Patterns table (line 124) | `useEffect` depends on `[ticker, selectedTimeframe, selectCount]`; ref-based dedup described | Yes |
| 02-ARCHITECTURE State Machine (lines 211, 214) | Two selectCount-driven transitions documented | Yes |
| 02-ARCHITECTURE Requirement Coverage (lines 258-259) | Both same-ticker edge cases covered | Yes |
| 03-UI-SPEC Flow 5 Case B (line 120) | Full selectCount -> useEffect -> dedup -> retry flow | Yes |
| 03-UI-SPEC Interaction: Ticker change (line 295) | `useEffect` dependency includes `selectCount` | Yes |
| 03-UI-SPEC Interaction: Same ticker (lines 330-335) | Both "ready" (no-op) and "error" (retry) cases | Yes |
| 03-UI-SPEC Sections table (line 185) | `selectCount` prop listed in data source | Yes |
| 03-UI-SPEC State Visibility (line 430) | `selectCount` listed with correct update triggers | Yes |
| 04-ROADMAP Dependency Map (line 26) | `selectCount` prop depends on `page.tsx` state | Yes |
| 04-ROADMAP Slice 1 (line 61) | Props: `{ ticker: string | null; selectCount: number }` | Yes |
| 04-ROADMAP Slice 2 (lines 104-107) | `useEffect([ticker, selectedTimeframe, selectCount])` with full dedup | Yes |
| 04-ROADMAP Slice 3 (line 167) | `selectCount` dependency interaction with cleanup | Yes |
| 04-ROADMAP Slice 4 (lines 199-201) | `useState(0)`, increment in both handlers, JSX with prop | Yes |

**Verdict: CONSISTENT across all 4 documents.**

### Check 2: page.tsx Changes

| Aspect | 02-ARCHITECTURE | 04-ROADMAP Slice 4 | Consistent? |
|--------|-----------------|---------------------|-------------|
| Import | `import TradingViewChart` | `import TradingViewChart from "@/components/TradingViewChart"` | Yes |
| State declaration | `const [selectCount, setSelectCount] = useState(0)` | Same | Yes |
| Increment in `handleGainerSelect` | `setSelectCount(c => c + 1)` | Same, "as the first line" | Yes |
| Increment in `handleSearch` | `setSelectCount(c => c + 1)` | Same, "as the first line" | Yes |
| JSX insertion point | Between Header and Headlines in conditional block | Same | Yes |
| JSX element | `<TradingViewChart ticker={selectedTicker} selectCount={selectCount} />` | Same | Yes |

**Verdict: CONSISTENT.**

### Check 3: useEffect Dependency Array

| Document | Dependency Array | Consistent? |
|----------|-----------------|-------------|
| 02-ARCHITECTURE Patterns (line 124) | `[ticker, selectedTimeframe, selectCount]` | Yes |
| 03-UI-SPEC Interaction: Ticker change (line 295) | `[ticker, selectedTimeframe, selectCount]` | Yes |
| 03-UI-SPEC State Visibility (line 431) | `[ticker, selectedTimeframe, selectCount]` | Yes |
| 04-ROADMAP Slice 2 (line 104) | `[ticker, selectedTimeframe, selectCount]` | Yes |
| 04-ROADMAP File Summary (line 260) | `[ticker, selectedTimeframe, selectCount]` | Yes |

**Verdict: CONSISTENT.**

### Check 4: Ref-Based Dedup Logic

| Document | Dedup Specification | Consistent? |
|----------|---------------------|-------------|
| 02-ARCHITECTURE Patterns (line 124) | Refs track prev ticker/timeframe; ready -> early return; error -> proceed | Yes |
| 02-ARCHITECTURE State Machine (lines 211-214) | error+selectCount -> loading; ready+selectCount -> ready (no-op) | Yes |
| 03-UI-SPEC Interaction: Ticker change (line 306) | Dedup paragraph matches architecture | Yes |
| 03-UI-SPEC Interaction: Same ticker (lines 330-335) | ready -> no-op; error -> retry | Yes |
| 04-ROADMAP Slice 2 (lines 106-107) | Full dedup: compare refs, check statusRef for ready/error/loading | Yes |

**Verdict: CONSISTENT.** The dedup logic is identically described everywhere.

### Check 5: Widget Config

| Config Field | 02-ARCHITECTURE | 04-ROADMAP Slice 2 | 03-UI-SPEC | Consistent? |
|--------------|-----------------|---------------------|------------|-------------|
| `hide_top_toolbar` | `true` | `true` | N/A (out-of-scope reminder) | Yes |
| `allow_symbol_change` | `false` | `false` | N/A | Yes |
| `theme` | `"dark"` | `"dark"` | `theme: "dark"` (State 3) | Yes |
| `backgroundColor` | `"#1b2230"` | `"#1b2230"` | `"#1b2230"` (State 3) | Yes |
| `gridColor` | `"#2a3447"` | `"#2a3447"` | `"#2a3447"` (State 3) | Yes |
| `autosize` | `true` | `true` | `autosize: true` (State 3) | Yes |

**Verdict: CONSISTENT.**

### Check 6: Widget Height

| Document | Value | Consistent? |
|----------|-------|-------------|
| 01-REQUIREMENTS AC US-01 | "minimum height of at least 300px" (floor) | Yes |
| 02-ARCHITECTURE Layout Contract | "min-height: 340px" (340 >= 300) | Yes |
| 03-UI-SPEC States 1-4 | "min-height: 340px" in all states | Yes |
| 04-ROADMAP Slice 1 | `style={{ minHeight: "340px" }}` | Yes |
| 04-ROADMAP Slice 4 Playwright | `toHaveCSS("min-height", "340px")` | Yes |

**Verdict: CONSISTENT.**

### Check 7: Insertion Point in page.tsx

| Document | Statement | Consistent? |
|----------|-----------|-------------|
| 01-REQUIREMENTS Constraint | "between the Header component and the Headlines component" | Yes |
| 02-ARCHITECTURE Integration Points | Inside conditional block, between Header and Headlines | Yes |
| 03-UI-SPEC Component Hierarchy | `Header > TradingViewChart > Headlines` | Yes |
| 04-ROADMAP Slice 4 | "between `<Header .../>` and `<Headlines .../>`" | Yes |
| Codebase (`page.tsx` line 351) | `<Header .../>` immediately followed by `<Headlines .../>` | Verified |

**Verdict: CONSISTENT and verified against codebase.**

### Check 8: Accent Color #a78bfa

| Document | Statement | Consistent? |
|----------|-----------|-------------|
| 01-REQUIREMENTS Constraints | "accent purple `#a78bfa`... not `#8b5cf6`" | Yes |
| 03-UI-SPEC Timeframe Selector | `#a78bfa` for accent; `#8b5cf6` NOT used | Yes |
| 03-UI-SPEC Design Token Reference | `#a78bfa` literal; `#8b5cf6` explicitly excluded | Yes |
| 04-ROADMAP Slice 1 | `border-[#a78bfa]` | Yes |
| 04-ROADMAP Slice 4 Playwright | `border-[#a78bfa]` in test | Yes |

**Verdict: CONSISTENT.**

---

## Requirements Completeness

- [x] Summary is present and clear
- [x] User stories follow "As a... I want... so that..." format (all 8)
- [x] Every user story has acceptance criteria (all 8 have testable ACs)
- [x] Edge cases table is populated (9 cases including same-ticker error retry)
- [x] Out of scope section is not empty (10 exclusions + 2 deferred)
- [x] Constraints are concrete (13 constraints with specific values)
- [x] `selectCount` constraint present (line 146)

### Requirements Gaps

| Gap | Impact |
|-----|--------|
| None found | Requirements document is complete and unambiguous |

---

## Architecture Completeness

- [x] Every requirement has architecture coverage (Coverage Matrix covers all 8 user stories + 4 edge cases)
- [x] Schemas are valid TypeScript
- [x] API contracts are complete (`TradingViewChartProps` with `ticker` and `selectCount`)
- [x] Patterns are justified (8 patterns + 4 anti-patterns)
- [x] Integration points documented
- [x] State machine covers all selectCount-driven transitions

### Requirements -> Architecture Coverage

| Requirement | Architecture Coverage | Status |
|-------------|----------------------|--------|
| US-01: Placement | Integration Points: conditional block insertion | PASS |
| US-02: Gainer click | `ticker` prop; `useEffect` dependency | PASS |
| US-03: Search | Same as US-02 | PASS |
| US-04: Timeframe selector | `ChartTimeframe` + `TIMEFRAME_TO_TV_INTERVAL` + `range` mapping | PASS |
| US-04: Persistence | `selectedTimeframe` not reset on ticker change | PASS |
| US-05: Dark theme | Widget config: theme, backgroundColor, gridColor | PASS |
| US-06: Loading | Skeleton overlay on `status === "loading"` | PASS |
| US-07: Error | `onerror` + try-catch; CSP covered | PASS |
| US-08: Idle | Guard clause; no script injection | PASS |
| Edge: Same ticker (ready) | Ref-based dedup; state machine: ready -> ready (no-op) | PASS |
| Edge: Same ticker (error) | selectCount triggers effect; dedup detects error, proceeds | PASS |
| Edge: Rapid switching | Mounted flag + cleanup + try-catch | PASS -- see GAP-01 |
| Edge: Offline/CDN blocked | `onerror` on script tag | PASS |

---

## UI Spec Completeness

- [x] Every user story has a flow (5 flows covering all stories)
- [x] Every screen has a layout (4 visual states with ASCII wireframes)
- [x] Interactions cover all states (loading, error, success, idle, same-ticker-ready, same-ticker-error)
- [x] Component hierarchy maps to architecture
- [x] `selectCount` mechanism fully specified in Flow 5, Interactions, State Visibility

### Requirements -> UI Coverage

| User Story | Screen/Flow | Status |
|------------|-------------|--------|
| US-01: Placement | Layout Structure; Component Hierarchy | PASS |
| US-02: Gainer click | Flow 1; Interaction: Ticker change | PASS |
| US-03: Search | Flow 2; Interaction: Ticker change | PASS |
| US-04: Timeframe | Flow 3; Timeframe Selector Specification | PASS |
| US-04: Persistence | Flow 3 explicit paragraph | PASS |
| US-05: Dark theme | Design Token Reference; State 3 config | PASS |
| US-06: Loading | State 2 wireframe | PASS |
| US-07: Error | State 4 wireframe; Flow 5 (Cases A and B) | PASS |
| US-07: CSP | Flow 5 error path | PASS |
| US-08: Idle | State 1 wireframe; Flow 4 | PASS |
| Edge: Same ticker (ready) | Interaction: Same ticker re-selected (no-op) | PASS |
| Edge: Same ticker (error) | Interaction: Same ticker re-selected (retry via selectCount); Flow 5 Case B | PASS |
| Edge: Rapid switching | Interaction: Rapid ticker switching | PASS |

---

## Roadmap Completeness

- [x] Every architecture component is in a slice
- [x] Every UI component is in a slice
- [x] No circular dependencies (linear: Slice 1 -> 2 -> 3 -> 4)
- [x] Each slice has "Done When" criteria
- [x] File paths are concrete and match codebase
- [x] `selectCount` introduced progressively across slices

### Architecture -> Roadmap Coverage

| Component | Slice | Status |
|-----------|-------|--------|
| `ChartTimeframe` type | Slice 1 | PASS |
| `TIMEFRAME_TO_TV_INTERVAL` mapping | Slice 1 | PASS |
| Idle placeholder UI | Slice 1 | PASS |
| Loading skeleton UI | Slice 1 | PASS |
| Error message UI | Slice 1 | PASS |
| Timeframe selector UI (with `#a78bfa`) | Slice 1 | PASS |
| `TradingViewChartProps` (incl. `selectCount`) | Slice 1 | PASS |
| Refs (`prevTickerRef`, `prevTimeframeRef`, `statusRef`) | Slice 1 | PASS |
| TradingView script injection | Slice 2 | PASS |
| Widget constructor + try-catch | Slice 2 | PASS |
| `useEffect([ticker, selectedTimeframe, selectCount])` + dedup | Slice 2 | PASS |
| Mounted-flag guard | Slice 3 | PASS |
| Cleanup function | Slice 3 | PASS -- **see GAP-01** |
| `page.tsx` integration (import, selectCount, JSX) | Slice 4 | PASS |
| Playwright verification | Slice 4 | PASS |

---

## Ref-Based Dedup Logic Assessment

The `selectCount` -> `useEffect` -> dedup -> conditional retry flow is assessed here for completeness and implementability.

**The specified algorithm (Slice 2, lines 104-107):**

1. `useEffect` fires because `[ticker, selectedTimeframe, selectCount]` changed.
2. Guard: if `!ticker`, return (idle state).
3. Dedup: compare `ticker` against `prevTickerRef.current` and `selectedTimeframe` against `prevTimeframeRef.current`.
   - If both unchanged AND `statusRef.current === "ready"`: return early (no-op).
   - If both unchanged AND `statusRef.current === "error"`: proceed (forced retry).
   - If both unchanged AND `statusRef.current === "loading"`: return early (already initializing).
   - If either changed: proceed (new ticker or new timeframe).
4. Update refs to current values.
5. Set status to "loading".
6. Clear container innerHTML.
7. Inject script, construct widget.

**Assessment:** The dedup algorithm is logically sound. It correctly distinguishes four scenarios:
- Same ticker + ready = no-op (prevents unnecessary reload)
- Same ticker + error = retry (user-requested recovery)
- Same ticker + loading = no-op (prevents double-init)
- Different ticker = re-init (normal case)

**However:** The interaction between this dedup logic and the cleanup function introduces a critical issue. See GAP-01.

---

## Identified Gaps

### GAP-01 (CRITICAL): Cleanup Function Destroys Chart DOM Before Dedup Can Prevent It

**Documents affected:** 02-ARCHITECTURE (line 260), 04-ROADMAP Slice 3 (lines 166-167)

**The problem:** React's `useEffect` cleanup always runs BEFORE the new effect body executes when a dependency changes. The cleanup function specified in Slice 3 (line 166) performs two actions: (1) sets `mounted = false`, and (2) clears `container.innerHTML`. The dedup check (Slice 2, line 106) runs at the top of the new effect body -- AFTER cleanup has already completed.

**Execution trace for same ticker re-selected while chart is "ready":**

```
1. selectCount increments (N -> N+1).
   React detects dependency change in [ticker, selectedTimeframe, selectCount].

2. React runs CLEANUP from previous effect:
   - mounted = false
   - container.innerHTML = ""     <-- chart widget DOM is destroyed

3. React runs NEW EFFECT BODY:
   - Guard: ticker is not null, passes.
   - Dedup: ticker === prevTickerRef (true),
            selectedTimeframe === prevTimeframeRef (true),
            statusRef === "ready" (true)
   - Returns early (no-op).         <-- chart is NOT rebuilt

4. Result: Chart container is empty. Widget destroyed by cleanup,
   never rebuilt because dedup returned early.
```

**This contradicts:**
- 04-ROADMAP Slice 3 test (line 173): "Selecting the same ticker that is already displayed (in 'ready' state) does not trigger any DOM teardown or re-initialization."
- 02-ARCHITECTURE State Machine (line 214): `ready --(same ticker, selectCount increments)--> ready (no-op)`.
- 03-UI-SPEC Interaction: Same ticker re-selected, active state (line 331): "No re-initialization, no visible flash or reload."
- 01-REQUIREMENTS AC US-02 (line 73): "chart does not reload or flash unnecessarily."

**Recommended fix:** The cleanup function should ONLY set `mounted = false`. It should NOT clear `container.innerHTML`. Container clearing should happen exclusively in the effect body, AFTER the dedup check passes. This is already specified in Slice 2 (line 109): "Clear the chart container's inner HTML before injecting a new widget." With this fix:

- Same ticker + ready: cleanup voids callbacks only; dedup returns early; chart DOM preserved. Correct.
- Same ticker + error: cleanup voids callbacks only; dedup proceeds; effect body clears container and retries. Correct.
- Different ticker: cleanup voids callbacks only; dedup proceeds; effect body clears container and re-inits. Correct.
- Rapid switching: cleanup voids callbacks via mounted flag; new effect clears container and inits. Correct.

The Architecture document's Requirement Coverage Matrix (line 260) should also be updated from "Each `useEffect` cleanup removes previous container children" to "Each `useEffect` cleanup voids in-flight callbacks via a mounted flag."

**Impact:** If implemented as currently specified, same-ticker re-selection on a healthy chart would visibly destroy the chart. This is a user-facing bug.

---

### GAP-02 (MINOR): Slice 3 Test Contradicts Specified Cleanup Behavior

**Document:** 04-ROADMAP Slice 3, line 173

The test states: "Selecting the same ticker that is already displayed (in 'ready' state) does not trigger any DOM teardown or re-initialization (ref-based dedup returns early even though `selectCount` changed)."

This test is correct in INTENT but would fail under the current cleanup specification because cleanup runs before the dedup check. Once GAP-01 is resolved (cleanup only sets `mounted = false`), this test becomes valid. No separate fix required beyond resolving GAP-01.

---

### GAP-03 (MINOR): Dedup Missing "loading" Branch in Architecture and UI Spec

**Documents affected:** 02-ARCHITECTURE Patterns table (line 124); 03-UI-SPEC Interaction: Same ticker re-selected (lines 330-335)

The Roadmap Slice 2 (line 106) specifies three branches: `"ready"` -> early return, `"error"` -> proceed, `"loading"` -> early return. The Architecture Patterns table and UI Spec Interaction sections only document the `"ready"` and `"error"` branches. The `"loading"` case is not mentioned.

**Impact:** Low. The Roadmap is the implementation guide and it is explicit. The `"loading"` branch is a safety guard for the edge case where the user rapidly re-selects the same ticker while it is still initializing. Omission from Architecture and UI Spec does not create implementation ambiguity.

**Recommended fix:** Add "If `status` is `'loading'`, the effect also returns early (already initializing)" to both documents.

---

### GAP-04 (MINOR): Architecture Data Schemas Missing statusRef Sync Pattern

**Document:** 02-ARCHITECTURE Data Schemas (lines 67-71)

The `TradingViewChartState` interface shows `status` and `selectedTimeframe` but does not mention the `statusRef` that must be synced to `status` on every render. The Roadmap Slice 1 (line 63) explicitly specifies this ref and its sync behavior, and the Architecture Patterns table (line 124) references "status (via ref)" -- but the Data Schemas section does not document the ref pattern.

**Impact:** Low. The Roadmap is explicit. An implementer following the Roadmap would not be confused.

---

## Identified Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| TradingView CDN URL changes or widget API breaks | Low | High | Error state (US-07) provides graceful degradation; URL is a single constant |
| `window.TradingView` typed as `any` -- no compile-time config safety | Medium | Low | try-catch around constructor catches runtime errors; error state surfaces failures |
| TradingView iframe injects styles that conflict with dark theme | Low | Medium | `backgroundColor`, `gridColor`, `theme: "dark"` config mitigate; iframe sandboxing limits bleed |

---

## Assumptions

| Assumption | Impact if Wrong |
|------------|-----------------|
| TradingView `range` param accepts `"1D"`, `"5D"`, `"1M"`, `"3M"` values | Timeframe selector would not work; would need alternative approach |
| Script `onload` fires reliably in Chromium on Danny's Tailscale device | Loading -> ready transition might not fire; would need polling fallback |
| `new TradingView.widget(config)` is a synchronous constructor | If async, try-catch and status transitions might not work as specified |
| Right panel provides sufficient width for useful chart | If too narrow, chart is unusable; `autosize: true` partially mitigates |
| Danny's Tailscale network does not block `s3.tradingview.com` | Feature would be non-functional; error state (US-07) prevents app crash |

---

## Open Questions

| Question | Status | Resolution |
|----------|--------|------------|
| Q1 (from v1.0) | **Resolved** | `#a78bfa` confirmed as active timeframe accent |
| Q2 (from v1.0) | **Resolved** | try-catch around widget constructor added |
| Q3 (from v1.0) | **Resolved** | Same-ticker error retry now via `selectCount` (replaced `retryKey`) |
| Q4 (from v1.0) | **Resolved** | `hide_top_toolbar: true` confirmed |
| Q5 (from v1.0) | **Resolved** | `allow_symbol_change: false` confirmed |
| Q6 (NEW) | **Open** | **GAP-01:** Should cleanup clear `container.innerHTML` or only set `mounted = false`? Reviewer recommends cleanup ONLY sets `mounted = false`; container clearing stays in effect body after dedup (already specified in Slice 2 line 109). **Needs human decision.** |

---

## Approval Checklist

### Requirements (01-REQUIREMENTS.md v1.2)
- [ ] Reviewed by human
- [x] Acceptance criteria are testable (all ACs have concrete assertions)
- [x] Out of scope is comprehensive (10 exclusions + 2 deferred)
- [x] Edge cases include same-ticker error retry (line 117)
- [x] `selectCount` constraint present (line 146)
- [x] No stale `retryKey` references outside change log

### Architecture (02-ARCHITECTURE.md v1.2)
- [ ] Reviewed by human
- [x] Patterns are appropriate (8 patterns + 4 anti-patterns)
- [x] Schemas are correct TypeScript
- [x] `selectCount` in props, integration points, patterns, state machine, coverage matrix
- [x] State machine models all selectCount-driven transitions
- [ ] GAP-01: Cleanup specification needs correction (line 260 -- should not clear innerHTML)
- [ ] GAP-03: Dedup logic missing "loading" branch (minor)
- [ ] GAP-04: `statusRef` sync not in Data Schemas (minor)

### UI Spec (03-UI-SPEC.md v1.2)
- [ ] Reviewed by human
- [x] Flows are complete (5 flows covering all stories)
- [x] Layouts are appropriate (4 visual states with wireframes)
- [x] `selectCount` fully specified in Flow 5, Interactions, State Visibility
- [x] No stale `retryKey` references outside change log
- [ ] GAP-03: Interaction: Same ticker missing "loading" case (minor)

### Roadmap (04-ROADMAP.md v1.2)
- [ ] Reviewed by human
- [x] Sequence is correct (linear, no circular deps)
- [x] Slices are appropriately sized
- [x] `selectCount` introduced progressively across all 4 slices
- [x] try-catch in Slice 2, mounted-flag in Slice 3
- [x] Playwright tests cover selectCount scenarios (Slice 4)
- [ ] GAP-01: Slice 3 cleanup should NOT clear innerHTML (conflicts with dedup)
- [ ] GAP-02: Slice 3 test line 173 would fail under current cleanup spec (resolved by GAP-01 fix)

### Overall
- [ ] GAP-01 resolved (critical -- cleanup vs. dedup conflict)
- [ ] All minor gaps acknowledged or resolved
- [x] All risks have mitigations
- [ ] Ready for implementation (blocked by GAP-01)

---

## Reviewer Verdict

The v1.2 spec suite is well-written and internally consistent on the `selectCount` mechanism. The replacement of `retryKey` with `selectCount` is a sound architectural decision. All four documents have been updated consistently -- no stale operational `retryKey` references remain.

**One critical gap must be resolved before implementation (GAP-01):** The `useEffect` cleanup function in Slice 3 is specified to clear `container.innerHTML`, but React runs cleanup BEFORE the new effect body. When `selectCount` increments on a healthy chart (same ticker, status "ready"), cleanup destroys the widget DOM, and the dedup then returns early without rebuilding it. The fix is straightforward: cleanup should only set `mounted = false`; container clearing should remain in the effect body after the dedup check (already specified in Slice 2, line 109).

Three minor gaps (GAP-02, GAP-03, GAP-04) are documentation completeness issues and are non-blocking.

**Counts: 1 critical gap. 3 minor gaps. 3 risks (all mitigated). 5 assumptions. 1 open question (Q6). 8 cross-document consistency checks (all pass).**
