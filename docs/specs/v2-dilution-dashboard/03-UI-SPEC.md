# UI Specification: v2-dilution-dashboard

**Version:** 2.0
**Date:** 2026-04-03
**Status:** Draft
**Author:** @ui-spec-writer
**Input documents:** 01-REQUIREMENTS.md, 02-ARCHITECTURE.md, specs/v2/INTAKE.md

---

## 1. Screens

| Screen | Purpose | Entry Point |
|--------|---------|-------------|
| DashboardPage | Two-panel workspace: left sidebar shows top premarket gainers; right panel shows full dilution detail for the selected ticker | Browser load — app has a single route (`/`) |
| DashboardPage (empty state) | Same page, right panel is empty/idle — no ticker selected yet | Initial page load before any interaction |
| DashboardPage (loading state) | Right panel shows skeleton placeholders while a dilution fetch is in flight | Immediately after a ticker is selected (click or search) |
| DashboardPage (error state) | Right panel shows an error card instead of data | When the dilution API returns 404, 429, or 500 |

There is one physical page (`page.tsx`). "Screens" are distinct visual states of that page, not separate routes.

---

## 2. User Flows

### Flow 1: Initial Load (US-01, US-02, US-14, US-16)

1. User opens the app in a browser.
2. System renders the two-panel shell immediately: left sidebar (~260px) + right panel (flex fill).
3. Sidebar automatically calls `GET /api/v1/gainers`.
4. While fetching: sidebar shows a loading indicator in its header ("Loading...") and skeleton rows.
5. Response arrives: sidebar renders ranked gainer rows, each with ticker, risk badge, change%, price, volume, float, mcap, sector, country.
6. Right panel: idle state — no ticker selected, panel shows a prompt ("Search a ticker or click a gainer to begin").
7. After 60 seconds: sidebar automatically re-fetches gainers without user action; a loading indicator reappears in the sidebar header during the refresh; gainer count is displayed next to the header title after load completes.

**Success path:** Both panels load; sidebar shows ranked gainer list; right panel waits for selection.
**Error path (gainers fail):** Sidebar shows an error state message ("Could not load gainers. Retry?") with a manual refresh button; right panel is unaffected.

---

### Flow 2: Click a Gainer (US-03, US-08, US-09, US-12, US-16)

1. User sees the gainer list in the sidebar.
2. User clicks a GainerRow (e.g., "MNTK").
3. Immediately: clicked row receives a selected highlight background (`bg-bg-card-hover` + `border-accent`); any previously selected row reverts to default.
4. Right panel: `dilutionData` is set to `null`, all panels show their skeleton placeholders.
5. System calls `GET /api/v1/dilution/MNTK`.
6. Response arrives: right panel renders all data panels in order (see Section 6 — Render Order).
7. If user clicks a second gainer while load is in flight: the in-flight request is aborted, the new ticker's load begins, the sidebar selection highlight moves to the newly clicked row.

**Success path:** Right panel fills with live dilution detail for the clicked ticker; sidebar highlight stays on that row.
**Error path:** Right panel shows an error card; sidebar highlight stays on the row so the user knows which ticker failed.

---

### Flow 3: Ticker Search (US-04, US-15, US-16)

1. User types a ticker symbol into the TickerSearch input (auto-uppercased).
2. User presses Enter or clicks "Search".
3. If input is empty: no request is made; current right panel state is unchanged.
4. If input has a value: sidebar selection highlight is cleared (no gainer row appears selected); right panel shows skeletons.
5. System calls `GET /api/v1/dilution/{ticker}`.
6. Response arrives: right panel renders data panels.
7. Search input remains populated with the searched ticker for reference.

**Success path:** Right panel shows dilution detail for the searched ticker; sidebar has no selection.
**Error path (404):** Right panel shows "No dilution data available for [TICKER]". Search input remains. User can retry or search another ticker.
**Error path (429):** Right panel shows "Rate limit exceeded. Try again later."
**Error path (500 / timeout):** Right panel shows "API error. Please retry."

---

### Flow 4: Manual Sidebar Refresh (US-14, AC-14)

1. User clicks the refresh button in the sidebar header (circular arrow icon).
2. Immediately: the current 60-second interval timer resets; a new fetch begins; sidebar header shows "Loading...".
3. Response arrives: gainer list re-renders with updated data; gainer count updates in the header; previously selected gainer row retains its highlight if the ticker still appears in the new list.

**Success path:** List updates within a few seconds; count updates.
**Error path:** Sidebar shows error state; previously loaded list remains visible (stale data shown, not blank).

---

## 3. Page Layout

### 3.1 Overall Shell

```
┌──────────────────────────────────────────────────────────────────────────┐
│ viewport: full height (100vh), overflow hidden                           │
│                                                                          │
│  ┌────────────────────┐  ┌───────────────────────────────────────────┐  │
│  │  LEFT SIDEBAR      │  │  RIGHT PANEL                              │  │
│  │  w: 260px (fixed)  │  │  flex-1 (fills remaining width)           │  │
│  │  h: 100vh          │  │  h: 100vh                                 │  │
│  │  overflow-y: auto  │  │  overflow-y: auto                         │  │
│  │  bg: #0e111a       │  │  bg: #0e111a                              │  │
│  │  border-r: #2a3447 │  │  p: 16px                                  │  │
│  │                    │  │                                           │  │
│  │  [Sidebar Header]  │  │  [Content panels stacked vertically]      │  │
│  │  [Gainer Rows...]  │  │                                           │  │
│  └────────────────────┘  └───────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

**CSS / Tailwind:**
- Root wrapper: `flex h-screen overflow-hidden bg-[#0e111a]`
- Left sidebar: `w-[260px] shrink-0 border-r border-[#2a3447] flex flex-col h-full overflow-hidden`
- Right panel: `flex-1 overflow-y-auto p-4 space-y-4`

---

### 3.2 Left Sidebar Layout

```
┌─────────────────────────┐
│  SIDEBAR HEADER         │  px-3 py-2, border-b border-[#2a3447]
│  "Top Gainers"          │  text-[#a78bfa] text-sm font-bold
│  [count badge] [↻ btn]  │  count: text-xs text-[#9aa7c7], button: text-[#ff4fa6]
│  [Loading... indicator] │  shown only while fetching
├─────────────────────────┤
│  SCROLLABLE LIST        │  flex-1 overflow-y-auto
│  ┌─────────────────────┐│
│  │ GainerRow           ││  repeated per gainer
│  └─────────────────────┘│
│  ┌─────────────────────┐│
│  │ GainerRow (selected)││  different background
│  └─────────────────────┘│
│  ...                    │
│  [No gainers found]     │  shown when list is empty after load
└─────────────────────────┘
```

**Sidebar header Tailwind:** `flex items-center justify-between px-3 py-2 border-b border-[#2a3447] shrink-0`

**Title:** `<h2 className="text-[#a78bfa] text-sm font-bold font-[Space_Grotesk]">Top Gainers</h2>`

**Count badge:** `<span className="text-[#9aa7c7] text-xs font-[JetBrains_Mono]">{count}</span>` — shown to the right of the title when data is loaded.

**Loading indicator (inline text):** `<span className="text-[#9aa7c7] text-xs animate-pulse">Loading...</span>` — appears in header during fetch; replaces count badge.

**Refresh button:** `<button className="text-[#ff4fa6] hover:text-[#ff6fbf] text-xs p-1 rounded transition-colors">↻</button>` — right side of header.

---

### 3.3 Right Panel States

**Idle (no ticker selected):**
```
┌──────────────────────────────────────────────────────┐
│                                                      │
│   [centered text block]                              │
│   "Search a ticker or click a gainer to begin."      │
│   text-[#9aa7c7] text-sm text-center                 │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Loading (skeletons):** All panels visible as `animate-pulse` skeleton blocks (see Section 9 — Loading States).

**Error:**
```
┌──────────────────────────────────────────────────────┐
│ bg-bg-card border border-[#2a3447] rounded-[9px] p-5 │
│                                                      │
│  [!] [Error message text]                            │
│       text-[#ff6b6b] text-sm                         │
│                                                      │
│  [Retry button] — calls same ticker again            │
└──────────────────────────────────────────────────────┘
```

**Loaded:** Panels stacked vertically per the render order in Section 6.

---

## 4. Component Specifications

### 4.1 GainerRow

**Purpose:** Single clickable entry in the sidebar list.

**Dimensions:** Full sidebar width (`w-full`), auto height; `px-2.5 py-1.5` inner padding.

**Backgrounds:**
- Default: `bg-[#1b2230]` (card color)
- Selected: `bg-[#222b3a]` (card hover) with `border border-[#ff4fa6]`
- Hover (not selected): `bg-[#222b3a]` (transition on hover)

**Border:** `border border-[#2a3447]` for default; `border border-[#ff4fa6]` for selected. `rounded-[5px]` (radius-sm). Margin: `mx-2 my-1`.

**Layout — three lines stacked:**

```
┌─────────────────────────────────────────────┐
│ TOP LINE:  TICKER [RISK] [News?]  +23.4%    │
│ MID LINE:  $1.24              Vol 2.3M      │
│ BOT LINE:  917K | 12.6M | Health | US       │
└─────────────────────────────────────────────┘
```

**Top line layout:** `flex items-center justify-between`

| Element | Content | Style |
|---------|---------|-------|
| Ticker symbol | e.g. "MNTK" | `text-[#63D3FF]` (cyan, matching desktop reference), `text-sm font-bold font-[JetBrains_Mono]` |
| Risk badge | e.g. "High" | Inline badge, see Risk Badge Colors (Section 5.1); `text-[10px] font-bold px-1.5 py-0.5 rounded-[3px] ml-1.5` |
| News badge | "News" | `bg-[#1F8FB3] text-white text-[10px] font-bold px-1.5 py-0.5 rounded-[3px] ml-1` — only shown when `newsToday === true` |
| Change % | "+23.4%" or "-5.1%" | `text-xs font-bold font-[JetBrains_Mono]`; positive: `text-[#5ce08a]`, negative: `text-[#ff6b6b]` |

**Middle line layout:** `flex items-center justify-between`

| Element | Content | Style |
|---------|---------|-------|
| Price | "$1.24" (2 decimal places if >= $1; 4 if < $1) | `text-xs text-[#eef1f8] font-[JetBrains_Mono]` |
| Volume | "Vol 2.3M" (formatted with M/K suffix) | `text-xs text-[#9aa7c7] font-[JetBrains_Mono]` |

**Bottom line layout:** `flex items-center` — rendered only when at least one value is present.

Content: float (formatted with M/K suffix), mcap (formatted), sector abbreviation, country — joined by ` | ` separator.

Sector abbreviation map:
```
Healthcare → "Health"
Technology → "Tech"
Industrials → "Indust"
Consumer Cyclical → "Cons Cyc"
Consumer Defensive → "Cons Def"
Communication Services → "Comms"
Financial Services → "Financ"
Basic Materials → "Materials"
Real Estate → "RE"
(any other) → full sector name
```

Style: `text-[10px] text-[#9aa7c7] font-[JetBrains_Mono]`

**Chart rating indicator:** The chart rating from `chartRating` is not displayed as a separate UI element in the row; it is reflected in the risk badge or shown as part of the gainer context. (The desktop reference displays the risk badge on the row's top line — the chart rating from `ai-chart-analysis` is used for the header badge in the right panel when that ticker is loaded, not in the sidebar row.)

**Click behavior:** Entire row surface is clickable. Clicking fires `onClick(ticker)`.

**Cursor:** `cursor-pointer` on the row wrapper.

---

### 4.2 TopGainersSidebar

**Purpose:** Manages fetching gainers and rendering the scrollable list.

**Internal state (managed by component):**
- `gainers: GainerEntry[]`
- `isLoading: boolean`
- `error: string | null`
- `lastUpdated: Date | null`

**Lifecycle:** On mount, fetches gainers immediately and sets a 60-second `setInterval`. On unmount, calls `clearInterval`.

**Empty state (loaded but 0 gainers):** Shows centered text "No gainers found" in `text-[#9aa7c7] text-xs text-center py-4`.

**Error state:** Shows `text-[#ff6b6b] text-xs text-center py-4` with message + a "Retry" text-button in `text-[#ff4fa6]`.

**Loading skeleton (sidebar):** 5 skeleton rows, each `h-14 bg-[#1b2230] rounded-[5px] mx-2 my-1 animate-pulse`.

---

### 4.3 Header (Updated)

**Purpose:** Shows ticker identity — symbol, overall risk badge, chart analysis badge, stock price, and float/market cap metadata.

**Container:** `bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5`

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│  ROW 1: TICKER (purple)    [HISTORY badge]   [RISK badge]   │
│  ROW 2: $price (data mono)                                  │
│  ROW 3: Float/OS: ... | MC: ... | Sector | Country (muted)  │
└─────────────────────────────────────────────────────────────┘
```

**Row 1:** `flex items-center gap-3 mb-1`
- Ticker: `<h1 className="text-3xl font-bold text-[#a78bfa]">{ticker}</h1>`
- ChartAnalysisBadge: rendered inline after ticker, before risk badge (see Section 4.9)
- Risk badge: `RISK: {level}` — colors per Section 5.1; `text-sm font-bold px-3 py-1 rounded-[5px] ml-auto text-white`

**Row 2 (stock price):** `mb-1`
- When `stockPrice >= 1`: `"$" + stockPrice.toFixed(2)`
- When `0 < stockPrice < 1`: `"$" + stockPrice.toFixed(4)`
- When `stockPrice` is null, 0, or absent: hide this row entirely (do not show "N/A")
- Style: `text-xl font-bold font-[JetBrains_Mono] text-[#eef1f8]`

**Row 3 (metadata):** `text-[#9aa7c7] text-sm`
- Format: `Float/OS: {float}/{outstanding} | MC: {marketCap} | {sector} | {country}`
- Separator: `<span className="mx-2 text-[#9aa7c7]">|</span>`

**Skeleton:** 
- Row 1: `h-9 w-32 bg-[#2a3447] rounded animate-pulse`
- Row 2: `h-6 w-20 bg-[#2a3447] rounded animate-pulse mt-1`
- Row 3: `h-4 w-96 bg-[#2a3447] rounded animate-pulse mt-2`

---

### 4.4 Headlines (Feed) — No Changes

**Purpose:** News, 8-K/6-K filings, and GROK summaries.

**No structural changes from V1.** Existing component is used as-is. Badge color map already defined in `Headlines.tsx`.

Filing badge colors (from `globals.css` tokens):
- 6-K: `bg-badge-6k` (`#d97706`)
- 8-K: `bg-badge-8k` (`#3b82f6`)
- GROK: `bg-badge-grok` (`#8b5cf6`)
- S-1: `bg-badge-s1` (`#ff6b6b`)
- 10-K/10-Q: `bg-badge-10k` (`#06b6d4`)
- SC 13D/SC 13G: `bg-badge-sc13` (`#ec4899`)
- Default/NEWS: `bg-badge-default` (`#6b7280`)

---

### 4.5 RiskBadges — No Changes

**Purpose:** Horizontal row of six sub-risk assessments.

**No structural changes from V1.** Existing component is used as-is.

Badge order: Overall Risk | Offering | Dilution | Frequency | Cash Need | Warrants.

Risk level colors:
- Low: `bg-risk-low` (`#36d29a`)
- Medium: `bg-risk-medium` (`#f7b731`)
- High: `bg-risk-high` (`#ff6b6b`)
- N/A: `bg-badge-default` (`#6b7280`)

---

### 4.6 OfferingAbility (Updated)

**Purpose:** Displays the issuer's remaining capital-raise capacity, parsed from the raw comma-separated `offeringAbilityDesc` string.

**Visibility:** Hidden entirely when `offeringAbilityDesc` is null, empty string, or absent.

**Container:** `bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5`

**Heading:** `text-lg font-bold text-[#a78bfa] mb-3` — "Offering Ability"

**Parsing rule:** Split `offeringAbilityDesc` on `,` (comma). `trim()` each segment. Each segment renders as its own line.

**Per-segment color rules:**

| Condition (case-insensitive match on segment text) | Text color | Font weight |
|---|---|---|
| Contains "pending s-1" or "pending f-1" | `#5ce08a` (accent-green) | `font-semibold` |
| Contains "shelf capacity", "atm capacity", or "equity line capacity" AND includes "$0.00" | `#ff6b6b` (accent-red) | normal |
| Contains "shelf capacity", "atm capacity", or "equity line capacity" AND does NOT include "$0.00" | `#5ce08a` (accent-green) | `font-semibold` |
| All other segments | `#eef1f8` (text-primary) | normal |

**Segment layout:** `<div className="text-sm px-3 py-1 rounded-[5px]">` per segment. No background tint for non-red/green items.

**Skeleton:** 4 skeleton lines: `h-4 w-48 bg-[#2a3447] rounded animate-pulse mb-2` each.

---

### 4.7 InPlayDilution (Updated)

**Purpose:** Warrants and convertibles that are currently "in play" (non-zero remaining).

**Container:** `bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5`

**Heading:** `text-lg font-bold text-[#a78bfa] mb-3` — "In Play Dilution"

**Structure — two subsections, stacked:**

```
[WARRANTS subsection] — rendered first
[CONVERTIBLES subsection] — rendered second, only if convertibles exist
```

**WARRANTS subsection heading:** `text-sm font-bold text-[#ff6b6b] mb-2` — "WARRANTS"

**CONVERTIBLES subsection heading:** `text-sm font-bold text-[#f7b731] mb-2 mt-4` — "CONVERTIBLES"

**Per-item card:** `border border-[#2a3447] rounded-[5px] p-3 bg-[rgba(10,14,22,0.4)] mb-2`

**Warrant item layout:**
```
Line 1: {issueDate} - {details}   →  text-sm text-[#eef1f8] mb-1.5
Line 2: Remaining: {remaining}  |  Strike: {strikePrice}  |  Filed: {filedDate}
```
Line 2 uses `font-[JetBrains_Mono]` monospace. Colors:
- "Remaining:" value: `text-[#ff6b6b]` (always red — draws attention to dilution risk)
- "Strike:" value: in-the-money color (see below)
- "Filed:" value: `text-[#9aa7c7]` (muted)

**Convertible item layout:**
```
Line 1: {details}   →  text-sm text-[#eef1f8] mb-1.5
Line 2: Remaining: {sharesRemaining}  |  Conv Price: {conversionPrice}  |  Filed: {filedDate}
```
- "Remaining:" value: in-the-money color
- "Conv Price:" value: in-the-money color
- "Filed:" value: `text-[#9aa7c7]`

**In-the-money color rule (applied to strike/conversion price fields):**
- `strikePrice <= stockPrice` AND `stockPrice > 0`: `text-[#5ce08a]` (green — in the money)
- `strikePrice > stockPrice` OR `stockPrice` is null/0: `text-[#f7b731]` (orange — out of money)

**Empty state:** If both `warrants` and `convertibles` arrays are empty: `<p className="text-[#9aa7c7] text-sm">No in-play dilution found.</p>`

**Warrants-only:** If convertibles are empty, the CONVERTIBLES subsection is not rendered.

**Skeleton:**
```
h-6 w-40 bg-[#2a3447] rounded mb-4 animate-pulse
h-5 w-28 bg-[#2a3447] rounded mb-3 animate-pulse
h-16 w-full bg-[#2a3447] rounded animate-pulse
h-16 w-full bg-[#2a3447] rounded animate-pulse mt-2
```

---

### 4.8 GapStats (New)

**Purpose:** Displays computed historical gap statistics with traffic-light color coding.

**Visibility:** Hidden entirely when `rawEntries` is an empty array.

**Container:** `bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5`

**Heading:** `text-lg font-bold text-[#a78bfa] mb-3` — "Gap Stats"

**Layout:** Vertical list of label-value rows. Each row: `flex items-center justify-between py-1`.
- Label: `text-sm text-[#9aa7c7] w-44 shrink-0`
- Value: `text-sm font-bold font-[JetBrains_Mono]` + color per table below

**Computed statistics (in display order):**

| Row label | Value format | Color rule |
|-----------|-------------|------------|
| Last Gap Date | YYYY-MM-DD from `gaps[0].date` | `text-[#eef1f8]` |
| Number of Gaps | integer count | `text-[#eef1f8]` |
| Avg Gap % | `+{n:.1f}%` | `text-[#eef1f8]` |
| Avg Open→High | `+{n:.1f}%` | Always `text-[#5ce08a]` (green) |
| Avg Open→Low | `{n:.1f}%` (negative) | Always `text-[#ff6b6b]` (red) |
| % New High After 11am | `{n:.0f}%` | >= 45%: `#5ce08a`; 21–44%: `#f7b731`; <= 20%: `#ff6b6b` |
| % Closed Below VWAP | `{n:.0f}%` | <= 59%: `#5ce08a`; 60–84%: `#f7b731`; >= 85%: `#ff6b6b` |
| % Closed Below Open | `{n:.0f}%` | <= 50%: `#5ce08a`; 51–74%: `#f7b731`; >= 75%: `#ff6b6b` |

**Computation logic (performed inside `GapStats` component):**
- `avgGapPct`: mean of `gap_percentage` fields where not null
- `avgOpenToHigh`: mean of `(high_price - market_open) / market_open * 100` where both are non-null and `market_open > 0`
- `avgOpenToLow`: mean of `(low_price - market_open) / market_open * 100` where both are non-null and `market_open > 0`
- `pctNewHighAfter11am`: count of entries where `high_time` parses to `hour >= 11` (EST), divided by total count * 100. Entries where `high_time` is null or unparseable are skipped.
- `pctClosedBelowVwap`: count of entries where `closed_over_vwap === false`, divided by total * 100
- `pctClosedBelowOpen`: count of entries where both `market_close` and `market_open` are present and `market_close < market_open`, divided by total * 100

**Edge cases:**
- If a divisor is 0 for any average: display 0.0%, do not crash.
- If `rawEntries` has entries but all `market_open` fields are null: Avg Open→High and Avg Open→Low display as "0.0%".

**Skeleton:**
```
h-6 w-36 bg-[#2a3447] rounded mb-4 animate-pulse
{repeat 8x: h-4 w-full bg-[#2a3447] rounded mb-2 animate-pulse}
```

---

### 4.9 ChartAnalysisBadge (New)

**Purpose:** Small inline badge rendered inside the Header showing the AI chart analysis history rating.

**Visibility:** Renders nothing when `analysis` is null or `analysis.rating` is absent/unrecognized.

**Placement:** Inside the Header component, on Row 1, between the ticker `<h1>` and the Risk badge.

**Size:** `text-xs font-bold px-2.5 py-1 rounded-[5px]`

**HISTORY_MAP:**

| `rating` value | Badge label | Background color |
|---|---|---|
| `"green"` | "HISTORY: Strong" | `#2F7D57` (risk-low dark) |
| `"yellow"` | "HISTORY: Semi-Strong" | `#B9A816` (gold) |
| `"orange"` | "HISTORY: Mixed" | `#B96A16` (risk-medium dark) |
| `"red"` | "HISTORY: Fader" | `#A93232` (risk-high dark) |
| any other | (hidden) | — |

**Text color:** `text-white` on all backgrounds.

---

### 4.10 Offerings (New)

**Purpose:** Displays the three most recent capital offerings with in-the-money price highlighting.

**Visibility:** Hidden entirely when `entries` is null or empty.

**Container:** `bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5`

**Heading:** `text-lg font-bold text-[#a78bfa] mb-3` — "Recent Offerings"

**Per-offering card:** `border border-[#2a3447] rounded-[5px] px-3 py-2 mb-2 bg-[rgba(10,14,22,0.4)]`

**Offering item layout (two lines):**

```
Line 1: {headline text}     →  text-sm text-[#eef1f8] mb-1
Line 2: [data fields]       →  text-sm font-[JetBrains_Mono] flex gap-1 items-center
```

**ATM offering (when `isAtmUsed === true`):**
- Line 1: headline text
- Line 2: `${offeringAmount formatted as $X.XXM}` in `text-[#5ce08a]` + ` | ` separator in `text-[#9aa7c7]` + `{filedAt[:10]}` in `text-[#9aa7c7]`

**Regular offering (when `isAtmUsed === false`):**
- Line 1: headline text
- Line 2 fields (colored together by in-the-money rule):
  - `Amt: {sharesAmount formatted}` (if present)
  - `| ${sharePrice:.2f}` (if present)
  - `| Wrrnts: {warrantsAmount formatted}` (if present)
  - `| {filedAt[:10]}` in `text-[#9aa7c7]` (date always muted, not in-the-money colored)

**In-the-money color rule for regular offerings:**
- `sharePrice <= stockPrice` AND both > 0: amount/price/warrants fields colored `text-[#5ce08a]`
- `sharePrice > stockPrice` OR `stockPrice` is null/0 OR `sharePrice` is null: colored `text-[#f7b731]`

**Skeleton:**
```
h-6 w-40 bg-[#2a3447] rounded mb-4 animate-pulse
{repeat 3x: h-14 w-full bg-[#2a3447] rounded mb-2 animate-pulse}
```

---

### 4.11 JMT415Notes — No Changes

**Purpose:** Scrollable analyst notes grouped by date.

**No structural changes from V1.** Existing component is used as-is. Max height `max-h-96` with internal scroll.

---

### 4.12 MgmtCommentary (New)

**Purpose:** Displays management commentary text from the dilution-rating response.

**Visibility:** Hidden entirely when `text` is null or empty string.

**Container:** `bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5`

**Heading:** `text-lg font-bold text-[#a78bfa] mb-3` — "Mgmt Commentary"

**Body:** `<p className="text-sm text-[#eef1f8] leading-relaxed whitespace-pre-line">{text}</p>`

No skeleton is needed for this component — it is conditionally rendered only when data exists.

---

### 4.13 Ownership (New)

**Purpose:** Displays insider and institutional ownership from the latest reported filing.

**Visibility:** Hidden entirely when `data` is null or `data.owners` is empty.

**Container:** `bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5`

**Heading:** `text-lg font-bold text-[#a78bfa] mb-1` — "Ownership"

**Reported date sub-heading:** `text-xs text-[#9aa7c7] mb-3 font-[JetBrains_Mono]` — `"As of {reportedDate[:10]}"`

**Table layout:**

```
┌─────────────────────────────────────────────────────┐
│  Owner              │  Title           │  Shares    │
│─────────────────────────────────────────────────────│
│  {owner_name}       │  {title}         │  {shares}  │
│  {owner_name}       │  {title}         │  {shares}  │
└─────────────────────────────────────────────────────┘
```

**Table container:** `w-full`

**Header row:** `text-xs text-[#9aa7c7] uppercase tracking-wide border-b border-[#2a3447] pb-1 mb-1`
- Columns: Owner | Title | Shares

**Data row:** `text-sm text-[#eef1f8] border-b border-[#2a3447] py-1.5` (last row no border)
- Owner cell: `font-medium`
- Title cell: `text-[#9aa7c7]`
- Shares cell: `text-[#5ce08a] font-bold font-[JetBrains_Mono] text-right` — formatted with comma separators (e.g., `1,234,567`)

**Skeleton:**
```
h-6 w-36 bg-[#2a3447] rounded mb-3 animate-pulse
h-4 w-full bg-[#2a3447] rounded mb-2 animate-pulse   (header row skeleton)
{repeat 4x: h-8 w-full bg-[#2a3447] rounded mb-1 animate-pulse}
```

---

### 4.14 TickerSearch — No Changes

**Purpose:** Text input for manual ticker lookup.

**No structural changes from V1.** Existing component is used as-is. Already auto-uppercases input. Existing styling matches the design system.

---

## 5. Color Reference

### 5.1 Risk Badge Background Colors

| Level | Hex | Usage |
|-------|-----|-------|
| High | `#A93232` | Header risk badge, RiskBadges row, GainerRow risk badge |
| Medium | `#B96A16` | Same |
| Low | `#2F7D57` | Same |
| N/A | `#4A525C` | Same; also used when no data |

Text: `text-white` on all risk badge backgrounds.

### 5.2 Data Colors

| Token | Hex | Usage |
|-------|-----|-------|
| Positive / in-the-money / green | `#5ce08a` | Avg Open→High, in-the-money prices, ownership shares, ATM amount |
| Negative / risk / red | `#ff6b6b` | Avg Open→Low, risk indicators, expired/$0 capacity |
| Caution / orange | `#f7b731` | Out-of-money prices, medium-risk gap stats |
| Heading purple | `#a78bfa` | All card headings, ticker in header |
| Cyan (gainer ticker) | `#63D3FF` | Ticker symbol in GainerRow only |
| Pink accent | `#ff4fa6` | Search button background, refresh button text, focused borders |
| Text primary | `#eef1f8` | Body text, offering headlines, item details |
| Text muted | `#9aa7c7` | Metadata, separators, timestamps, table sub-headings |

### 5.3 Background Colors

| Token | Hex | Tailwind class | Usage |
|-------|-----|----------------|-------|
| Page background | `#0e111a` | `bg-[#0e111a]` | App root, both panels |
| Card background | `#1b2230` | `bg-bg-card` | All panel cards |
| Card hover | `#222b3a` | `bg-bg-card-hover` | Selected gainer row |
| Input background | `#0f1622` | `bg-bg-input` | Search input |
| Border | `#2a3447` | `border-[#2a3447]` or `border-border-card` | All card borders, row dividers |

---

## 6. Right Panel Render Order

This is the canonical vertical stacking order for the right panel when data is loaded. This order matches the `_show_data` function in `das_monitor.py`.

| Position | Component | Condition to render |
|----------|-----------|---------------------|
| 1 | **Header** | Always (shows skeleton when loading) |
| 2 | **Headlines** (Feed) | Always (shows skeleton when loading; empty state if no news) |
| 3 | **RiskBadges** | Always (shows skeleton when loading) |
| 4 | **OfferingAbility** | Only when `offeringAbilityDesc` is non-null and non-empty |
| 5 | **InPlayDilution** | Always (shows skeleton when loading; empty-state message if no warrants or convertibles) |
| 6 | **Offerings** (Recent Offerings) | Only when `offerings` array is non-empty |
| 7 | **GapStats** | Only when `gapStats` array is non-empty |
| 8 | **JMT415Notes** | Always (shows skeleton when loading; "No notes available." if empty) |
| 9 | **MgmtCommentary** | Only when `mgmtCommentary` is non-null and non-empty |
| 10 | **Ownership** | Only when `ownership` is non-null and `ownership.owners` is non-empty |

---

## 7. Interaction Patterns

### 7.1 Gainer Row Click

**Trigger:** User clicks anywhere on a `GainerRow` element.
**Component that handles it:** `GainerRow` fires `onClick(ticker)` → `TopGainersSidebar.onGainerSelect(ticker)` → `page.tsx`.
**Behavior:**
1. `page.tsx` sets `sidebarSelectedTicker = ticker` — sidebar re-renders with selected highlight on clicked row.
2. `page.tsx` sets `selectedTicker = ticker`, `dilutionData = null`, `isLoading = true`.
3. If a prior fetch is in flight: `AbortController.abort()` is called on the prior controller.
4. New fetch: `fetchDilution(ticker, signal)`.
5. On success: `dilutionData = data`, `isLoading = false`.
6. On abort (superseded): result is discarded; no state update.
7. On error: `error = { status, message }`, `isLoading = false`.

**Loading state:** All right-panel cards show their `animate-pulse` skeleton variants.
**Error state:** Right panel shows a single error card with the appropriate message.
**Success state:** Right panel renders all 10 panel positions per Section 6 render order.

---

### 7.2 Ticker Search Submit

**Trigger:** User presses Enter in the TickerSearch input or clicks the "Search" button.
**Component that handles it:** `TickerSearch.onSearch(ticker)` → `page.tsx`.
**Behavior:**
1. If trimmed input is empty: no action.
2. `page.tsx` sets `sidebarSelectedTicker = null` — clears sidebar highlight.
3. Sets `selectedTicker = ticker`, `dilutionData = null`, `isLoading = true`.
4. Same abort + fetch pattern as gainer click.

**Loading state:** Same skeleton pattern.
**Error state:** Same error card pattern.

---

### 7.3 Sidebar Auto-Refresh (60 Seconds)

**Trigger:** 60-second `setInterval` fires inside `TopGainersSidebar`.
**Component that handles it:** `TopGainersSidebar` internal timer.
**Behavior:**
1. `isLoading = true` — sidebar header shows "Loading..." in place of count badge.
2. Fetch `GET /api/v1/gainers`.
3. On success: `gainers = data`, `isLoading = false`, `lastUpdated = now`. Count badge shows new count.
4. Previously selected row retains highlight if its ticker still appears in the new list.
5. If the selected ticker is no longer in the new gainers list: the highlight is cleared (the gainer left the 15% threshold).

**Loading state:** Sidebar header shows "Loading..." text indicator; existing rows remain visible during refresh (not replaced with skeletons) — this prevents jarring full sidebar blank-outs.
**Error state:** Sidebar header shows a small error indicator; previously loaded rows remain visible.

---

### 7.4 Manual Refresh Button Click

**Trigger:** User clicks the refresh (↻) button in the sidebar header.
**Component that handles it:** `TopGainersSidebar`.
**Behavior:**
1. Current interval timer is cleared.
2. Immediate fetch begins (same as auto-refresh behavior above).
3. New 60-second interval starts after fetch completes.

---

### 7.5 Superseded Load Handling

**Trigger:** User clicks a second gainer row while the first ticker's data is still loading.
**Behavior:**
1. `page.tsx` calls `abortController.abort()` on the in-flight request.
2. The sidebar highlight immediately moves to the second row.
3. The first ticker's response, if it arrives after abort, is discarded.
4. Second ticker's load proceeds normally.

---

## 8. Component Hierarchy

```
page.tsx (DashboardPage)
├── [left panel wrapper: w-[260px] shrink-0]
│   └── TopGainersSidebar
│       ├── [sidebar header: title + count + refresh button + loading indicator]
│       └── [scrollable list]
│           └── GainerRow (×n)
│               └── [risk badge inline]
│               └── [news badge inline]
└── [right panel wrapper: flex-1 overflow-y-auto]
    ├── [idle state: centered prompt]  — OR —
    ├── [error state: ErrorCard]       — OR —
    └── [loaded / loading state: panel stack]
        ├── Header
        │   └── ChartAnalysisBadge (inline, inside Header)
        ├── Headlines
        ├── RiskBadges
        ├── OfferingAbility (conditional)
        ├── InPlayDilution
        │   ├── [WARRANTS subsection]
        │   └── [CONVERTIBLES subsection] (conditional)
        ├── Offerings (conditional)
        ├── GapStats (conditional)
        ├── JMT415Notes
        ├── MgmtCommentary (conditional)
        └── Ownership (conditional)
```

---

## 9. Loading States

Every component that fetches data must render a skeleton placeholder while `data` is null (the `isLoading` state in `page.tsx`). Skeletons use `animate-pulse` with `bg-[#2a3447]` blocks.

| Component | Skeleton pattern |
|-----------|-----------------|
| Header | 3 skeleton blocks (ticker area, price, metadata row) |
| Headlines | 3 rows: badge rect + timestamp rect + full-width text rect |
| RiskBadges | 6 badge stubs: label rect + badge rect |
| OfferingAbility | 4 text-line rects of varying widths |
| InPlayDilution | 1 heading rect + 1 subsection label rect + 2 item card rects |
| Offerings | 1 heading rect + 3 offering card rects |
| GapStats | 1 heading rect + 8 label-value row rects |
| JMT415Notes | 1 heading rect + 2 grouped note blocks |
| Ownership | 1 heading rect + 1 table header rect + 4 row rects |
| MgmtCommentary | No skeleton — component only renders when data exists |
| GainerRow (sidebar) | 5 placeholder rows: `h-14 bg-[#1b2230] rounded-[5px] animate-pulse mx-2 my-1` |

All right-panel skeletons are contained inside cards with the same `bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5` wrapper to preserve layout structure during load.

---

## 10. Error States

### 10.1 Right Panel Errors

A single `ErrorCard` component occupies the top of the right panel content area. All other panel slots are not rendered.

**ErrorCard layout:**
```
bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5
├── [!] icon (text-[#ff6b6b])
├── Error message (text-sm text-[#ff6b6b])
└── Retry button (text-[#ff4fa6] text-sm hover:underline cursor-pointer)
```

**Error messages by HTTP status:**

| Status | Display message |
|--------|----------------|
| 404 | "No dilution data available for {TICKER}." |
| 429 | "Rate limit exceeded. Try again later." |
| 500 / timeout / network | "API error. Please retry." |

The Retry button re-fires the same `fetchDilution(selectedTicker)` call.

### 10.2 Sidebar Errors

When `GET /api/v1/gainers` fails during a refresh, previously loaded rows are retained — the last-known-good gainer list remains visible so traders are not left with a blank sidebar during a transient network failure. A subtle error indicator is overlaid in the sidebar header:

```
text-[#ff6b6b] text-xs ml-2 (inline next to the title or count badge)
"Refresh failed"
```

The full error state (rows replaced by an error message + Retry button) only applies when the initial load fails (i.e., there are no previously loaded rows to retain):
```
text-[#ff6b6b] text-xs text-center py-4
"Could not load gainers."
[Retry] — text-[#ff4fa6] text-xs underline cursor-pointer
```

### 10.3 Per-Panel Graceful Degradation

When a specific sub-field is null/empty (due to backend graceful degradation per AC-18), the conditional panels (Offerings, GapStats, Ownership, OfferingAbility, MgmtCommentary) are simply not rendered. No error indicator is shown for individual panel absences — this is expected behavior when AskEdgar returns no data for those fields.

---

## 11. State Visibility

| State field | Where it is visible | Who updates it |
|-------------|---------------------|----------------|
| `selectedTicker` | Right panel heading area (via Header component); TickerSearch input reflects it implicitly | `page.tsx` on gainer click or search submit |
| `sidebarSelectedTicker` | GainerRow `isSelected` prop drives the highlight style | `page.tsx` on gainer click (set); search submit (cleared) |
| `dilutionData` | All right-panel components consume slices of this | `page.tsx` on fetch success |
| `isLoading` (right panel) | All right-panel components: show skeleton when null/loading | `page.tsx` |
| `error` | ErrorCard in right panel | `page.tsx` on fetch failure |
| `gainers[]` (sidebar) | GainerRow list in TopGainersSidebar | `TopGainersSidebar` internal state |
| `isLoading` (sidebar) | Sidebar header "Loading..." indicator; skeleton rows on initial load | `TopGainersSidebar` internal state |
| `error` (sidebar) | Sidebar error state | `TopGainersSidebar` internal state |
| `stockPrice` | Header row 2; InPlayDilution (for in-the-money logic, not displayed directly); Offerings (same) | Carried inside `dilutionData` |
| `chartAnalysis` | ChartAnalysisBadge inside Header | Carried inside `dilutionData` |

---

## 12. Number Formatting Reference

These formatting rules apply consistently across all components.

| Value type | Format | Examples |
|-----------|--------|---------|
| Price >= $1 | `$` + `.toFixed(2)` | $1.24, $12.50, $120.00 |
| Price < $1 | `$` + `.toFixed(4)` | $0.0034, $0.1200 |
| Millions/billions (float, mcap, offering amount) | Divide by 1,000,000 → `{n:.2f}M`; if >= 1000M → `{n/1000:.2f}B` | 917K, 12.6M, 1.23B |
| Volume | Same M/K suffix format | 2.3M, 845K |
| Share count (Ownership) | Comma-separated integer | 1,234,567 |
| Percentage | `.toFixed(1)` for averages; `.toFixed(0)` for traffic-light stats | +23.4%, 67% |

"K" suffix threshold: values >= 1,000 and < 1,000,000 display as `{n/1000:.1f}K`.

---

## 13. Typography Reference

| Element | Font | Weight | Size |
|---------|------|--------|------|
| Card headings | Space Grotesk | Bold (`font-bold`) | `text-lg` (18px) |
| Ticker in Header | Space Grotesk | Bold | `text-3xl` (30px) |
| Ticker in GainerRow | JetBrains Mono | Bold | `text-sm` (14px) |
| Body text, descriptions | Space Grotesk | Normal | `text-sm` (14px) |
| Data values, prices, timestamps | JetBrains Mono | Bold for values, normal for timestamps | `text-sm` (14px) |
| Metadata / muted text | Space Grotesk | Normal | `text-sm` (14px) or `text-xs` (12px) |
| Badge labels | JetBrains Mono or Space Grotesk | Bold | `text-xs` (12px) or `text-[10px]` |

JetBrains Mono Tailwind class: `font-[JetBrains_Mono,ui-monospace,monospace]`

---

## 14. Accessibility Notes (Functional, Not Aesthetic)

- All interactive elements (GainerRow, refresh button, search button, retry button) must have `cursor-pointer` class.
- GainerRow click targets must cover the entire row surface — achieved by binding click on the row wrapper, not only the ticker text.
- The search input already has `disabled` prop wired to `isLoading` in the existing `TickerSearch` component — no change needed.
- Skeleton elements carry `animate-pulse` for visual indication; no content ARIA roles needed per scope (desktop tool, not accessibility-targeted).

---

## Appendix A: Sector Abbreviation Map

```typescript
const SECTOR_SHORT: Record<string, string> = {
  "Healthcare":             "Health",
  "Technology":             "Tech",
  "Industrials":            "Indust",
  "Consumer Cyclical":      "Cons Cyc",
  "Consumer Defensive":     "Cons Def",
  "Communication Services": "Comms",
  "Financial Services":     "Financ",
  "Basic Materials":        "Materials",
  "Real Estate":            "RE",
};
// Fallback: full sector name
```

---

## Appendix B: Chart Analysis HISTORY_MAP

```typescript
const HISTORY_MAP: Record<string, { label: string; bg: string }> = {
  green:  { label: "HISTORY: Strong",      bg: "#2F7D57" },
  yellow: { label: "HISTORY: Semi-Strong", bg: "#B9A816" },
  orange: { label: "HISTORY: Mixed",       bg: "#B96A16" },
  red:    { label: "HISTORY: Fader",       bg: "#A93232" },
};
// Any other rating value: render nothing
```
