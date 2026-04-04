# Requirements: tradingview-chart-widget

**Version:** 1.2
**Date:** 2026-04-04
**Status:** Draft
**Feature:** Embed TradingView Advanced Chart widget in the dilution dashboard right panel

**Change note (v1.2):** Replaced internal `retryKey` mechanism with `selectCount` prop from `page.tsx`. Added edge case for same-ticker re-selection in error state. Updated page.tsx constraint to reflect one new state variable.

**Change note (v1.1):** Addressed three gaps identified in 05-REVIEW.md and resolved open questions Q1, Q4, and Q5. Specific changes: (1) Added 2-second response AC to US-04. (2) Updated US-04 AC bullet 4 to specify timeframe persists on ticker change (removes "either behavior is acceptable" language, matches UI Spec decision). (3) Added CSP acceptance criterion to US-07. (4) Confirmed `#a78bfa` as accent color for active timeframe button in Constraints. (5) Added `hide_top_toolbar: true` constraint. (6) Added `allow_symbol_change: false` constraint.

---

## Summary

Add an embedded TradingView Advanced Chart widget to the right panel of the Gap Lens Dilution dashboard, positioned between the Header component and the Headlines component. The widget displays a price chart for the currently active ticker, updates automatically when the user clicks a gainer row or submits a search, and offers a 4-option timeframe selector. The chart uses TradingView's free embeddable Advanced Chart widget (iframe/script embed) styled to match the existing dark design system.

---

## User Stories

### US-01 — Chart Widget Placement
As an active trader using the dilution dashboard,
I want a price chart displayed between the Header and Headlines sections in the right panel,
so that I can see price action for the selected ticker in the same view as dilution data, without switching tools.

### US-02 — Auto-Update on Gainer Click
As an active trader,
I want the chart to automatically update to the selected ticker whenever I click a gainer row in either the TradingView or Massive gainers sidebar,
so that chart, dilution data, and gainer selection always refer to the same stock without any extra interaction.

### US-03 — Auto-Update on Search
As an active trader,
I want the chart to automatically update to the searched ticker whenever I submit a ticker via the search bar,
so that the chart stays in sync with the dilution data I am viewing.

### US-04 — Timeframe Selector
As an active trader,
I want to switch the chart between 1D, 5D, 1M, and 3M timeframes using a control on or adjacent to the chart widget,
so that I can assess short-term intraday action as well as multi-week context without leaving the dashboard.

### US-05 — Dark Theme
As an active trader,
I want the chart widget to use a dark color scheme consistent with the rest of the dashboard,
so that the embedded widget does not visually break the interface or cause eye strain during extended use.

### US-06 — Loading State
As an active trader,
I want to see a loading placeholder in the chart area while the widget initializes or while a new ticker is loading,
so that the layout does not shift unexpectedly and I know a chart is incoming.

### US-07 — Error / Unavailable State
As an active trader,
I want a clear fallback message in the chart area if the TradingView widget fails to load (e.g., network error, widget blocked),
so that I understand the chart is unavailable rather than assuming the panel is empty by design.

### US-08 — Idle / No Ticker State
As an active trader,
I want the chart area to show a neutral placeholder (not a broken embed) when no ticker has been selected yet,
so that the initial dashboard state looks intentional and complete.

---

## Acceptance Criteria

### US-01 — Chart Widget Placement
- [ ] Given the right panel renders, the chart widget appears after the Header component and before the Headlines component in the DOM order.
- [ ] Given the right panel is displayed at any viewport width supported by the existing layout, the chart widget does not overflow its container horizontally.
- [ ] Given the right panel renders, the chart widget has a defined minimum height of at least 300px.

### US-02 — Auto-Update on Gainer Click
- [ ] Given a ticker is displayed in the chart, when the user clicks a different gainer row in either sidebar column, then the chart widget updates to display that new ticker within 2 seconds.
- [ ] Given a ticker is already selected, when the user clicks the same ticker again in the sidebar, the chart does not reload or flash unnecessarily.
- [ ] Given the chart updates to a new ticker via gainer click, the Header and dilution data panel update to the same ticker simultaneously (existing behavior is preserved, chart is additive).

### US-03 — Auto-Update on Search
- [ ] Given a ticker is displayed in the chart, when the user submits a new ticker via the search bar, then the chart widget updates to that ticker within 2 seconds.
- [ ] Given the chart updates via search, the existing selectedTicker state propagation to dilution data components is not disrupted.

### US-04 — Timeframe Selector
- [ ] Given the chart is displaying a ticker, the timeframe selector offers exactly 4 options: 1D, 5D, 1M, 3M.
- [ ] Given the chart is displaying a ticker, when the user clicks a timeframe option, the chart reloads or updates to reflect that timeframe.
- [ ] Given the chart is displaying a ticker, the currently active timeframe option is visually distinguished from inactive options (e.g., highlighted, underlined, or bold).
- [ ] Given the user selects a new ticker while a non-default timeframe is active, the selected timeframe persists to the new ticker (it does not reset to 1D).
- [ ] Given the chart is displaying a ticker, when the user clicks a timeframe option, the chart updates to reflect that timeframe within 2 seconds.

### US-05 — Dark Theme
- [ ] Given the chart widget is rendered, the widget background color matches or closely approximates the existing card background (#1b2230 or equivalent dark token).
- [ ] Given the chart widget is rendered, no large white or light-colored background panels are visible within the chart embed area.

### US-06 — Loading State
- [ ] Given a ticker has been selected but the chart widget has not yet completed initialization, a skeleton or spinner placeholder is visible in the chart area.
- [ ] Given the skeleton is displayed, it occupies the same dimensions as the loaded chart to prevent layout shift.

### US-07 — Error / Unavailable State
- [ ] Given the TradingView widget script fails to load or throws an error, the chart area displays a human-readable message (e.g., "Chart unavailable") instead of a blank space or broken embed.
- [ ] Given the error state is shown, the rest of the right panel (Header, Headlines, dilution components) continues to render normally.
- [ ] Given the TradingView CDN script (`tv.js`) is blocked by a Content Security Policy rule or firewall at the network level, the chart area displays the error state (human-readable message) rather than a blank space or a broken embed.

### US-08 — Idle / No Ticker State
- [ ] Given no ticker has been selected and the dashboard is in its idle state, the chart area displays a placeholder message (e.g., "Select a ticker to view chart") rather than an empty or broken embed.
- [ ] Given the idle placeholder is shown, it does not trigger any TradingView widget initialization or network requests.

---

## Edge Cases

| Case | Expected Behavior |
|------|-------------------|
| User clicks a gainer while the previous chart is still loading | The widget cancels or replaces the in-flight load with the new ticker; no duplicate embeds appear |
| Ticker symbol contains characters not recognized by TradingView (e.g., OTC symbols with suffixes) | The widget renders with the ticker as supplied; if TradingView shows "symbol not found" inside the iframe, that is acceptable as a TradingView limitation, not an app error |
| User rapidly clicks multiple gainer rows in succession | Only the last selected ticker is shown; intermediate tickers do not cause flickering stacks of widgets |
| Network is offline when the widget attempts to load | The error state (US-07) is shown; the rest of the panel is unaffected |
| Right panel is very narrow (e.g., browser window resized small) | Chart widget scales or constrains within the panel without breaking the layout; horizontal scrollbar does not appear on the right panel |
| TradingView widget loads but the 1D intraday data is unavailable for the ticker | TradingView renders its own internal "no data" state inside the iframe; no special app-level handling required |
| User submits the same ticker that is already displayed (chart working) | Chart does not reload; no visible flash or re-initialization |
| User re-selects the same ticker while the chart is in error state | The chart retries loading; skeleton replaces error message; if CDN is now reachable, chart renders; if still unreachable, error message returns |
| Dashboard is accessed on a Tailscale-connected device with strict CSP or firewall rules blocking TradingView CDN | The error state (US-07) is shown; app does not crash |

---

## Out of Scope

- NOT: Historical intraday charting from Danny's own dataset. Custom dataset chart integration is explicitly deferred to a future sprint.
- NOT: TradingView Lightweight Charts library (open-source, custom implementation). The Advanced Chart embed widget is the required approach for this sprint.
- NOT: Any paid TradingView API or data subscription. Only the free embeddable widget is in scope.
- NOT: Drawing tools, technical indicator configuration, or any user-customization of the chart beyond the 4 timeframe options.
- NOT: Saving or persisting user-selected timeframe across page reloads or sessions.
- NOT: Mobile layout optimization. The app is accessed via Tailscale by a single user on desktop; mobile responsiveness is not a requirement.
- NOT: Chart data for the gainers sidebar rows (sparklines, mini-charts). The widget applies only to the main right-panel chart area.
- NOT: Backend API changes. The chart widget is a purely frontend concern and does not require new FastAPI endpoints.
- Deferred: Replacing the TradingView embed with a custom charting solution backed by Danny's intraday dataset.
- Deferred: Additional timeframe options beyond 1D, 5D, 1M, 3M.

---

## Constraints

- Must: Use TradingView's free embeddable Advanced Chart widget (iframe/script embed). No paid API.
- Must: Position the chart between the Header component and the Headlines component in `frontend/src/app/page.tsx`.
- Must: React to the existing `selectedTicker` state (or an equivalent derived from it) that is already propagated to Header, Headlines, and all dilution components. The chart must not introduce a separate ticker-selection mechanism.
- Must: Match the existing dark design system. Background tokens in use: card background `#1b2230`, border `#2a3447`, primary text `#eef1f8`, muted text `#9aa7c7`, accent purple `#a78bfa`, accent pink `#ff4fa6`. The active timeframe button accent color is `#a78bfa` (matching the Header ticker text color), not `#8b5cf6`.
- Must: Start with `hide_top_toolbar: false` in the TradingView widget configuration. Evaluate the toolbar visually during Slice 2 — if it exposes drawing tools, indicators, or other out-of-scope features that clutter the UI, flip to `true`. Decision deferred to visual review.
- Must: Set `allow_symbol_change: false` in the TradingView widget configuration. The widget's built-in symbol search is disabled because the dashboard provides its own ticker search via TickerSearch.
- Must: Build and serve via production build only (`npx next build && npx next start -p 3001 -H 0.0.0.0`). No dev-server-only workarounds.
- Must not: Break existing component rendering order or state management in `page.tsx`. One new state variable (`selectCount`) is permitted in `page.tsx` to signal re-selection events to the chart component.
- Must not: Make any changes to the FastAPI backend (`app/main.py`) or any backend files.
- Must not: Introduce the chart widget into the idle state (no ticker selected) in a way that fires network requests to TradingView before a ticker is available.
- Assumes: TradingView's free Advanced Chart widget supports setting the symbol and timeframe via configuration options at initialization time (this is consistent with TradingView's published widget documentation as of the knowledge cutoff).
- Assumes: The right panel flex container in `page.tsx` (`flex-1 overflow-y-auto p-4 space-y-4`) provides sufficient width to render the chart at a useful size on Danny's desktop display.
- Assumes: The app is used by a single user (Danny) on a Tailscale-connected device, so cross-origin iframe restrictions are not a concern beyond standard browser defaults.
