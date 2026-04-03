# Gap Lens Dilution V2 — Intake Document

## Overview

Upgrade the Gap Lens Dilution web app to match feature parity with the AskEdgar Dilution Monitor V2 desktop app. The reference implementation is a single-file tkinter desktop app (`das_monitor.py`) located at `/home/d-tuned/projects/ask-edgar-repo/`. We are building a web app equivalent — no DAS/thinkorswim window scraping.

## Project Location

- **Web app (this project):** `/home/d-tuned/projects/gap-lens-dilution/`
  - Backend: `app/` (FastAPI + httpx)
  - Frontend: `frontend/` (Next.js + TypeScript + Tailwind)
- **V2 reference:** `/home/d-tuned/projects/ask-edgar-repo/das_monitor.py`
- **Original screenshot reference:** `specs/AskEdgar Dilution App.png`

## What Already Exists (V1)

### Backend (FastAPI) — Working
- **Single endpoint:** `GET /api/v1/dilution/{ticker}`
- **Service layer:** `app/services/dilution.py` — makes 5 concurrent calls to AskEdgar:
  1. `/v1/dilution-rating` — risk ratings, cash data, offering ability desc
  2. `/v1/float-outstanding` — float, OS, market cap, sector, country
  3. `/v1/news` — headlines, 8-K/6-K filings, grok summaries, JMT415 notes
  4. `/v1/registrations` — shelf, ATM, equity line, S-1
  5. `/v1/dilution-data` — warrants and convertibles
- **Retry logic:** 3 retries with exponential backoff
- **Error handling:** TickerNotFoundError, RateLimitError, ExternalAPIError
- **Config:** `.env` with `ASKEDGAR_API_KEY`, `ASKEDGAR_URL=https://eapi.askedgar.io`

### Frontend (Next.js) — Static Placeholder Data
Components built but wired to placeholder data only (no API calls):
- `Header.tsx` — ticker, risk badge, stats row
- `Headlines.tsx` — color-coded filing badges with timestamps
- `RiskBadges.tsx` — horizontal row of Low/Medium/High badges
- `OfferingAbility.tsx` — text list with red items for concerning fields
- `InPlayDilution.tsx` — warrant details (remaining, strike, filed)
- `JMT415Notes.tsx` — scrollable date-grouped text entries
- `TickerSearch.tsx` — input with search button
- Types: `frontend/src/types/dilution.ts`
- Design system: Gap Research dark theme (navy bg, pink accent, Space Grotesk font)

---

## V2 Scope — What Needs to Be Built

### New AskEdgar API Endpoints (5 new)

All use the same API key. Base URL: `https://eapi.askedgar.io`

#### 1. Gap Statistics
```
GET /v1/gap-stats?ticker={ticker}&page=1&limit=100
```
Returns list of historical gap-up entries with:
- `date`, `gap_percentage`, `market_open`, `high_price`, `low_price`, `market_close`
- `high_time` (ISO, EST timezone)
- `closed_over_vwap` (boolean)
- `volume`

**UI computes and displays:**
- Last Gap Date
- Number of Gaps
- Avg Gap %
- Avg Open→High (green)
- Avg Open→Low (red)
- % New High After 11am — color coded: >=45% green, >=21% orange, else red
- % Closed Below VWAP — color coded: <=59% green, <=84% orange, else red
- % Closed Below Open — color coded: <=50% green, <=74% orange, else red

#### 2. Recent Offerings
```
GET /v1/offerings?ticker={ticker}&limit=5
```
Returns list of offerings with:
- `headline` — offering title (check for "ATM USED" in headline)
- `offering_amount` — dollar amount
- `share_price` — price per share
- `shares_amount` — number of shares
- `warrants_amount` — warrants included
- `filed_at` — filing date

**UI displays:** Up to 3 most recent offerings. ATM offerings show amount + date. Regular offerings show amount, price, warrants, date. Price highlight: green if share_price <= current stock price (in the money), orange otherwise.

#### 3. Ownership
```
GET /v1/ownership?ticker={ticker}&limit=100
```
Returns ownership groups by reported date. Use first result (latest). Each has:
- `reported_date`
- `owners[]` — array of:
  - `owner_name`
  - `title` or `owner_type`
  - `common_shares_amount`
  - `document_url`

**UI displays:** Table with columns: Owner | Title | Shares. Header shows reported date. Shares formatted with commas, colored green.

#### 4. AI Chart Analysis
```
GET /v1/ai-chart-analysis?ticker={ticker}&limit=1
```
Returns chart analysis with:
- `rating` — one of: "green", "yellow", "orange", "red"

**UI displays:** Badge in header area. Maps to labels:
- green → "Strong" (green badge)
- yellow → "Semi-Strong" (yellow badge)
- orange → "Mixed" (orange badge)
- red → "Fader" (red badge)

#### 5. Top Gainers (TradingView Scanner — no API key)
```
POST https://scanner.tradingview.com/america/scan
```
Request body:
```json
{
  "markets": ["america"],
  "symbols": {"query": {"types": ["stock"]}, "tickers": []},
  "options": {"lang": "en"},
  "columns": ["name", "close", "premarket_change", "premarket_change_abs",
               "premarket_close", "premarket_volume", "volume", "market_cap_basic"],
  "sort": {"sortBy": "premarket_change", "sortOrder": "desc"},
  "range": [0, 30]
}
```
**Filters:** Only tickers matching `^[A-Z]{2,4}$`, change >= 15%.

**Enrichment per gainer (parallel):** Fetch float, dilution rating, and chart analysis from AskEdgar. Check news endpoint for filings today.

**UI displays:** Left sidebar panel with rows per gainer:
- Top line: Ticker (cyan) | Risk badge | Change % (green/red)
- Middle: Price | Volume
- Bottom: Float | MCap | Sector | Country
- Click a gainer → loads full dilution detail in the right panel

**Refresh:** Every 60 seconds.

### New Backend Features

#### API Response Caching
- 30-minute TTL for all endpoints EXCEPT news (news is always live)
- Cache key format: `"{endpoint}:{ticker}"`
- Don't cache None/error responses

#### Updated Dilution Endpoint Response
The main `/api/v1/dilution/{ticker}` endpoint should add:
- `gapStats[]` — raw gap stats data
- `offerings[]` — recent offerings (up to 5)
- `ownership` — latest ownership group
- `chartAnalysis` — chart rating
- `stockPrice` — current price from screener
- `mgmtCommentary` — management commentary text

#### New Endpoint: Top Gainers
```
GET /api/v1/gainers
```
Returns enriched top gainers list. Refresh logic can be server-side with 60s cache.

### Frontend Changes

#### Two-Panel Layout
- **Left panel** (~260px): Top Gainers list with search at top
- **Right panel** (flex): Full dilution detail for selected ticker
- Click gainer in left panel → populates right panel
- Or type ticker in search → populates right panel

#### New Components Needed
1. **TopGainersSidebar.tsx** — scrollable list of gainer rows
2. **GainerRow.tsx** — single gainer with ticker, risk, change%, price, volume, float info
3. **GapStats.tsx** — computed statistics table with color-coded values
4. **Offerings.tsx** — recent offerings with ATM detection and in-the-money highlighting
5. **Ownership.tsx** — owner table with reported date header
6. **ChartAnalysisBadge.tsx** — small badge showing history rating
7. **MgmtCommentary.tsx** — text card for management commentary

#### Updated Components
- **Header.tsx** — add ChartAnalysisBadge, add stock price display
- **InPlayDilution.tsx** — add convertibles section, add in-the-money color logic (green if strike <= stock price, orange otherwise)
- **OfferingAbility.tsx** — parse offering_ability_desc for shelf capacity, ATM capacity, S-1/F-1 status with red highlighting for pending registrations

#### API Service Layer
- `frontend/src/services/api.ts` — fetch from backend endpoints
- Loading skeletons already exist on all components (show when data is null)
- Error handling: show error messages for 404, 429, 500

---

## Visual Design System

Already applied from Gap Research project (`/home/d-tuned/Gap Research/app/static/styles.css`):

```
Background:     #0e111a (primary), #141a24 (alt), #1b2230 (cards)
Borders:        #2a3447
Text:           #eef1f8 (primary), #9aa7c7 (muted)
Accent:         #ff4fa6 (pink — buttons, links)
Risk Low:       #36d29a (green)
Risk Medium:    #f7b731 (yellow/orange)
Risk High:      #ff6b6b (red)
Positive:       #5ce08a (green — in the money, gains)
Negative:       #ff6b6b (red — losses, risk)
Headings:       #a78bfa (purple)
Fonts:          Space Grotesk (UI), JetBrains Mono (data/timestamps)
Border radius:  9px (cards), 5px (inner elements)
```

V2 reference desktop app uses a slightly different palette (darker `#0D1014` bg, cyan `#63D3FF` accent) but we are keeping the Gap Research design system for brand consistency across the platform.

---

## V2 Reference: Color-Coding Rules

### Risk Badges
- High → red `#A93232`
- Medium → orange `#B96A16`
- Low → green `#2F7D57`
- N/A → gray `#4A525C`

### Filing Type Badges
- 6-K / 8-K → orange stripe
- NEWS → cyan stripe
- GROK → purple stripe
- JMT415 → default gray

### Gap Stats Color Coding
| Metric | Green | Orange | Red |
|--------|-------|--------|-----|
| % Closed Below VWAP | <=59% | 60-84% | >=85% |
| % Closed Below Open | <=50% | 51-74% | >=75% |
| % New High After 11am | >=45% | 21-44% | <=20% |
| Avg Open→High | always green | — | — |
| Avg Open→Low | — | — | always red |

### In-Play Dilution
- Strike/conversion price <= stock price → green (in the money)
- Strike/conversion price > stock price → orange

### Offerings
- ATM offerings: show amount in green
- Regular: share_price <= stock_price → green, otherwise orange

---

## Out of Scope

- DAS Trader / thinkorswim window title scraping (desktop-only feature)
- `yfinance` real-time price enrichment for gainers (use TradingView data directly, or add as a follow-up)
- `massive_backup.py` (Polygon/Massive API alternative — reference only)
- Mobile responsive design (desktop-first for now)

---

## API Configuration

All AskEdgar endpoints use the same key:
```
ASKEDGAR_URL=https://eapi.askedgar.io
ASKEDGAR_API_KEY=<key in .env>
```

Enterprise endpoints use `/enterprise/v1/` prefix. Standard endpoints use `/v1/` prefix.

| Endpoint | Path Prefix |
|----------|-------------|
| dilution-rating | `/enterprise/v1/` |
| float-outstanding | `/enterprise/v1/` |
| news | `/enterprise/v1/` |
| dilution-data | `/enterprise/v1/` |
| screener | `/enterprise/v1/` |
| gap-stats | `/v1/` |
| offerings | `/v1/` |
| ownership | `/v1/` |
| ai-chart-analysis | `/v1/` |

**Rate limit:** 50 unique tickers/day per endpoint.

---

## File Map

### Backend
- `app/main.py` — FastAPI app factory, CORS, static files
- `app/api/v1/routes.py` — API route handlers
- `app/services/dilution.py` — AskEdgar API client (needs V2 updates)
- `app/core/config.py` — pydantic settings from .env
- `app/utils/validation.py` — ticker validation
- `app/utils/formatting.py` — number formatting
- `app/utils/errors.py` — custom exceptions

### Frontend
- `frontend/src/app/page.tsx` — main page (currently placeholder data)
- `frontend/src/app/layout.tsx` — root layout with fonts
- `frontend/src/app/globals.css` — design system tokens
- `frontend/src/components/` — all UI components
- `frontend/src/types/dilution.ts` — TypeScript interfaces

### Reference
- `/home/d-tuned/projects/ask-edgar-repo/das_monitor.py` — V2 reference (1610 lines)
