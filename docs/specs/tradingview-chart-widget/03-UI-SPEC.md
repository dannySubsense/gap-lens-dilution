# UI Specification: tradingview-chart-widget

**Version:** 1.2
**Date:** 2026-04-04
**Status:** Draft
**Feature:** Embed TradingView Advanced Chart widget in the dilution dashboard right panel

---

## Change Log

| Version | Change |
|---------|--------|
| 1.2 | Replaced `retryKey` mechanism with `selectCount` prop from `page.tsx`. Same-ticker retry now driven by `selectCount` increment + ref-based dedup inside the component. |
| 1.1 | Q1 resolved: `#a78bfa` confirmed as the active timeframe button accent (definitive, matching Header ticker text). Q3 resolved: same-ticker-in-error-state now forces a retry. |
| 1.0 | Initial draft |

---

## Overview

This spec defines the screen states, layout, interactions, and component structure for placing a TradingView Advanced Chart widget between the `Header` and `Headlines` components in the right panel of the Gap Lens Dilution dashboard.

The widget is a single new component (`TradingViewChart`) dropped into an existing layout. The dashboard as a whole does not change structurally — only the right panel gains a new section.

---

## Screens

The dashboard is a single-page application. No new screens are introduced. The widget adds a new section to the existing **Dashboard Screen**, which itself has several display states driven by `selectedTicker`.

| Screen / State | Purpose | Entry Point |
|----------------|---------|-------------|
| Dashboard — Idle | No ticker selected; right panel shows prompt only | Initial page load |
| Dashboard — Loading | Ticker selected; data fetch in progress | Gainer click or search submit |
| Dashboard — Active | Dilution data loaded; all right-panel sections visible including chart | Data fetch completes |
| Dashboard — App Error | API fetch failed; error message shown in right panel | Failed data fetch |

The `TradingViewChart` component itself has four internal visual states that appear within the Dashboard — Active and Dashboard — Loading screens:

| Chart State | When It Appears |
|-------------|----------------|
| Idle placeholder | `ticker` prop is `null` (not reachable from inside the conditional block per architecture; documented for completeness) |
| Loading skeleton | `ticker` prop is set, widget script not yet initialized |
| Active chart | Widget fully rendered and displaying price data |
| Error message | TradingView script failed to load or threw an error |

---

## User Flows

### Flow 1: Gainer click updates chart (US-02)

1. User starts at: Dashboard — Active (a ticker is already displayed)
2. User sees: Right panel showing Header, chart widget, Headlines, and dilution components for the current ticker
3. User action: Clicks a gainer row in either the TradingView or Massive sidebar column
4. System response: `handleGainerSelect` fires in `page.tsx`; `selectedTicker` is updated; `TradingViewChart` receives the new ticker prop; the chart's `useEffect` dependency fires; the previous widget is destroyed; `status` transitions to `"loading"`; a skeleton overlay covers the chart area; the dilution data fetch begins for the new ticker
5. User sees: Skeleton overlay on the chart area (same dimensions as the chart); Header and other components show their skeleton state while the API fetch is in progress
6. End state: Dashboard — Active with the new ticker's chart rendered and dilution data populated

Success path: New ticker's chart loads within 2 seconds; skeleton is replaced by the live chart.
Error path: If the TradingView script fails (CDN blocked, network offline), the skeleton is replaced by the chart error message. The rest of the right panel continues to render.

---

### Flow 2: Search submit updates chart (US-03)

1. User starts at: Dashboard — Idle or Dashboard — Active
2. User sees: TickerSearch bar at the top of the right panel
3. User action: Types a ticker symbol into the search input and presses Enter or clicks "Search"
4. System response: `handleSearch` fires; `selectedTicker` is set; the `{(isLoading || dilutionData) && (...)}` conditional block renders (if not already visible); `TradingViewChart` appears with the new ticker; `status` transitions to `"loading"`; skeleton overlay is shown; dilution data fetch begins
5. User sees: Right panel transitions from idle prompt (or previous ticker state) to the loading skeleton layout — Header skeleton, chart skeleton, Headlines skeleton
6. End state: Dashboard — Active with chart and dilution data for the searched ticker

Success path: Chart renders; dilution data populates.
Error path: TradingView CDN error shows chart error message. API error shows app error panel (existing behavior); chart error and app error are independent.

---

### Flow 3: Timeframe selection (US-04)

1. User starts at: Dashboard — Active (chart is displaying a ticker)
2. User sees: Timeframe selector row above the chart area showing 4 buttons: 1D, 5D, 1M, 3M; the active timeframe is visually distinguished
3. User action: Clicks a timeframe button (e.g., "5D")
4. System response: `selectedTimeframe` state inside `TradingViewChart` updates to `"5D"`; the `useEffect` dependency fires because `selectedTimeframe` changed; the previous widget is destroyed; `status` transitions to `"loading"`; skeleton overlay appears; the widget is re-initialized with the new `range` and `interval` values
5. User sees: Skeleton overlay briefly; then chart re-renders showing the 5-day range
6. End state: Dashboard — Active; chart shows the newly selected timeframe; selected button is visually active

Success path: Chart re-renders with new timeframe in under 2 seconds.
Error path: If re-initialization fails, `status` transitions to `"error"` and the error message replaces the skeleton.

Timeframe persistence behavior: When the user selects a new ticker while a non-default timeframe is active, the timeframe selection **persists** to the new ticker. The `selectedTimeframe` state is owned by `TradingViewChart` and is not reset on ticker prop change. This provides continuity — if the user is reviewing 5D charts, switching tickers keeps the 5D context.

---

### Flow 4: Page load — idle state (US-08)

1. User starts at: Dashboard — Idle (no ticker selected, initial page load)
2. User sees: TickerSearch bar; idle prompt text ("Search a ticker or click a gainer to begin."); the `{(isLoading || dilutionData) && (...)}` conditional block is not rendered; therefore `TradingViewChart` does not render
3. User action: None yet
4. End state: Dashboard — Idle; no TradingView script requests are made

No chart loading state, no error state, no TradingView network requests in this flow.

---

### Flow 5: Error recovery (US-07)

1. User starts at: Dashboard — Active; chart is in `"error"` state
2. User sees: Error message in the chart area ("Chart unavailable"); Header, Headlines, and dilution components are rendering normally
3. User action: Clicks any gainer row or submits any ticker via search

**Case A — Different ticker selected:**

4. System response: Ticker prop changes; `useEffect` fires (dependency: `ticker`); `status` resets to `"loading"`; a new widget initialization is attempted
5. End state: If CDN is reachable, chart transitions to `"ready"`. If CDN is still unreachable, error message is shown again.

**Case B — Same ticker re-selected while in error state:**

4. System response: `page.tsx` calls `handleGainerSelect` (or `handleSearch`) with the same ticker string. Even though `selectedTicker` doesn't change, `page.tsx` increments `selectCount` (which increments on every selection action). `TradingViewChart` receives the new `selectCount` prop. The `useEffect` dependency array includes `selectCount`, so the effect fires. Inside the effect, the ref-based dedup check sees that `ticker` and `selectedTimeframe` are unchanged, but `status` (via ref) is `"error"` — so it proceeds with re-initialization rather than returning early. `status` resets to `"loading"`.
5. User sees: Skeleton overlay replaces the error message immediately on click.
6. End state: If CDN is now reachable, chart transitions to `"ready"`. If CDN is still unreachable, error message is shown again.

Implementation note: The retry is triggered by the user's explicit click causing `selectCount` to increment in `page.tsx`. It does NOT auto-retry on timeout or in the background.

There is no manual "retry chart" button (deferred). The recovery mechanisms are: (a) select a different ticker, or (b) re-select the same ticker (which forces a retry via `selectCount`), or (c) refresh the page.

---

## Screen: Dashboard — Active (Right Panel)

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│ TickerSearch                                         │
│ [input: "Enter ticker symbol..."] [Search button]    │
├─────────────────────────────────────────────────────┤
│ Header                                               │
│ TICKER  [ChartAnalysisBadge]           RISK: High    │
│ $2.47                                                │
│ Float/OS: 45M/67M | MC: 165M | Biotech | USA        │
├─────────────────────────────────────────────────────┤
│ TradingViewChart                                     │
│ ┌───────────────────────────────────────────────┐   │
│ │ [1D] [5D] [1M] [3M]   ← timeframe selector   │   │
│ ├───────────────────────────────────────────────┤   │
│ │                                               │   │
│ │   TradingView Advanced Chart iframe           │   │
│ │   (min-height: 340px, autosize width)         │   │
│ │                                               │   │
│ └───────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│ Headlines                                            │
│ [badge] [timestamp] Headline text                    │
│ [badge] [timestamp] Headline text                    │
│ ...                                                  │
├─────────────────────────────────────────────────────┤
│ RiskBadges                                           │
├─────────────────────────────────────────────────────┤
│ OfferingAbility                                      │
├─────────────────────────────────────────────────────┤
│ InPlayDilution                                       │
├─────────────────────────────────────────────────────┤
│ Offerings (conditional)                              │
├─────────────────────────────────────────────────────┤
│ GapStats (conditional)                               │
├─────────────────────────────────────────────────────┤
│ JMT415Notes                                          │
├─────────────────────────────────────────────────────┤
│ MgmtCommentary (conditional)                         │
├─────────────────────────────────────────────────────┤
│ Ownership (conditional)                              │
└─────────────────────────────────────────────────────┘
```

The right panel is `flex-1 overflow-y-auto p-4 space-y-4` (existing). All sections stack vertically with `space-y-4` gap. `TradingViewChart` is a direct child of this flex column, between `Header` and `Headlines`.

### Sections

| Section | Content | Data Source |
|---------|---------|-------------|
| TickerSearch | Text input + submit button | User input; calls `handleSearch` in `page.tsx` |
| Header | Ticker symbol, risk badge, chart analysis badge, stock price, float/OS/MC/sector/country | `dilutionData` via `buildHeaderData()`; null shows skeleton |
| TradingViewChart | Timeframe selector + TradingView iframe; 4 visual states | `selectedTicker` + `selectCount` props from `page.tsx`; internal `selectedTimeframe` state |
| Headlines | Filing type badges, timestamps, headline text | `dilutionData.news` via `mapNewsToHeadlines()`; null shows skeleton |
| RiskBadges | Risk level indicators (overall, offering, dilution, etc.) | `dilutionData` via `buildRiskData()` |
| OfferingAbility | Text description of offering ability | `dilutionData.offeringAbilityDesc` |
| InPlayDilution | Warrants and convertibles tables | `dilutionData` via `buildInPlayData()` |
| Offerings | Past offering entries table | `dilutionData.offerings` (conditional: only when non-empty) |
| GapStats | Historical gap statistics | `dilutionData.gapStats` (conditional: only when non-empty) |
| JMT415Notes | JMT analyst notes | `dilutionData.news` via `extractJMT415()` |
| MgmtCommentary | Management commentary text | `dilutionData.mgmtCommentary` (conditional) |
| Ownership | Ownership table | `dilutionData.ownership` (conditional) |

---

## Screen: TradingViewChart Component — All Visual States

### State 1: Idle (ticker is null)

This state is not reachable from the existing `page.tsx` render path because `TradingViewChart` is rendered only inside the `{(isLoading || dilutionData) && (...)}` block, which requires `selectedTicker` to have been set. This state is defined defensively for direct component usage.

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│        Select a ticker to view chart                │
│        [muted text, vertically centered]            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

- Outer wrapper: `bg-bg-card border border-border-card rounded-[var(--radius)]` — matches all other card sections
- Height: same `min-height: 340px` container so layout remains stable
- Text: `text-text-secondary text-sm text-center` (`#9aa7c7`)
- No timeframe selector is rendered
- No TradingView script is loaded or injected

---

### State 2: Loading (ticker set, widget initializing)

```
┌─────────────────────────────────────────────────────┐
│ [1D] [5D] [1M] [3M]                                 │
├─────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────┐ │
│ │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ │
│ │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ │
│ │    skeleton overlay (animate-pulse)             │ │
│ │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

- Outer wrapper: `bg-bg-card border border-border-card rounded-[var(--radius)] p-4`
- Timeframe selector row: rendered and interactive (user may switch timeframe while loading)
- Chart container div: always present, `min-height: 340px`, `width: 100%`, `position: relative`
- Skeleton overlay: `position: absolute; inset: 0; background: #1b2230 (bg-card); animate-pulse; rounded-[var(--radius-sm)]`
- The TradingView mount target `<div id={containerId}>` exists in the DOM but is hidden behind the skeleton overlay
- No text content in the skeleton; it is a solid dark rectangle that pulses

---

### State 3: Active / Ready (widget fully rendered)

```
┌─────────────────────────────────────────────────────┐
│ [1D]* [5D] [1M] [3M]     ← active button highlighted│
├─────────────────────────────────────────────────────┤
│                                                     │
│   [TradingView Advanced Chart iframe — dark theme]  │
│   (min-height: 340px, fills container width)        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

- Skeleton overlay is not rendered (`status === "ready"`)
- The TradingView widget fills the container div
- Widget config: `theme: "dark"`, `backgroundColor: "#1b2230"`, `gridColor: "#2a3447"`, `autosize: true`
- Active timeframe button is visually distinguished (see Timeframe Selector spec below)

---

### State 4: Error (TradingView script failed to load)

```
┌─────────────────────────────────────────────────────┐
│ [1D] [5D] [1M] [3M]                                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│        Chart unavailable                            │
│        [muted subtext: Could not load TradingView   │
│         chart widget]                               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

- Outer wrapper: same card styling as other states
- Chart container: `min-height: 340px` maintained to prevent layout shift
- Error heading: `text-text-secondary text-sm text-center` (`#9aa7c7`)
- Error subtext: `text-text-muted text-xs text-center` (`#9aa7c7`)
- Timeframe selector still rendered (it is always present when `ticker !== null`)
- Recovery: clicking any gainer row or submitting any ticker via search triggers a retry. Re-selecting the same ticker while in this error state forces a retry via `selectCount` increment (see Flow 5, Case B).

---

## Interactions

### Interaction: Ticker change (gainer click or search)

**Trigger:** `ticker` prop received by `TradingViewChart` changes to a new non-null string
**Component:** `TradingViewChart`
**Behavior:**
1. `useEffect` fires (dependencies: `ticker`, `selectedTimeframe`, `selectCount`)
2. Previous widget DOM is torn down (container contents cleared; any in-flight script `onload` is voided via a mounted ref flag)
3. `status` is set to `"loading"`; skeleton overlay is shown
4. New script tag is created and appended to `document.head`
5. On script `onload`: widget constructor is called targeting the container `div`; `status` is set to `"ready"`; skeleton is removed
6. On script `onerror`: `status` is set to `"error"`; skeleton is replaced by error message

**Loading state:** Skeleton overlay covers the chart container (same height)
**Error state:** Error message replaces skeleton in the chart container area
**Success state:** TradingView chart renders inside the container

**Deduplication:** When `selectCount` increments but `ticker` and `selectedTimeframe` are unchanged (tracked via refs) and `status` is `"ready"`, the effect returns early — no re-initialization, no flash. The effect only proceeds when either a value has actually changed or the chart is in error state.

---

### Interaction: Timeframe button click

**Trigger:** User clicks one of the 4 timeframe buttons (1D, 5D, 1M, 3M)
**Component:** `TradingViewChart` (internal `selectedTimeframe` state)
**Behavior:**
1. `setSelectedTimeframe(newValue)` is called
2. `useEffect` fires (dependency: `selectedTimeframe`)
3. Follows same destroy-and-recreate sequence as ticker change
4. Widget is re-initialized with updated `range` and `interval` values from `TIMEFRAME_TO_TV_INTERVAL`

**Loading state:** Skeleton overlay shown during re-initialization
**Error state:** Error message if re-initialization fails
**Success state:** Chart re-renders with new timeframe

---

### Interaction: Same ticker re-selected

**Trigger:** User clicks a gainer row whose ticker matches the currently displayed ticker, or submits the same ticker via search

**When chart status is `"ready"` (chart working):**
`selectCount` increments (it always does on every selection), so the `useEffect` fires. But inside the effect, the ref-based dedup check sees that `ticker` and `selectedTimeframe` are unchanged and `status` is `"ready"` — so it returns early. No re-initialization, no visible flash or reload.

**When chart status is `"loading"` (chart initializing):**
Same behavior as `"ready"` — the dedup check returns early because re-initializing while already loading would be wasteful. The in-progress initialization continues undisturbed.

**When chart status is `"error"` (error state):**
`selectCount` increments, so the `useEffect` fires. Inside the effect, the ref-based dedup check sees that `ticker` and `selectedTimeframe` are unchanged but `status` is `"error"` — so it proceeds with re-initialization. `status` transitions to `"loading"`; the skeleton overlay replaces the error message; a new widget initialization is attempted. This is a forced retry triggered by the user's explicit re-selection.

---

### Interaction: Rapid ticker switching

**Trigger:** User clicks multiple gainer rows in quick succession
**Component:** `TradingViewChart`
**Behavior:**
1. Each `ticker` prop change triggers `useEffect` cleanup
2. The cleanup function sets a `mounted` flag to false for the previous effect
3. The previous effect's `onload` callback checks the flag before calling `status` updates
4. Only the last-selected ticker's widget initialization completes
5. Intermediate ticker widgets are discarded before they render

**Visible result:** A single loading skeleton is shown; only the final ticker's chart appears.

---

## Timeframe Selector Specification

The timeframe selector is a row of 4 buttons rendered above the chart container, inside the `TradingViewChart` outer wrapper.

**Position:** Above the chart container, inside the outer card wrapper
**Visibility:** Rendered only when `ticker !== null` (hidden in idle state)
**Default active timeframe:** `"1D"` (initial `selectedTimeframe` state value)

**Button layout:**
```
[1D] [5D] [1M] [3M]
```
Left-aligned row. Buttons are compact, not full-width.

**Active button appearance:**
- Background: `bg-border-card` (`#2a3447`) or a slightly brighter variant to distinguish from inactive
- Text: `text-text-primary` (`#eef1f8`), `font-bold`
- Accent indicator: `#a78bfa` — e.g., a bottom border or subtle background tint in this color. This value matches the Header's ticker text color (`text-[#a78bfa]`), providing visual consistency across the right panel. The CSS variable `--color-badge-grok` (`#8b5cf6`) is NOT used for this element; the literal `#a78bfa` is used instead.

**Inactive button appearance:**
- Background: transparent
- Text: `text-text-secondary` (`#9aa7c7`)
- On hover: background `bg-border-card` (`#2a3447`)

**Button sizing:** `text-xs font-bold px-3 py-1.5 rounded-[var(--radius-sm)]` — matches `RiskBadgeInline` sizing pattern

**Spacing between selector row and chart container:** `gap` of `mb-2` or `space-y-2` via outer wrapper

---

## Component Hierarchy

```
page.tsx (Home)
├── [Left sidebar]
│   ├── GainerPanel (TradingView)
│   │   └── GainerRow (×n)
│   └── GainerPanel (Massive)
│       └── GainerRow (×n)
└── [Right panel]
    ├── TickerSearch
    └── {(isLoading || dilutionData) && (
        ├── Header
        ├── TradingViewChart          ← NEW
        │   ├── TimeframeSelector     ← internal sub-element (not a separate component file)
        │   │   ├── TimeframeButton ("1D")
        │   │   ├── TimeframeButton ("5D")
        │   │   ├── TimeframeButton ("1M")
        │   │   └── TimeframeButton ("3M")
        │   ├── ChartContainer        ← the TradingView mount target div
        │   ├── SkeletonOverlay       ← shown when status === "loading"
        │   └── ErrorMessage          ← shown when status === "error"
        ├── Headlines
        ├── RiskBadges
        ├── OfferingAbility
        ├── InPlayDilution
        ├── Offerings (conditional)
        ├── GapStats (conditional)
        ├── JMT415Notes
        ├── MgmtCommentary (conditional)
        └── Ownership (conditional)
    )}
```

`TimeframeSelector`, `TimeframeButton`, `ChartContainer`, `SkeletonOverlay`, and `ErrorMessage` are internal JSX elements within `TradingViewChart.tsx` — they are not separate component files.

---

## State Visibility

| State | Visible In | Updated By |
|-------|------------|------------|
| `selectedTicker` (page.tsx) | Header, TradingViewChart (via `ticker` prop), Headlines, all dilution components | `handleSearch`, `handleGainerSelect` in `page.tsx` |
| `sidebarSelectedTicker` (page.tsx) | GainerRow highlight state in both GainerPanel instances | `handleGainerSelect`; reset to `null` by `handleSearch` |
| `isLoading` (page.tsx) | Conditional block render gate; Header skeleton, Headlines skeleton | `loadTicker()` async flow |
| `dilutionData` (page.tsx) | All right-panel components (Header, Headlines, RiskBadges, etc.) | `loadTicker()` success path |
| `error` (page.tsx) | App error panel in right panel | `loadTicker()` error path |
| `selectCount` (page.tsx) | Not directly visible; passed as prop to `TradingViewChart`; forces `useEffect` re-execution when incremented | `handleGainerSelect`, `handleSearch` — incremented on every selection action |
| `status` (TradingViewChart internal) | Chart container content (skeleton, active chart, or error message) | `useEffect` on `[ticker, selectedTimeframe, selectCount]`; script `onload`/`onerror` callbacks |
| `selectedTimeframe` (TradingViewChart internal) | Timeframe selector (active button highlight); chart widget `range`/`interval` config | Timeframe button click handler |

---

## Design Token Reference (for implementer)

All values are already defined in `frontend/src/app/globals.css`. No new tokens are required.

| Token | Hex | Usage in TradingViewChart |
|-------|-----|--------------------------|
| `--color-bg-card` | `#1b2230` | Outer wrapper background; TradingView widget `backgroundColor`; skeleton overlay fill |
| `--color-border-card` | `#2a3447` | Card border; inactive button hover background; TradingView widget `gridColor` |
| `--color-text-primary` | `#eef1f8` | Active timeframe button text |
| `--color-text-secondary` | `#9aa7c7` | Inactive timeframe button text; idle placeholder text; error message text |
| `--color-accent` (pink) | `#ff4fa6` | Not used in chart widget (reserved for TickerSearch button, GainerPanel refresh) |
| `--color-badge-grok` (purple) | `#8b5cf6` | Not used for the active timeframe button accent |
| `#a78bfa` (literal) | `#a78bfa` | Active timeframe button accent indicator (bottom border or tint). This is the same literal hex used by the Header component for ticker text (`text-[#a78bfa]`). It is used here as a literal rather than a CSS variable to match the Header's treatment and maintain visual consistency across the right panel. |
| `--radius` | `9px` | Outer card border-radius |
| `--radius-sm` | `5px` | Timeframe button border-radius; skeleton overlay border-radius |

---

## Requirement Coverage Verification

| Requirement | Covered In This Spec |
|-------------|---------------------|
| US-01: Chart placed between Header and Headlines | Layout Structure section; Component Hierarchy |
| US-02: Auto-update on gainer click | Flow 1; Interaction: Ticker change |
| US-03: Auto-update on search | Flow 2; Interaction: Ticker change |
| US-04: Timeframe selector (1D/5D/1M/3M) | Timeframe Selector Specification; State 3 layout; Flow 3 |
| US-04: Timeframe persistence on ticker change | Flow 3 (timeframe persists) |
| US-05: Dark theme | Design Token Reference; State 3 widget config |
| US-06: Loading skeleton | State 2; Interaction: Ticker change — loading state |
| US-07: Error message | State 4; Interaction: Ticker change — error state; Flow 5 |
| US-08: Idle placeholder | State 1; Flow 4 |
| Edge: Same ticker re-selected (active) | Interaction: Same ticker re-selected — active state (no-op) |
| Edge: Same ticker re-selected (error) | Interaction: Same ticker re-selected — error state (force retry via selectCount); Flow 5 Case B |
| Edge: Rapid ticker switching | Interaction: Rapid ticker switching |
| Edge: Offline / CDN blocked | State 4 (error message shown) |
| AC: min-height 300px | State 2 and 3 layout notes (340px specified) |
| AC: No horizontal overflow | Layout: `autosize: true` + right panel `overflow-y-auto` contains it |

---

## Out-of-Scope Reminders

The following are explicitly not specified here and must not be implemented:

- Custom dataset intraday charting
- TradingView Lightweight Charts library
- Paid TradingView API or data subscription
- Drawing tools or indicator configuration beyond 4 timeframe buttons
- Timeframe persistence across page reloads (no localStorage)
- Mobile layout optimization
- Mini-charts / sparklines in gainer sidebar rows
- Backend changes of any kind
