# Requirements: v2-dilution-dashboard

**Version:** 2.0
**Date:** 2026-04-03
**Status:** Draft
**Source documents:** specs/v2/INTAKE.md, ask-edgar-repo/das_monitor.py

---

## Summary

Upgrade the Gap Lens Dilution web app to match feature parity with the AskEdgar Dilution Monitor V2 desktop app. The upgrade adds five new AskEdgar API integrations (Gap Statistics, Recent Offerings, Ownership, AI Chart Analysis, Top Gainers proxy), a two-panel layout with a scrollable Top Gainers sidebar, in-memory API response caching, seven new frontend components, and updates to three existing components. The web app already has a working FastAPI backend and a Next.js frontend with placeholder-only data; V2 wires them together and extends both layers.

---

## User Stories

### US-01 — Two-Panel Layout
As a trader in the accountability group,
I want a persistent left sidebar showing top premarket gainers alongside the dilution detail panel on the right,
so that I can monitor which tickers are moving while drilling into dilution data without switching views.

### US-02 — Top Gainers Sidebar
As a trader,
I want to see a ranked list of stocks gapping up at least 15% premarket, enriched with their dilution risk level, chart rating, float, market cap, sector, and country,
so that I can quickly identify which gappers are worth researching.

### US-03 — Click-to-Load Gainer
As a trader,
I want to click any gainer row in the sidebar to load that ticker's full dilution detail in the right panel,
so that I can move from discovery to analysis without retyping the ticker.

### US-04 — Ticker Search Wired to API
As a trader,
I want to type a ticker in the search field and submit it to load live data from the backend,
so that I can look up any ticker, not just the ones listed in the gainers panel.

### US-05 — Gap Statistics Panel
As a trader,
I want to see computed gap statistics for the selected ticker (last gap date, number of gaps, avg gap %, avg open-to-high, avg open-to-low, % new high after 11am, % closed below VWAP, % closed below open) with traffic-light color coding,
so that I can assess whether this stock is historically a fader or a runner after gapping up.

### US-06 — Recent Offerings Panel
As a trader,
I want to see the three most recent offerings for the selected ticker (type, amount, price, warrants, date) with in-the-money price highlighting,
so that I can judge the dilution pressure from recent capital raises relative to the current stock price.

### US-07 — Ownership Panel
As a trader,
I want to see the most recently reported insider and institutional ownership table (owner name, title, share count) for the selected ticker,
so that I can understand who holds meaningful positions.

### US-08 — AI Chart Analysis Badge
As a trader,
I want to see the AI chart analysis rating (Strong / Semi-Strong / Mixed / Fader) displayed as a badge next to the ticker in the header,
so that I can evaluate the technical chart history at a glance.

### US-09 — In-Play Dilution — Convertibles Extension
As a trader,
I want to see both warrants and convertibles in the In Play Dilution section, each row colored green when the exercise/conversion price is at or below the current stock price and orange otherwise,
so that I can identify which instruments are immediately exercisable and thus pose active dilution risk.

### US-10 — Offering Ability — Parsed Capacity Display
As a trader,
I want the Offering Ability section to parse the raw description text and display each capacity segment on its own line, highlighting shelf capacity, ATM capacity, and equity line capacity in green when funded and red when at $0.00, and marking pending S-1/F-1 registrations distinctly,
so that I can quickly see the issuer's remaining ability to raise capital.

### US-11 — Management Commentary Panel
As a trader,
I want to see the management commentary text from the dilution-rating response displayed as a labeled text card,
so that I can read qualitative context about the company's capital management stance.

### US-12 — Stock Price in Header
As a trader,
I want to see the current stock price displayed in the header alongside the ticker and risk badge,
so that I can see the price context without leaving the dilution view.

### US-13 — API Response Caching (30-Minute TTL)
As a trader using the tool throughout a trading session,
I want repeated lookups for the same ticker within 30 minutes to be served from cache rather than re-fetching from AskEdgar,
so that the tool remains fast, avoids hitting the 50-ticker/day rate limit prematurely, and reduces API latency.

### US-14 — Gainers Auto-Refresh Every 60 Seconds
As a trader monitoring premarket activity,
I want the Top Gainers sidebar to automatically refresh every 60 seconds,
so that newly gapping stocks appear without me taking any action.

### US-15 — Error States for All Components
As a trader,
I want to see clear error messages (ticker not found, rate limit hit, API unavailable) when a data fetch fails, rather than a broken or empty view,
so that I can understand what went wrong and retry or search a different ticker.

### US-16 — Loading Skeletons During Data Fetch
As a trader,
I want to see skeleton placeholders in all data panels while data is being fetched from the backend,
so that the UI does not flash empty or broken states during load.

### US-17 — Frontend API Service Layer
As a developer,
I want a centralized frontend API service module that handles all fetch calls to the backend endpoints,
so that components do not contain raw fetch logic and error handling is consistent.

### US-18 — Extended Dilution Endpoint Response
As a developer,
I want the existing `GET /api/v1/dilution/{ticker}` backend endpoint to include gap stats, recent offerings, ownership, chart analysis, stock price, and management commentary in its response,
so that the frontend can load all dilution detail in a single request.

### US-19 — New Gainers Backend Endpoint
As a developer,
I want a `GET /api/v1/gainers` backend endpoint that fetches and enriches the TradingView top gainers list and returns it as JSON,
so that the frontend does not make cross-origin calls to TradingView directly.

---

## Acceptance Criteria

### AC-01: Two-Panel Layout

- [ ] Given the app loads, when the page renders, then a left panel approximately 260px wide is visible alongside a right panel that fills the remaining width.
- [ ] Given a 1280px wide viewport, when the page is viewed, then both panels are fully visible without horizontal scrolling.
- [ ] Given a user scrolls the right panel content, when the content is taller than the viewport, then only the right panel scrolls; the left sidebar remains stationary.

### AC-02: Top Gainers Sidebar

- [ ] Given the sidebar fetches gainers, when results arrive, then only tickers matching the pattern `^[A-Z]{2,4}$` with premarket change >= 15% are displayed.
- [ ] Given a gainer row renders, when data is present, then the row shows: ticker (cyan), risk badge (color-coded by level), change percentage (green if positive, red if negative), current price, volume, float, market cap, sector (abbreviated per the defined short map), and country.
- [ ] Given a gainer has a news/8-K/6-K filing dated today, when the row renders, then a "News" badge (cyan background) appears next to the risk badge.
- [ ] Given a gainer has a chart analysis rating, when the row renders, then the history rating label is visible in the row (or via badge coloring consistent with HISTORY_MAP).
- [ ] Given no gainers meet the 15% filter, when the sidebar finishes loading, then the message "No gainers found" is displayed in the sidebar.

### AC-03: Click-to-Load Gainer

- [ ] Given a gainer row is clicked, when the click fires, then the right panel begins loading data for that ticker.
- [ ] Given a gainer row is clicked and then another is clicked, when the second click fires, then the right panel loads the second ticker's data.
- [ ] Given a gainer row is selected, when the sidebar renders, then that row is visually distinguished from others (different background color).

### AC-04: Ticker Search Wired to API

- [ ] Given the user types a valid ticker and presses Enter or clicks the search button, when the form submits, then a loading state appears in the right panel and a GET request is made to `/api/v1/dilution/{ticker}`.
- [ ] Given the user submits an empty field, when the form submits, then no API request is made and the current view remains unchanged.
- [ ] Given the user submits a ticker via search while a gainer is selected, when the response loads, then the gainer selection highlight is cleared in the sidebar.

### AC-05: Gap Statistics Panel

- [ ] Given the dilution response includes `gapStats`, when the panel renders, then it displays: Last Gap Date, Number of Gaps, Avg Gap %, Avg Open→High (always green), Avg Open→Low (always red), % New High After 11am, % Closed Below VWAP, % Closed Below Open.
- [ ] Given % Closed Below VWAP is <= 59%, when the value renders, then it is green (`#5ce08a`). Given it is 60-84%, then orange (`#f7b731`). Given it is >= 85%, then red (`#ff6b6b`).
- [ ] Given % Closed Below Open is <= 50%, when the value renders, then it is green. Given it is 51-74%, then orange. Given it is >= 75%, then red.
- [ ] Given % New High After 11am is >= 45%, when the value renders, then it is green. Given it is 21-44%, then orange. Given it is <= 20%, then red.
- [ ] Given `gapStats` is an empty array, when the panel renders, then the Gap Stats panel is not shown (or shows a "no data" message) rather than showing NaN or zero values.
- [ ] Given `high_time` is an ISO timestamp in EST, when % New High After 11am is computed, then the threshold is 11:00 EST (hour >= 11).

### AC-06: Recent Offerings Panel

- [ ] Given the dilution response includes `offerings`, when the panel renders, then it shows up to 3 offerings (the 3 most recent) in order from most recent to oldest. Note: the backend fetches up to 5 offerings (`limit=5`) so that filtering (e.g., ATM USED rows) does not reduce the visible count below 3; the frontend slices to a maximum of 3 for display.
- [ ] Given an offering's `headline` contains the string "ATM USED" (case-insensitive), when that offering renders, then only the offering amount (formatted as $X.XXM) and date are shown, with the amount in green.
- [ ] Given a regular offering where `share_price <= stockPrice` and both are > 0, when the offering renders, then the price-related fields (shares amount, share price, warrants) are colored green.
- [ ] Given a regular offering where `share_price > stockPrice`, when the offering renders, then the price-related fields are colored orange.
- [ ] Given `offerings` is null or empty, when the panel renders, then the Recent Offerings section is hidden.

### AC-07: Ownership Panel

- [ ] Given the dilution response includes `ownership` with at least one owner, when the panel renders, then it displays a table with columns Owner, Title, and Shares.
- [ ] Given the ownership card renders, when the header is drawn, then the `reported_date` (truncated to YYYY-MM-DD) is shown in the card title.
- [ ] Given an owner has a `common_shares_amount`, when the shares cell renders, then the number is formatted with comma separators and colored green.
- [ ] Given `ownership` is null or has an empty `owners` array, when the panel renders, then the Ownership section is hidden.

### AC-08: AI Chart Analysis Badge

- [ ] Given the dilution response includes `chartAnalysis.rating == "green"`, when the header renders, then a badge labeled "HISTORY: Strong" with green background is visible.
- [ ] Given `rating == "yellow"`, then the badge reads "HISTORY: Semi-Strong" with yellow/gold background.
- [ ] Given `rating == "orange"`, then the badge reads "HISTORY: Mixed" with orange background.
- [ ] Given `rating == "red"`, then the badge reads "HISTORY: Fader" with red background.
- [ ] Given `chartAnalysis` is null or rating is absent, when the header renders, then no chart analysis badge is shown.

### AC-09: In-Play Dilution — Convertibles Extension

- [ ] Given the dilution response includes convertibles (items where `conversion_price` is present and `underlying_shares_remaining > 0`), when the In Play Dilution panel renders, then a "CONVERTIBLES" subsection is displayed below the "WARRANTS" subsection.
- [ ] Given a convertible has `conversion_price <= stockPrice` and `stockPrice > 0`, when the row renders, then remaining shares and conversion price are colored green.
- [ ] Given a convertible has `conversion_price > stockPrice`, when the row renders, then remaining shares and conversion price are colored orange.
- [ ] Given an item is marked "Not Registered" and is a convertible filed more than 180 days ago, when the list is built, then it is included (not skipped).
- [ ] Given an item is marked "Not Registered" and is a warrant, when the list is built, then it is excluded.
- [ ] Given `warrants_remaining == 0` or `underlying_shares_remaining == 0`, when the list is built, then that item is excluded.

### AC-10: Offering Ability — Parsed Capacity

- [ ] Given `offering_ability_desc` is a comma-separated string, when the Offering Ability panel renders, then each comma-delimited segment is displayed on its own line.
- [ ] Given a segment contains "shelf capacity" or "atm capacity" or "equity line capacity" and includes "$0.00", when rendered, then that line is red.
- [ ] Given a segment contains "shelf capacity" or "atm capacity" or "equity line capacity" and the value is not "$0.00", when rendered, then that line is green and bold.
- [ ] Given a segment contains "pending s-1" or "pending f-1" (case-insensitive), when rendered, then that line is green and bold.
- [ ] Given a warrant or convertible item has a strike price or conversion price exceeding 4x the current stock price (`strike_price > stockPrice * 4`), when the In-Play Dilution list is built, then that item is excluded from display regardless of its in-the-money status.

### AC-11: Management Commentary Panel

- [ ] Given the dilution response includes a non-empty `mgmtCommentary` string, when the right panel renders, then a card labeled "Mgmt Commentary" displays the text.
- [ ] Given `mgmtCommentary` is null or empty string, when the panel renders, then the Management Commentary card is not shown.

### AC-12: Stock Price in Header

- [ ] Given the dilution response includes a numeric `stockPrice > 0`, when the header renders, then the current stock price is displayed formatted as "$X.XX" (two decimal places for prices >= $1, four decimal places for prices < $1).
- [ ] Given `stockPrice` is null, 0, or absent, when the header renders, then the price field is either hidden or shows "N/A".

### AC-13: API Response Caching

- [ ] Given a ticker was fetched within the last 30 minutes, when the same ticker is requested again, then no new outbound HTTP request is made to AskEdgar for the cached endpoints (dilution-rating, float-outstanding, dilution-data, gap-stats, offerings, ownership, ai-chart-analysis, screener).
- [ ] Given the news endpoint is called, when any ticker is requested, then the response is always fetched live (never from cache).
- [ ] Given an AskEdgar endpoint returns an error or None result, when the cache is checked, then that error result is not stored (the next request will re-attempt the live fetch).
- [ ] Given 30 minutes have elapsed since a cache entry was stored, when the ticker is requested again, then a new outbound request is made.
- [ ] Given the cache key format is `"{endpoint}:{ticker}"` (e.g., `"dilution:EEIQ"`), when two different tickers are requested, then their cache entries are independent.

### AC-14: Gainers Auto-Refresh

- [ ] Given the sidebar has loaded, when 60 seconds elapse, then the sidebar automatically re-fetches the TradingView scanner and re-renders with updated data.
- [ ] Given a user manually triggers a refresh (by clicking a refresh button), when clicked, then a new fetch starts immediately and the 60-second timer resets.
- [ ] Given the sidebar is refreshing, when the fetch is in progress, then a "loading..." status indicator is visible in the sidebar header.
- [ ] Given the refresh completes, when the list is rendered, then the gainer count is displayed next to the header.

### AC-15: Error States

- [ ] Given the backend returns 404 for a ticker, when the right panel renders, then the message "No dilution data available for [TICKER]" is displayed.
- [ ] Given the backend returns 429, when the right panel renders, then a rate limit error message is displayed (not a generic error).
- [ ] Given the backend returns 500 or times out, when the right panel renders, then a generic API error message is displayed with enough context to retry.
- [ ] Given the `/api/v1/gainers` endpoint fails, when the sidebar renders, then an error state is shown in the sidebar rather than a blank panel.

### AC-16: Loading Skeletons

- [ ] Given a ticker search is submitted, when the API call is in flight, then skeleton placeholder elements are visible in all content sections of the right panel.
- [ ] Given the gainers endpoint is fetching, when the sidebar is in the loading state, then a loading indicator (not a blank sidebar) is shown.

### AC-17: Frontend API Service Layer

- [ ] Given a component needs to fetch dilution data, when it calls the API service, then it does not contain inline `fetch()` calls or hardcoded base URLs.
- [ ] Given the backend base URL is configured in an environment variable or config constant, when the service module runs, then all API calls use that base URL consistently.
- [ ] Given an API call fails, when the service function returns, then it returns a typed error result that components can render without throwing unhandled exceptions.

### AC-18: Extended Dilution Endpoint Response

- [ ] Given a GET request to `/api/v1/dilution/{ticker}`, when the response succeeds, then the JSON body includes the fields: `gapStats` (array), `offerings` (array, max 5), `ownership` (object or null), `chartAnalysis` (object or null with `rating` field), `stockPrice` (number or null), and `mgmtCommentary` (string or null).
- [ ] Given any of the new AskEdgar sub-calls fail, when the main endpoint responds, then the failed fields return null or empty array (not a 500 error), and the successfully fetched fields are still returned.
- [ ] Given the dilution endpoint is called, when the backend fetches the screener for stock price, then the price is included in the response as `stockPrice`.

### AC-19: New Gainers Backend Endpoint

- [ ] Given a GET request to `/api/v1/gainers`, when the TradingView scanner returns data, then the response is a JSON array of gainer objects each containing: `ticker`, `todaysChangePerc`, `price`, `volume`, and enrichment fields (`float`, `marketCap`, `sector`, `country`, `risk`, `chartRating`, `newsToday`).
- [ ] Given the TradingView scanner POST returns no results or fails, when `/api/v1/gainers` is requested, then the endpoint returns an empty array with a 200 status, not a 500.
- [ ] Given a ticker from TradingView does not match `^[A-Z]{2,4}$`, when the gainers list is built, then that ticker is excluded from the response.
- [ ] Given a ticker from TradingView has premarket change < 15%, when the gainers list is built, then that ticker is excluded from the response.
- [ ] Given the enrichment calls for float, dilution, and chart analysis for each gainer are made, when they are executed, then they run in parallel (not sequentially) to meet the 60-second refresh budget.

---

## Edge Cases

| Case | Expected Behavior |
|------|-------------------|
| Ticker not found in AskEdgar (404) | Right panel shows "No dilution data available for [TICKER]" error state; other panels that returned data still render |
| `gapStats` is non-empty but all entries have null `market_open` | Avg Open→High and Avg Open→Low display as 0.0% or are omitted; no crash |
| `high_time` field is missing or malformed ISO string | That gap entry is skipped in the "new high after 11am" computation without crashing |
| Offering has null `share_price` | In-the-money color check is skipped; offering renders without price highlight |
| Ownership `owners` array is present but empty | Ownership panel is not rendered |
| `chartAnalysis.rating` is an unrecognized string value | No badge is shown (graceful fallback to hidden state) |
| `offering_ability_desc` is an empty string or null | Offering Ability section is hidden |
| `mgmt_commentary` field is an empty string (not null) | Management Commentary card is not shown |
| TradingView scanner returns a ticker with 1 or 5+ characters | Ticker is filtered out by `^[A-Z]{2,4}$` regex before enrichment |
| AskEdgar enrichment for a gainer times out | Gainer row still appears with partial data; missing enrichment fields show as empty or "N/A" |
| Gainer row is clicked while a previous ticker is still loading | The previous load is superseded; the newly clicked ticker's data is shown |
| Stock price is 0 or null when evaluating in-the-money status | In-the-money color logic is skipped; all strike/conversion prices render orange |
| API key is missing from the backend environment | Backend returns a clear 500 with a message indicating the missing key; frontend shows API error state |
| Cache hit for a ticker where float and dilution data both exist but chart analysis was null | Chart analysis null is not cached; next request for chart analysis re-fetches live |
| Convertible filed exactly 180 days ago | The 180-day cutoff is exclusive (> 180 days); exactly 180 days is treated as not old enough and remains excluded if "Not Registered" |

---

## Out of Scope

- NOT: DAS Trader window title scraping (win32gui, `find_montage_windows`) — desktop-only feature, not applicable to the web app.
- NOT: thinkorswim window title monitoring (`find_tos_tickers`) — desktop-only, not applicable.
- NOT: yfinance real-time price enrichment for gainers — TradingView scanner price data is used directly; yfinance enrichment is a deferred follow-up.
- NOT: `massive_backup.py` / Polygon API integration — reference only, not part of this upgrade.
- NOT: Mobile responsive design — the layout is desktop-first; no breakpoints or touch optimizations are required.
- NOT: DAS Trader auto-detect (window polling at 1-second intervals) — web app uses manual search only.
- NOT: Window drag-to-move behavior from the desktop overlay — not applicable to a browser tab.
- NOT: Export or download of any data panels.
- NOT: User authentication or per-user settings.
- Deferred: yfinance price enrichment for gainers (mentioned as a follow-up in the intake).
- Deferred: Enterprise `/v1/registrations` endpoint wiring for the new components (the existing backend already calls it; its data is exposed in `offering_ability_desc` which is parsed client-side).

---

## Constraints

- Must: All AskEdgar API calls use the same `ASKEDGAR_API_KEY` from the `.env` file; the key must never be exposed to the frontend.
- Must: Respect the AskEdgar rate limit of 50 unique tickers per day per endpoint; cache results for 30 minutes to reduce consumption.
- Must: The news endpoint (`/enterprise/v1/news`) must always be fetched live — it must not be cached.
- Must: The backend caches results in-memory using a dict keyed by `"{endpoint}:{ticker}"` with a timestamp; None/error results must not be cached.
- Must: The TradingView scanner URL (`https://scanner.tradingview.com/america/scan`) requires no API key and must be called server-side from the backend, not client-side from the browser.
- Must: Gainer enrichment (float, dilution rating, chart analysis, news check) must be performed in parallel (concurrent HTTP calls) per gainer.
- Must: The design system from the Gap Research project is applied: background `#0e111a`, card background `#1b2230`, border `#2a3447`, accent `#ff4fa6`, fonts Space Grotesk (UI) and JetBrains Mono (data). The V2 desktop app uses a different palette (cyan accent, darker background) which is explicitly not adopted here.
- Must: Risk badge colors follow: High → `#A93232`, Medium → `#B96A16`, Low → `#2F7D57`, N/A → `#4A525C`.
- Must: The left panel width is approximately 260px (fixed); the right panel fills all remaining horizontal space.
- Must: The existing backend retry logic (3 retries with exponential backoff) applies to all new AskEdgar endpoint calls.
- Must: The existing custom exceptions (`TickerNotFoundError`, `RateLimitError`, `ExternalAPIError`) are used and propagated correctly for new endpoints.
- Assumes: The AskEdgar enterprise API endpoints use the `/enterprise/v1/` prefix and standard endpoints use `/v1/` prefix — this must not be swapped (table confirmed in the intake).
- Assumes: `management commentary` (mgmt_commentary) is a field already returned by the existing `/enterprise/v1/dilution-rating` endpoint, not a new endpoint call. If this assumption is wrong, a new AskEdgar endpoint call is required.
- Assumes: The Next.js frontend is running on Node 18+ and the existing Tailwind + TypeScript setup can be extended without framework changes.
- Must not: Cache the gainers list for 30 minutes — gainers use a shorter 60-second server-side TTL for the `/api/v1/gainers` endpoint response.

---

## API Endpoint Mapping

| User Story | Backend Route | AskEdgar Endpoint | Cache TTL |
|---|---|---|---|
| US-02, US-03, US-14, US-19 | GET /api/v1/gainers | POST scanner.tradingview.com/america/scan + parallel AskEdgar enrichment | 60s (gainers list) |
| US-05, US-18 | GET /api/v1/dilution/{ticker} | GET /v1/gap-stats | 30 min |
| US-06, US-18 | GET /api/v1/dilution/{ticker} | GET /v1/offerings | 30 min |
| US-07, US-18 | GET /api/v1/dilution/{ticker} | GET /v1/ownership | 30 min |
| US-08, US-18 | GET /api/v1/dilution/{ticker} | GET /v1/ai-chart-analysis | 30 min |
| US-09, US-18 | GET /api/v1/dilution/{ticker} | GET /enterprise/v1/dilution-data (existing) | 30 min |
| US-12, US-18 | GET /api/v1/dilution/{ticker} | GET /enterprise/v1/screener | 30 min |
| US-11, US-18 | GET /api/v1/dilution/{ticker} | Field in /enterprise/v1/dilution-rating (existing) | 30 min |
| US-15 (news) | GET /api/v1/dilution/{ticker} | GET /enterprise/v1/news (existing) | Never cached |

---

## Component Mapping

| Component | Status | Depends On |
|---|---|---|
| TopGainersSidebar.tsx | New | GET /api/v1/gainers |
| GainerRow.tsx | New | TopGainersSidebar.tsx data |
| GapStats.tsx | New | gapStats[] in dilution response |
| Offerings.tsx | New | offerings[] in dilution response |
| Ownership.tsx | New | ownership object in dilution response |
| ChartAnalysisBadge.tsx | New | chartAnalysis in dilution response |
| MgmtCommentary.tsx | New | mgmtCommentary in dilution response |
| Header.tsx | Update | Add ChartAnalysisBadge, add stockPrice display |
| InPlayDilution.tsx | Update | Add convertibles section, add in-the-money color logic |
| OfferingAbility.tsx | Update | Parse offering_ability_desc into segments |
| page.tsx | Rewrite | Wire all components to API service; add two-panel layout |
| frontend/src/services/api.ts | New | Backend endpoints |
| frontend/src/types/dilution.ts | Update | Add new data shape types for V2 fields |
