# Architecture: tradingview-chart-widget

**Version:** 1.2
**Date:** 2026-04-04
**Status:** Draft
**Feature:** Embed TradingView Advanced Chart widget in the dilution dashboard right panel

**Change log:**
- 1.2 (2026-04-04): Replaced internal `retryKey` with `selectCount` prop from `page.tsx`. `page.tsx` increments `selectCount` on every selection; component uses ref-based dedup to skip re-init when chart is healthy, retry when errored. One new state variable added to `page.tsx`.
- 1.1 (2026-04-04): Added try-catch around `TradingView.widget()` constructor (Q2); changed `hide_top_toolbar` to `true` (Q4); added rationale note for `allow_symbol_change: false` (Q5).

---

## Overview

The TradingView Advanced Chart widget is a pure frontend addition. It introduces one new component (`TradingViewChart`) and one new supporting type block (`ChartTimeframe`). No backend changes are required. The component reacts to the existing `selectedTicker` state in `page.tsx` — zero new state-management infrastructure is needed.

The TradingView Advanced Chart embed works by appending a `<script>` tag that calls `new TradingView.widget(config)` and renders the chart into a target `<div>` with a given id. Because the script is third-party and executes client-side, the component must be marked `"use client"` and must gate script injection behind a `useEffect`. Swapping tickers requires destroying the previous widget DOM node and re-creating it rather than mutating the existing widget instance — this is the documented approach for iframe-based TradingView embeds.

---

## Components

| Component | Responsibility | Location |
|-----------|----------------|----------|
| `TradingViewChart` | Renders the TradingView Advanced Chart embed for a given symbol and timeframe; manages loading, error, and idle states; owns the timeframe selector UI | `frontend/src/components/TradingViewChart.tsx` |

No new stores, services, or utility modules are required. The component is self-contained.

---

## Data Schemas

```typescript
// Timeframe options exposed in the selector (US-04)
// Maps user-facing label → TradingView widget `interval` param
type ChartTimeframe = "1D" | "5D" | "1M" | "3M";

// Internal mapping — not exported; lives inside the component module
const TIMEFRAME_TO_TV_INTERVAL: Record<ChartTimeframe, string> = {
  "1D": "D",   // TradingView daily interval  — renders intraday 1-day range
  "5D": "D",   // Same bar interval; range controlled via date_range param
  "1M": "W",   // Weekly bars over 1-month range
  "3M": "W",   // Weekly bars over 3-month range
};

// TradingView widget constructor config shape (subset used by this feature)
// Full type is not published by TradingView; this covers required fields only.
interface TradingViewWidgetConfig {
  container_id: string;       // id of the target <div>
  symbol: string;             // e.g. "AAPL" or "NASDAQ:AAPL"
  interval: string;           // e.g. "D", "W"
  theme: "dark" | "light";
  autosize: boolean;
  hide_top_toolbar?: boolean;  // false initially — evaluate during Slice 2, may hide if toolbar exposes out-of-scope features
  hide_legend?: boolean;
  save_image?: boolean;
  allow_symbol_change?: boolean; // false — dashboard provides its own ticker search via TickerSearch component
  withdateranges?: boolean;
  range?: string;             // e.g. "1D", "5D", "1M", "3M" — TradingView built-in ranges
  backgroundColor?: string;  // hex, used to match card background
  gridColor?: string;
  locale?: string;
}

// Component internal state shape
interface TradingViewChartState {
  status: "idle" | "loading" | "ready" | "error";
  selectedTimeframe: ChartTimeframe;
}

// Refs used for dedup logic inside useEffect (not React state)
// statusRef: synced to `status` on every render via `statusRef.current = status`
// prevTickerRef: tracks previous ticker value for dedup comparison
// prevTimeframeRef: tracks previous timeframe value for dedup comparison
```

**TradingView `range` parameter mapping:**

| User label | `range` value passed to widget |
|------------|-------------------------------|
| `1D` | `"1D"` |
| `5D` | `"5D"` |
| `1M` | `"1M"` |
| `3M` | `"3M"` |

Using TradingView's built-in `range` parameter (instead of custom `from`/`to` dates) is the correct approach for the free embed widget. The `interval` field controls bar granularity; the `range` field controls the visible window. Both are set at widget construction time.

**Widget config values (non-negotiable):**

| Field | Value | Rationale |
|-------|-------|-----------|
| `hide_top_toolbar` | `false` (initial) | Start with toolbar visible to evaluate what it provides. May be set to `true` during Slice 2 if it exposes unwanted features (drawing tools, indicators). Decision deferred to visual review. |
| `allow_symbol_change` | `false` | The dashboard provides its own ticker search via the `TickerSearch` component. Enabling the widget's built-in symbol search would duplicate this functionality and bypass `selectedTicker` state management. |

---

## API Contracts

```typescript
// Props contract for TradingViewChart
interface TradingViewChartProps {
  // The currently active ticker, or null when no ticker is selected.
  // Drives the chart symbol and determines whether to show the idle state.
  ticker: string | null;
  // Monotonically increasing counter incremented by page.tsx on every
  // handleGainerSelect / handleSearch call (even same-ticker).
  // Lets the component detect re-selection events that React would
  // otherwise suppress (same prop value → no re-render).
  selectCount: number;
}

// The component signature
export default function TradingViewChart(props: TradingViewChartProps): JSX.Element;
```

No new service functions, API calls, or data-fetching hooks are introduced. The component only talks to TradingView's script CDN via a dynamically injected `<script>` tag.

---

## Patterns

| Pattern | Usage | Rationale |
|---------|-------|-----------|
| `"use client"` directive | `TradingViewChart.tsx` | TradingView widget bootstraps entirely in the browser via `window.TradingView`; there is no server-render path for it |
| `useEffect` for DOM mutation | Script injection and widget construction | React must finish its render before DOM nodes are available for TradingView to target |
| `useRef` for container `id` | Stable unique id per component instance | Avoids stale closure bugs with `useState`; id is set once at mount and never changes |
| Destroy-and-recreate widget | Ticker or timeframe change | TradingView's free embed widget does not expose a `setSymbol()` or `setRange()` method; full re-initialization is the documented update mechanism |
| Deduplication via refs | `useEffect` depends on `[ticker, selectedTimeframe, selectCount]`; inside the effect, refs track previous `ticker` and `selectedTimeframe` values. If both are unchanged AND `statusRef.current` is `"ready"`, early return (no-op). If `"loading"`, early return (already initializing). If `"error"`, proceed with re-initialization (forced retry). | Allows `selectCount` to signal re-selection while preventing unnecessary re-init of a healthy or in-progress chart |
| Conditional render + guard clause | Widget script injected only when `ticker !== null` | Satisfies US-08 requirement that idle state fires no TradingView network requests |
| `onload` / `onerror` on script tag | Driving `status` state transitions | Provides reliable hooks for loading → ready and loading → error transitions; no polling required |
| Skeleton overlay | Absolute-positioned div over chart container during `status === "loading"` | Prevents layout shift (US-06): the chart container div is always present and sized; the skeleton covers it |
| Design token alignment | `backgroundColor: "#1b2230"`, `gridColor: "#2a3447"` | Matches `--color-bg-card` and `--color-border-card` from `globals.css`; no new CSS variables required |
| try-catch around widget constructor | `new TradingView.widget(config)` call inside the `onload` callback | Defense-in-depth against synchronous exceptions from the constructor (e.g., the container div removed between script load and constructor call during rapid ticker switching). On catch, if the mounted flag is still true, set `status` to `"error"`. The mounted-flag guard (Slice 3) is the primary mitigation for this race condition; the try-catch is a secondary layer. |

### Anti-Patterns (Do Not Use)

- **`next/script` with `strategy="lazyOnload"`**: The TradingView widget script must target a specific container id that exists in the DOM at the moment the script runs. `next/script` does not guarantee DOM order relative to script execution for third-party injected widgets; manual `document.createElement("script")` inside `useEffect` is safer and is the pattern used in TradingView's own embed documentation.
- **`dangerouslySetInnerHTML` for the script**: Unnecessary complexity. The script element created via `document.createElement` is simpler and supports `onload`/`onerror` event handlers.
- **Mutating widget state via a TradingView instance variable**: The free Advanced Chart widget does not expose a stable public API for live updates. Mutating it is undefined behavior; destroy-and-recreate is the correct approach.
- **`useState` for the container id**: The id must be stable from the moment `useEffect` first runs. `useRef` initialized once is the correct tool.

---

## Dependencies

No new dependencies. The TradingView widget is loaded at runtime from TradingView's CDN (`https://s3.tradingview.com/tv.js`) via a dynamically injected script tag. No npm package is required.

Current `package.json` dependencies are sufficient:

| Existing Dependency | Version | Relevance |
|---------------------|---------|-----------|
| `next` | `16.2.2` | Provides the Next.js build pipeline and `"use client"` directive support |
| `react` | `19.2.4` | `useEffect`, `useRef`, `useState` for component lifecycle |
| `tailwindcss` | `^4` | Utility classes for layout, skeleton, and timeframe selector styling |

---

## Integration Points

### `frontend/src/app/page.tsx`

Changes to `page.tsx`:

1. Import `TradingViewChart`.
2. Add `const [selectCount, setSelectCount] = useState(0)` to the state block.
3. Add `setSelectCount(c => c + 1)` to both `handleGainerSelect` and `handleSearch`.
4. Insert `<TradingViewChart ticker={selectedTicker} selectCount={selectCount} />` between `<Header .../>` and `<Headlines .../>` inside the `{(isLoading || dilutionData) && (...)}` block.

The chart must appear in this conditional block because `selectedTicker` is set at the same time `isLoading` becomes true. This ensures the chart appears in sync with the rest of the panel and never shows in the idle state.

`selectCount` is the only new state variable in `page.tsx`. It increments on every user selection action (gainer click or search submit), including same-ticker re-selections. This gives `TradingViewChart` a signal that a user action occurred, even when the ticker prop value hasn't changed — solving the problem that React suppresses re-renders when props are identical.

```
// Exact insertion point in page.tsx (for reference, not implementation)
{(isLoading || dilutionData) && (
  <>
    <Header data={...} />
    <TradingViewChart ticker={selectedTicker} selectCount={selectCount} />
    <Headlines data={...} />
    ...
  </>
)}
```

### TradingView CDN (`https://s3.tradingview.com/tv.js`)

The component dynamically injects a `<script src="https://s3.tradingview.com/tv.js">` element into `document.head`. The script populates `window.TradingView` and the widget constructor is called immediately in the `onload` callback, wrapped in a try-catch. The component does not cache the script tag — each widget initialization appends a fresh script (TradingView's own embed snippets follow this pattern).

### Design System (`globals.css`)

The component uses existing design token values by reference (hex literals matching the CSS variables). No new CSS variables or Tailwind config changes are needed.

| Token (globals.css) | Hex used in widget config |
|---------------------|--------------------------|
| `--color-bg-card` | `#1b2230` → `backgroundColor` |
| `--color-border-card` | `#2a3447` → `gridColor` |

---

## State Machine

The component's internal `status` field follows this state machine:

```
idle ──(ticker prop set)──► loading ──(script onload + widget init succeeds)──► ready
                                    ├──(script onerror)──────────────────────► error
                                    └──(script onload + widget constructor throws + mounted)──► error

ready ──(ticker or timeframe changes)──► loading ──► ready
                                                  └──► error

error ──(ticker or timeframe changes)──► loading ──► ready
                                                   └──► error

error ──(same ticker re-selected, selectCount increments)──► loading ──► ready
                                                                      └──► error

ready ──(same ticker re-selected, selectCount increments)──► ready  (no-op, dedup via refs)
```

Transitions are driven by:
- `status = "loading"`: start of `useEffect` when `ticker !== null`
- `status = "ready"`: `onload` callback after widget construction completes without throwing
- `status = "error"`: `onerror` callback on the script element, OR catch block of the try-catch around `new TradingView.widget(config)` (only if mounted flag is still true at the time of the exception)

The `"idle"` state is never entered once a ticker has been set; the idle UI is rendered by a guard clause (`if (!ticker) return <idle UI />`), not by the state machine.

---

## Layout Contract

The `TradingViewChart` component renders:

```
<div>                                         // outer wrapper — full width, relative position
  <div id={containerId} style={{height}}>     // TradingView mount target
    {/* widget renders here */}
  </div>
  {status === "loading" && <skeleton />}       // absolute overlay, same dimensions
  {status === "error" && <error message />}    // replaces chart, same height
</div>
```

Height: `min-height: 340px` as a fixed value on the container div. This satisfies the AC "minimum height of at least 300px" requirement and provides a useful chart area on Danny's desktop display. The `autosize: true` widget config option fills the container width automatically.

The timeframe selector is positioned above the chart container as a row of 4 buttons, inside the outer wrapper. It only renders when `ticker !== null`.

---

## Requirement Coverage Matrix

| Requirement | Coverage |
|-------------|----------|
| US-01: Chart placed between Header and Headlines | Insertion in `page.tsx` conditional block |
| US-02: Auto-update on gainer click | `ticker` prop from `selectedTicker`; `useEffect` dependency fires on prop change |
| US-03: Auto-update on search | Same mechanism as US-02 |
| US-04: Timeframe selector (1D/5D/1M/3M) | `selectedTimeframe` state + `TIMEFRAME_TO_TV_INTERVAL` mapping; timeframe in `useEffect` dependency array |
| US-05: Dark theme | `theme: "dark"`, `backgroundColor: "#1b2230"`, `gridColor: "#2a3447"` passed to widget config |
| US-06: Loading state | Skeleton overlay while `status === "loading"` |
| US-07: Error state | Error message rendered when `status === "error"` (triggered by script `onerror` or widget constructor exception) |
| US-08: Idle state | Guard clause returns placeholder when `ticker === null`; no script injected |
| Edge: Same ticker re-selected (ready) | Ref-based dedup in `useEffect` — `selectCount` changes trigger the effect, but if ticker/timeframe unchanged and status is "ready", early return (no-op) |
| Edge: Same ticker re-selected (error) | `selectCount` changes trigger the effect; ref-based dedup detects status is "error" and proceeds with re-initialization (forced retry) |
| Edge: Rapid ticker switching | `useEffect` cleanup sets `mounted = false` to void in-flight callbacks; container clearing happens in effect body after dedup passes; try-catch on constructor provides additional defense |
| Edge: Offline / CDN blocked | `onerror` on script tag drives `status = "error"` |

---

## File Summary

| File | Action | Notes |
|------|--------|-------|
| `frontend/src/components/TradingViewChart.tsx` | Create | New component; entire feature lives here |
| `frontend/src/app/page.tsx` | Modify | Import, one JSX insertion, `selectCount` state + increment in both handlers |
| `frontend/src/types/dilution.ts` | No change | `ChartTimeframe` type is component-local; no need to export |
| All backend files | No change | Feature is purely frontend |
