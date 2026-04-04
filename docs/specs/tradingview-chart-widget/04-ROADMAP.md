# Implementation Roadmap: tradingview-chart-widget

**Version:** 1.2
**Date:** 2026-04-04
**Status:** Ready for Implementation
**Feature:** Embed TradingView Advanced Chart widget in the dilution dashboard right panel

**Change log (v1.2):** Replaced internal `retryKey` with `selectCount` prop from `page.tsx`. `page.tsx` now adds one state variable (`selectCount`) and increments it in both handlers. Component uses ref-based dedup to skip re-init when healthy, retry when errored. Slice 4 page.tsx changes updated accordingly.

**Change log (v1.1):** `hide_top_toolbar` corrected to `true`. try-catch added around widget constructor. Same-ticker error retry mechanism added.

---

## Summary

Four ordered slices. One new file created; one existing file modified. No backend changes, no new dependencies, no new Tailwind config. Each slice is independently verifiable before the next begins.

---

## Dependency Map

| Unit | Depends On |
|------|------------|
| `ChartTimeframe` type | — |
| `TIMEFRAME_TO_TV_INTERVAL` mapping | `ChartTimeframe` type |
| `selectCount` prop | `page.tsx` state — passed as prop |
| Idle placeholder UI | `ChartTimeframe` type |
| Loading skeleton UI | `ChartTimeframe` type |
| Error message UI | `ChartTimeframe` type |
| Timeframe selector UI | `ChartTimeframe`, `TIMEFRAME_TO_TV_INTERVAL` |
| TradingView script injection + widget constructor | All UI states complete |
| `useEffect` destroy-and-recreate lifecycle | Script injection logic |
| Rapid-switch mounted-flag guard | `useEffect` lifecycle |
| `page.tsx` integration | `TradingViewChart` component fully implemented |

---

## Slice Overview

| Slice | Goal | Depends On | Files |
|-------|------|------------|-------|
| 1 | Scaffold `TradingViewChart.tsx` with all static UI states (idle, loading skeleton, error) and the timeframe selector — no live widget | — | `TradingViewChart.tsx` (create) |
| 2 | Wire the TradingView CDN script injection and widget constructor into the component | Slice 1 | `TradingViewChart.tsx` (modify) |
| 3 | Harden the lifecycle: destroy-and-recreate on prop change, mounted-flag guard against rapid switching | Slice 2 | `TradingViewChart.tsx` (modify) |
| 4 | Integrate into `page.tsx`: import, insert between Header and Headlines, production build and Playwright verification | Slice 3 | `page.tsx` (modify) |

---

## Slice 1: Static UI Scaffold

**Goal:** Create `TradingViewChart.tsx` with all four visual states rendered correctly from props/internal state, with no live TradingView network calls.

**Depends On:** —

**Files:**
- `frontend/src/components/TradingViewChart.tsx` — create

**Implementation Notes:**
- Add `"use client"` directive at the top of the file.
- Define `ChartTimeframe` type (`"1D" | "5D" | "1M" | "3M"`) and `TIMEFRAME_TO_TV_INTERVAL` as a module-local constant. Neither is exported.
- Define component props interface: `{ ticker: string | null; selectCount: number }`.
- Add `useState<"idle" | "loading" | "ready" | "error">` defaulting to `"idle"`, and `useState<ChartTimeframe>` defaulting to `"1D"`.
- Add `useRef` entries for `prevTickerRef` (initialized to `null`), `prevTimeframeRef` (initialized to `"1D"`), and `statusRef` (synced to `status` on every render). These refs power the dedup logic in Slice 2's `useEffect`.
- Add `useRef` for a stable `containerId` string (set once on mount, never changes).
- Implement the guard clause: if `ticker === null`, return the idle placeholder (centered muted text "Select a ticker to view chart", `min-height: 340px`, card styling). No script tag, no TradingView reference anywhere in this branch.
- Implement the timeframe selector row (only renders when `ticker !== null`): 4 buttons (1D, 5D, 1M, 3M). Active button: `bg-[#2a3447] text-[#eef1f8] font-bold border-b-2 border-[#a78bfa]`. Inactive button: `text-[#9aa7c7] hover:bg-[#2a3447]`. Button sizing: `text-xs font-bold px-3 py-1.5 rounded-[5px]`.
- Implement the chart container div: `id={containerId}` attribute, `style={{ minHeight: "340px", width: "100%" }}`, `position: relative`.
- Implement skeleton overlay: `position: absolute; inset: 0; background: #1b2230; animate-pulse; rounded-[5px]` — rendered only when `status === "loading"`.
- Implement error state: centered text "Chart unavailable" (`text-[#9aa7c7] text-sm`) and subtext "Could not load TradingView chart widget" (`text-[#9aa7c7] text-xs`) — rendered only when `status === "error"`.
- For Slice 1 only, force `status` to `"loading"` via a temporary `useEffect(() => { if (ticker) setStatus("loading"); }, [ticker])` to make the skeleton visually testable. This temporary effect is replaced entirely in Slice 2.
- Outer card wrapper: `bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-4`.
- Spacing between timeframe selector and chart container: `mb-2` on the selector row or `space-y-2` on the outer wrapper.

**Tests:**
- [ ] With `ticker={null}`: idle placeholder text is present in DOM; no `<script>` tag referencing `tradingview.com` appears anywhere in document.
- [ ] With `ticker="AAPL"` and `status` forced to `"loading"`: skeleton overlay is visible; timeframe selector renders all 4 buttons; "1D" button has active styling.
- [ ] With `ticker="AAPL"` and `status` manually set to `"error"`: "Chart unavailable" text is present; timeframe selector still renders.
- [ ] Clicking the "5D" button updates `selectedTimeframe` to `"5D"` and the "5D" button receives active styling.
- [ ] Container div always has `min-height: 340px` regardless of `status`.
- [ ] No horizontal overflow when the component is rendered inside a `max-w-sm` wrapper.

**Done When:**
- [ ] `TradingViewChart.tsx` file exists at `frontend/src/components/TradingViewChart.tsx`.
- [ ] The file compiles without TypeScript errors (`npx tsc --noEmit` passes in `frontend/`).
- [ ] All 4 visual states (idle, loading, ready, error) are reachable by controlling `ticker` prop and `status` state.
- [ ] Timeframe selector renders 4 buttons with correct active/inactive styling using `#a78bfa` as the active accent color.
- [ ] Props interface accepts `selectCount: number`. Refs for `prevTickerRef`, `prevTimeframeRef`, and `statusRef` are declared.
- [ ] No TradingView CDN references appear anywhere in the file (Slice 1 is purely static).
- [ ] Temporary forced-loading `useEffect` is in place and clearly marked `// TODO: replace in Slice 2`.

---

## Slice 2: TradingView Script Injection and Widget Constructor

**Goal:** Replace the temporary loading effect with real TradingView CDN script injection and widget initialization; drive `status` through `loading → ready` and `loading → error` via script `onload`/`onerror`; wrap the widget constructor in a try-catch for defense-in-depth.

**Depends On:** Slice 1

**Files:**
- `frontend/src/components/TradingViewChart.tsx` — modify

**Implementation Notes:**
- Remove the temporary `useEffect` from Slice 1 entirely.
- Add a `useEffect` with dependency array `[ticker, selectedTimeframe, selectCount]`. Including `selectCount` ensures the effect fires on every user selection, even same-ticker re-clicks.
- Guard clause at the top of the effect: `if (!ticker) return;`.
- Dedup check (immediately after guard): compare `ticker` and `selectedTimeframe` against `prevTickerRef.current` and `prevTimeframeRef.current`. If both are unchanged AND `statusRef.current === "ready"`, return early (no-op — chart is healthy, no reason to re-init). If `statusRef.current === "error"`, proceed (forced retry). If `statusRef.current === "loading"`, return early (already initializing).
- After the dedup check passes: update `prevTickerRef.current` and `prevTimeframeRef.current` to the current values.
- Set `status` to `"loading"`.
- Clear the chart container's inner HTML before injecting a new widget (prevents stale DOM from previous initialization).
- Create a `<script>` element via `document.createElement("script")`; set `src` to `https://s3.tradingview.com/tv.js`; append to `document.head`.
- In the `onload` callback: wrap the widget constructor call in a try-catch block.
  - In the try block: call `new window.TradingView.widget(config)` targeting `containerId`. Set `status` to `"ready"` immediately after the constructor call (widget renders asynchronously into the container, but the constructor call completing is the signal that initialization was accepted).
  - In the catch block: if the component is still mounted (`mounted` flag is `true` — see Slice 3), set `status` to `"error"`. This guards against synchronous exceptions from the constructor (e.g., the container div removed between script load and constructor call during rapid ticker switching).
  - Note: the `mounted` flag is introduced fully in Slice 3. For Slice 2 only, the catch block may set `status` to `"error"` unconditionally; the mounted-flag guard is layered on in Slice 3.
- Widget config shape (use `TIMEFRAME_TO_TV_INTERVAL[selectedTimeframe]` for `interval` and the string value of `selectedTimeframe` for `range`):
  ```
  container_id: containerId,
  symbol: ticker,
  interval: TIMEFRAME_TO_TV_INTERVAL[selectedTimeframe],
  range: selectedTimeframe,
  theme: "dark",
  autosize: true,
  backgroundColor: "#1b2230",
  gridColor: "#2a3447",
  hide_top_toolbar: false,  // evaluate visually — may flip to true
  allow_symbol_change: false,
  save_image: false,
  locale: "en",
  ```
- In the `onerror` callback: set `status` to `"error"`.
- The `window.TradingView` reference requires a TypeScript declaration. Add `declare global { interface Window { TradingView: any; } }` at the module level to satisfy the compiler without importing a non-existent package.

**Tests:**
- [ ] With `ticker="AAPL"` and CDN reachable: `status` transitions from `"loading"` to `"ready"`; skeleton overlay is no longer visible; TradingView iframe is present inside the container.
- [ ] With CDN blocked (test by overriding `window.TradingView` to throw or by simulating `onerror`): `status` transitions to `"error"`; error message is displayed.
- [ ] With `ticker="AAPL"` then `selectedTimeframe` changed to `"5D"`: effect fires again; widget is reconstructed with `range: "5D"`.
- [ ] Simulating a constructor exception (override `window.TradingView.widget` to throw): `status` transitions to `"error"` via the catch block; error message is displayed.
- [ ] `npx tsc --noEmit` passes with no errors after adding the `Window` declaration.
- [ ] No duplicate `<script>` tags from the same CDN URL accumulate when the component re-renders without a dependency change.

**Done When:**
- [ ] Temporary `useEffect` from Slice 1 is fully removed.
- [ ] Real `useEffect([ticker, selectedTimeframe, selectCount])` is in place with ref-based dedup and drives `status` via `onload`/`onerror`.
- [ ] `new TradingView.widget(config)` call is wrapped in a try-catch; catch sets `status` to `"error"`.
- [ ] Widget config specifies `hide_top_toolbar: false` (evaluate visually — may flip to `true` per Requirements v1.2).
- [ ] `window.TradingView` TypeScript declaration is present; `npx tsc --noEmit` passes.
- [ ] Status state correctly transitions: `loading → ready` on CDN success; `loading → error` on CDN failure or constructor exception.
- [ ] The component does NOT inject any script tag when `ticker === null`.

---

## Slice 3: Lifecycle Hardening (Destroy-and-Recreate + Mounted Flag)

**Goal:** Ensure that rapid ticker switching produces only one final widget, that changing to a new ticker tears down the previous DOM correctly, and that stale `onload`/`onerror` callbacks from superseded effects do not update state.

**Depends On:** Slice 2

**Files:**
- `frontend/src/components/TradingViewChart.tsx` — modify

**Implementation Notes:**
- Add a `mounted` boolean flag (`let mounted = true`) at the top of the `useEffect` body. All state-setting calls inside `onload`, `onerror`, and the try-catch catch block must be guarded with `if (!mounted) return;` before executing. This includes:
  - The `setStatus("ready")` call in the try block after the widget constructor.
  - The `setStatus("error")` call in the catch block.
  - The `setStatus("error")` call in the `onerror` callback.
- Return a cleanup function from the `useEffect` that sets `mounted = false` ONLY. The cleanup must NOT clear `container.innerHTML` — because React runs cleanup before the new effect body, and if the dedup check then returns early (same ticker, chart healthy), the container would be left empty with no rebuild. Instead, the container clearing (`container.innerHTML = ""`) stays in the effect body (already specified in Slice 2), executed AFTER the dedup check passes and BEFORE injecting the new script.
- The `selectCount` dependency in the `useEffect` means cleanup also runs on same-ticker re-selection. The mounted-flag guard correctly voids any in-flight callbacks from the previous effect run. The ref-based dedup at the top of the effect body then decides whether to proceed (error → retry) or return early (ready → no-op, chart DOM untouched).
- Do not attempt to remove the dynamically appended `<script>` tag from `document.head` on cleanup. TradingView's script is idempotent once loaded; removing and re-adding it causes unnecessary re-fetches. The `mounted` flag is sufficient to discard callbacks from superseded effect runs.

**Tests:**
- [ ] Simulating rapid ticker changes (A → B → C in quick succession with mocked async `onload`): only ticker C's widget constructor is called; A and B's `onload` callbacks fire but do not call `setStatus` (guarded by mounted flag).
- [ ] After a ticker change, the previous chart container's inner HTML is empty before the new widget is initialized.
- [ ] Selecting the same ticker that is already displayed (in `"ready"` state) does not trigger any DOM teardown or re-initialization (ref-based dedup returns early even though `selectCount` changed).
- [ ] Selecting a different ticker and returning to the original causes a full re-initialization (dependency has changed).
- [ ] No React state-update-on-unmounted-component warnings appear in the browser console during rapid switching.
- [ ] If the widget constructor throws after a ticker change races with cleanup, the catch block's `setStatus("error")` is suppressed by the `if (!mounted) return;` guard.

**Done When:**
- [ ] `mounted` flag is present in `useEffect` body and guards all state-setting callbacks, including the try-catch catch block introduced in Slice 2.
- [ ] Cleanup function sets `mounted = false` only. Container clearing happens in the effect body after dedup passes.
- [ ] No stale state updates occur when a ticker change, timeframe change, or `selectCount` increment supersedes an in-flight initialization.
- [ ] `npx tsc --noEmit` still passes.
- [ ] No regressions to Slice 2 behavior when tested in the normal (non-rapid) path.

---

## Slice 4: Integration into `page.tsx` + Production Verification

**Goal:** Import `TradingViewChart` into `page.tsx`, insert it between `Header` and `Headlines` inside the existing conditional block, build and serve the production bundle, and verify all acceptance criteria via Playwright from the Tailscale IP.

**Depends On:** Slice 3

**Files:**
- `frontend/src/app/page.tsx` — modify (import, JSX insertion, `selectCount` state + increment in both handlers)
- `frontend/src/components/TradingViewChart.tsx` — no changes

**Implementation Notes:**
- Add `import TradingViewChart from "@/components/TradingViewChart";` to the import block in `page.tsx`.
- Add `const [selectCount, setSelectCount] = useState(0)` to the state block in `page.tsx`.
- Add `setSelectCount(c => c + 1)` as the first line in both `handleGainerSelect` and `handleSearch` (before any other state updates).
- Insert `<TradingViewChart ticker={selectedTicker} selectCount={selectCount} />` as a direct child of the `<>` fragment inside the `{(isLoading || dilutionData) && (...)}` block, between `<Header data={...} />` and `<Headlines data={...} />`.
- Build command: `cd frontend && npx next build && npx next start -p 3001 -H 0.0.0.0`.
- Playwright tests run against the Tailscale IP (not localhost).

**Playwright Test Expectations:**
- [ ] **US-01 — Placement:** After selecting a ticker, the chart container appears after the Header element and before the first Headlines element in the DOM. `Header >> .. >> TradingViewChart >> .. >> Headlines` order holds in the DOM.
- [ ] **US-01 — Height:** The chart container div has `min-height` of at least 300px (spec: 340px). Playwright: `await expect(locator).toHaveCSS("min-height", "340px")` or equivalent bounding box check.
- [ ] **US-02 — Gainer click updates chart:** Click gainer row A (ticker "X"), wait for chart container to contain a TradingView iframe. Click gainer row B (ticker "Y"), verify TradingView iframe re-initializes with the new symbol (check `src` attribute or container contents change within 2 seconds).
- [ ] **US-03 — Search updates chart:** Submit ticker "TSLA" via TickerSearch. Chart container iframe appears within 2 seconds.
- [ ] **US-04 — Timeframe selector visible:** After selecting a ticker, 4 buttons labeled "1D", "5D", "1M", "3M" are visible. Clicking "5D" gives it the active style class (including `border-[#a78bfa]`) and removes active style from "1D".
- [ ] **US-04 — Timeframe persists across ticker change:** Select ticker, set timeframe to "3M". Click a different gainer. After the new chart loads, "3M" button still has the active style.
- [ ] **US-05 — Dark theme:** The outer card wrapper has `background-color: rgb(27, 34, 48)` (which is `#1b2230`). Playwright: `toHaveCSS("background-color", "rgb(27, 34, 48)")`.
- [ ] **US-06 — Loading skeleton visible:** Immediately after clicking a gainer, before the widget finishes loading, the skeleton overlay is present in the DOM. (Requires either a slow-network simulation or a fast assertion after click.)
- [ ] **US-07 — Error state:** With TradingView CDN blocked (network intercept in Playwright), the chart area displays "Chart unavailable" text. Other right-panel sections (Header, Headlines) continue to render.
- [ ] **US-08 — Idle state (no ticker selected):** On initial page load, no `<script src="https://s3.tradingview.com">` request is made. The chart component does not render inside the conditional block, which is not visible in the idle state.
- [ ] **Edge — Same ticker re-selection (active state):** Click gainer row for "AAPL". Then click the same row again. Verify no chart flash or skeleton re-appearance occurs (chart container content is stable).
- [ ] **Edge — Same ticker re-selection in error state:** With TradingView CDN blocked (network intercept), click a gainer row and wait for "Chart unavailable" to appear. Click the same gainer row again. Verify the skeleton overlay appears (retry is triggered), and "Chart unavailable" re-appears after the retry attempt fails. Verify no stale widget DOM remains from the previous attempt.
- [ ] **No horizontal overflow:** Right panel does not have a horizontal scrollbar at any point during chart rendering. Playwright: `await expect(page.locator(".right-panel")).not.toHaveCSS("overflow-x", "scroll")`.

**Done When:**
- [ ] `page.tsx` diff contains: one new import, one `selectCount` state declaration, one increment call in each handler (`handleGainerSelect` and `handleSearch`), and one JSX insertion.
- [ ] No other components in `page.tsx` are modified.
- [ ] `npx next build` completes without errors or TypeScript diagnostics.
- [ ] `npx next start -p 3001 -H 0.0.0.0` serves the app successfully.
- [ ] All Playwright test expectations above pass from the Tailscale IP.
- [ ] Existing right-panel components (Header, Headlines, RiskBadges, etc.) render and behave identically to the pre-feature baseline.

---

## Sequence Rules

1. Complete each slice fully before starting the next. No partial slice work.
2. Each slice must satisfy all "Done When" criteria before proceeding.
3. Slices 1–3 can be tested locally with `npx next dev` or a production build; Slice 4 requires a production build.
4. If any slice is blocked (TypeScript error that cannot be resolved, unexpected TradingView API behavior, layout regression), HALT and report. Do not skip ahead or work around with hacks.
5. No new slices or scope additions without explicit human approval.

---

## Deferred (Not This Roadmap)

- Custom intraday charting backed by Danny's own dataset.
- TradingView Lightweight Charts library (open-source, custom implementation).
- Any paid TradingView API or data subscription.
- Drawing tools, indicator configuration, or chart UI beyond the 4 timeframe buttons.
- Timeframe persistence across page reloads (no localStorage or session storage).
- Mobile layout optimization.
- Mini-charts or sparklines in the gainer sidebar rows.
- Additional timeframe options beyond 1D, 5D, 1M, 3M.
- A manual "retry chart" button on the error state.
- Removing dynamically appended script tags on cleanup (not needed; TradingView script is idempotent and mounting behavior does not require this).

---

## File Summary

| File | Slice | Action |
|------|-------|--------|
| `frontend/src/components/TradingViewChart.tsx` | 1 | Create |
| `frontend/src/components/TradingViewChart.tsx` | 2 | Modify — add real `useEffect([ticker, selectedTimeframe, selectCount])` + ref-based dedup + script injection + try-catch |
| `frontend/src/components/TradingViewChart.tsx` | 3 | Modify — add mounted flag + cleanup (guards try-catch catch block too) |
| `frontend/src/app/page.tsx` | 4 | Modify — import, JSX insertion, `selectCount` state + increment in both handlers |

All backend files: no changes across all slices.
