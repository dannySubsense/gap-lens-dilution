# Architecture: v2-dilution-dashboard

**Version:** 2.0
**Date:** 2026-04-03
**Status:** Draft
**Author:** @architect

---

## Overview

This document specifies the technical architecture for upgrading the Gap Lens Dilution web app to V2 feature parity. The design extends the existing FastAPI backend and Next.js frontend — it does not replace them. Every new component, schema, and service function is anchored to the existing code patterns observed in `dilution.py`, `routes.py`, and the frontend components.

---

## Pre-Architecture Note: Endpoint Prefix Discrepancy

The existing `app/services/dilution.py` calls AskEdgar using a `/v1/` prefix for all endpoints (e.g., `/v1/dilution-rating`, `/v1/float-outstanding`). The INTAKE.md and `das_monitor.py` reference implementation both confirm these should be `/enterprise/v1/` for the enterprise tier. The new service methods in this architecture use the correct prefixes as specified in the INTAKE endpoint table. The existing service methods must be corrected as part of V2 implementation (not deferred — incorrect prefixes will cause 404s at runtime).

**Correct prefix table (source: INTAKE.md):**

| Endpoint | Path Prefix |
|---|---|
| dilution-rating | `/enterprise/v1/` |
| float-outstanding | `/enterprise/v1/` |
| news | `/enterprise/v1/` |
| dilution-data | `/enterprise/v1/` |
| screener | `/enterprise/v1/` |
| gap-stats | `/v1/` |
| offerings | `/v1/` |
| ownership | `/v1/` |
| ai-chart-analysis | `/v1/` |

---

## 1. System Architecture Diagram

```
Browser (Next.js)
    │
    ├── TopGainersSidebar ──→ GET /api/v1/gainers (60s poll)
    │
    └── Right Panel ────────→ GET /api/v1/dilution/{ticker}
                                    │
                                    ▼
                             FastAPI Backend
                                    │
                          ┌─────────┴──────────┐
                          │   In-Memory Cache   │
                          │  dict[str, Entry]   │
                          │  TTL = 30 min       │
                          │  news = never       │
                          └─────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────────┐
                    │               │                   │
             AskEdgar Enterprise   AskEdgar Standard   TradingView
             /enterprise/v1/       /v1/                 scanner POST
```

---

## 2. Components

### 2.1 Backend Components

| Component | Responsibility | Location |
|---|---|---|
| `DilutionService` | Makes all AskEdgar API calls with retry logic; owns the cache dict | `app/services/dilution.py` |
| `CacheStore` | In-memory TTL cache; new inner class or module-level dict within `dilution.py` | `app/services/dilution.py` |
| `GainersService` | Calls TradingView scanner; enriches each gainer in parallel via `DilutionService` | `app/services/gainers.py` (new file) |
| `DilutionRouter` | HTTP route handlers; maps exceptions to HTTP status codes | `app/api/v1/routes.py` |

### 2.2 Frontend Components

| Component | Status | Responsibility | Location |
|---|---|---|---|
| `page.tsx` | Rewrite | Owns `selectedTicker` and `dilutionData` state; renders two-panel layout; wires sidebar click and search submit to API service | `frontend/src/app/page.tsx` |
| `TopGainersSidebar` | New | Fetches gainers on mount and every 60s; renders scrollable list; emits selected ticker upward | `frontend/src/components/TopGainersSidebar.tsx` |
| `GainerRow` | New | Renders one gainer with ticker, risk badge, change %, price, volume, float, mcap, sector, country, news badge, chart rating | `frontend/src/components/GainerRow.tsx` |
| `GapStats` | New | Computes and renders gap statistics table with traffic-light color coding | `frontend/src/components/GapStats.tsx` |
| `Offerings` | New | Renders up to 3 recent offerings with ATM detection and in-the-money price highlight | `frontend/src/components/Offerings.tsx` |
| `Ownership` | New | Renders owner table with reported_date header; hides when empty | `frontend/src/components/Ownership.tsx` |
| `ChartAnalysisBadge` | New | Renders history rating badge using HISTORY_MAP; hides when absent | `frontend/src/components/ChartAnalysisBadge.tsx` |
| `MgmtCommentary` | New | Renders management commentary text card; hides when null or empty | `frontend/src/components/MgmtCommentary.tsx` |
| `Header` | Update | Add `ChartAnalysisBadge` and `stockPrice` display to existing layout | `frontend/src/components/Header.tsx` |
| `InPlayDilution` | Update | Add convertibles subsection with in-the-money color logic | `frontend/src/components/InPlayDilution.tsx` |
| `OfferingAbility` | Update | Replace current boolean flags approach with comma-split segment parser; apply per-segment color rules | `frontend/src/components/OfferingAbility.tsx` |
| `apiService` | New | Centralized module for all backend HTTP calls; typed return values; no raw fetch in components | `frontend/src/services/api.ts` |

---

## 3. Data Schemas

### 3.1 Backend — Python (Pydantic Response Models)

These are the shapes returned by the updated `GET /api/v1/dilution/{ticker}` endpoint.

```python
# app/models/responses.py  (new file)

from pydantic import BaseModel
from typing import Optional

class GapStatEntry(BaseModel):
    date: str
    gap_percentage: Optional[float]
    market_open: Optional[float]
    high_price: Optional[float]
    low_price: Optional[float]
    market_close: Optional[float]
    high_time: Optional[str]       # ISO timestamp, EST
    closed_over_vwap: Optional[bool]
    volume: Optional[int]

class OfferingEntry(BaseModel):
    headline: Optional[str]
    offering_amount: Optional[float]
    share_price: Optional[float]
    shares_amount: Optional[float]
    warrants_amount: Optional[float]
    filed_at: Optional[str]

class OwnerEntry(BaseModel):
    owner_name: Optional[str]
    title: Optional[str]
    common_shares_amount: Optional[int]
    document_url: Optional[str]

class OwnershipGroup(BaseModel):
    reported_date: Optional[str]
    owners: list[OwnerEntry]

class ChartAnalysis(BaseModel):
    rating: Optional[str]          # "green" | "yellow" | "orange" | "red"

class WarrantItem(BaseModel):
    details: Optional[str]
    warrants_exercise_price: Optional[float]
    warrants_remaining: Optional[float]
    warrants_amount: Optional[float]
    filed_at: Optional[str]
    registered: Optional[str]

class ConvertibleItem(BaseModel):
    details: Optional[str]
    conversion_price: Optional[float]
    underlying_shares_remaining: Optional[float]
    filed_at: Optional[str]
    registered: Optional[str]

class DilutionV2Response(BaseModel):
    ticker: str
    # Existing V1 fields
    offeringRisk: Optional[str]
    offeringAbility: Optional[str]
    offeringAbilityDesc: Optional[str]
    dilutionRisk: Optional[str]
    dilutionDesc: Optional[str]
    offeringFrequency: Optional[str]
    cashNeed: Optional[str]
    cashNeedDesc: Optional[str]
    cashRunway: Optional[float]
    cashBurn: Optional[float]
    estimatedCash: Optional[float]
    warrantExercise: Optional[str]
    warrantExerciseDesc: Optional[str]
    float_: Optional[str]           # mapped from "float" (Python reserved word)
    outstanding: Optional[str]
    marketCap: Optional[str]
    industry: Optional[str]
    sector: Optional[str]
    country: Optional[str]
    insiderOwnership: Optional[float]
    institutionalOwnership: Optional[float]
    news: list
    registrations: list
    warrants: list[WarrantItem]
    convertibles: list[ConvertibleItem]
    # New V2 fields
    gapStats: list[GapStatEntry]
    offerings: list[OfferingEntry]
    ownership: Optional[OwnershipGroup]
    chartAnalysis: Optional[ChartAnalysis]
    stockPrice: Optional[float]
    mgmtCommentary: Optional[str]

class GainerEntry(BaseModel):
    ticker: str
    todaysChangePerc: float
    price: float
    volume: float
    float_: Optional[float]        # raw number from float-outstanding
    marketCap: Optional[float]
    sector: Optional[str]
    country: Optional[str]
    risk: Optional[str]            # "High" | "Medium" | "Low" | "N/A"
    chartRating: Optional[str]     # "green" | "yellow" | "orange" | "red"
    newsToday: bool
```

### 3.2 Backend — Cache Entry Type

```python
# Internal to DilutionService / CacheStore (not exposed via API)
# cache: dict[str, tuple[float, Any]]
# key format: "{endpoint_name}:{ticker}"  e.g. "gapstats:EEIQ"
# value: (stored_at_unix_timestamp, data)
# Rule: only store when data is not None and not an error
```

### 3.3 Frontend — TypeScript Interfaces

These extend and replace the existing `frontend/src/types/dilution.ts`.

```typescript
// frontend/src/types/dilution.ts  (full V2 replacement)

export type RiskLevel = "Low" | "Medium" | "High" | "N/A";

export type ChartRating = "green" | "yellow" | "orange" | "red";

// ── Existing types (unchanged) ────────────────────────────────────────────

export interface HeaderData {
  ticker: string;
  float: string;
  outstandingShares: string;
  marketCap: string;
  sector: string;
  country: string;
  overallRisk: RiskLevel;
  // V2 additions
  stockPrice: number | null;
  chartAnalysis: ChartAnalysis | null;
}

export type FilingType =
  | "6-K"
  | "8-K"
  | "S-1"
  | "10-K"
  | "10-Q"
  | "SC 13D"
  | "SC 13G"
  | "GROK"
  | "news"
  | "jmt415";

export interface Headline {
  filingType: FilingType;
  filedAt: string;
  headline: string;
}

export interface RiskAssessment {
  overallRisk: RiskLevel;
  offering: RiskLevel;
  dilution: RiskLevel;
  frequency: RiskLevel;
  cashNeed: RiskLevel;
  warrants: RiskLevel;
}

export interface JMT415Note {
  date: string;
  ticker: string;
  content: string[];
}

// ── V2: OfferingAbility rework ────────────────────────────────────────────

export interface OfferingAbilityData {
  /** Raw description string from AskEdgar, comma-separated segments */
  offeringAbilityDesc: string | null;
}

// ── V2: In-Play Dilution extension ───────────────────────────────────────

export interface WarrantItem {
  details: string;
  issueDate: string;        // formatted from filed_at
  remaining: number;        // warrants_remaining (raw number)
  strikePrice: number;      // warrants_exercise_price
  filedDate: string;        // filed_at YYYY-MM-DD
  registered: string;
  inTheMoney: boolean;      // computed: strikePrice <= stockPrice
}

export interface ConvertibleItem {
  details: string;
  sharesRemaining: number;  // underlying_shares_remaining
  conversionPrice: number;  // conversion_price
  filedDate: string;
  registered: string;
  inTheMoney: boolean;      // computed: conversionPrice <= stockPrice
}

export interface InPlayDilutionData {
  warrants: WarrantItem[];
  convertibles: ConvertibleItem[];
  stockPrice: number | null;
}

// ── V2: New panel types ───────────────────────────────────────────────────

export interface GapStatEntry {
  date: string;
  gap_percentage: number | null;
  market_open: number | null;
  high_price: number | null;
  low_price: number | null;
  market_close: number | null;
  high_time: string | null;
  closed_over_vwap: boolean | null;
  volume: number | null;
}

export interface GapStatsComputed {
  lastGapDate: string | null;
  numGaps: number;
  avgGapPct: number;
  avgOpenToHigh: number;
  avgOpenToLow: number;
  pctNewHighAfter11am: number;
  pctClosedBelowVwap: number;
  pctClosedBelowOpen: number;
}

export interface OfferingEntry {
  headline: string | null;
  offeringAmount: number | null;
  sharePrice: number | null;
  sharesAmount: number | null;
  warrantsAmount: number | null;
  filedAt: string | null;
  isAtmUsed: boolean;       // computed: headline contains "ATM USED" case-insensitive
  inTheMoney: boolean;      // computed: sharePrice <= stockPrice and both > 0
}

export interface OwnerEntry {
  ownerName: string;
  title: string;
  commonSharesAmount: number | null;
  documentUrl: string | null;
}

export interface OwnershipData {
  reportedDate: string;
  owners: OwnerEntry[];
}

export interface ChartAnalysis {
  rating: ChartRating;
  label: string;            // derived: "Strong" | "Semi-Strong" | "Mixed" | "Fader"
  badgeColor: string;       // derived from HISTORY_MAP
}

// ── V2: Gainers ────────────────────────────────────────────────────────────

export interface GainerEntry {
  ticker: string;
  todaysChangePerc: number;
  price: number;
  volume: number;
  float: number | null;
  marketCap: number | null;
  sector: string | null;
  country: string | null;
  risk: RiskLevel | null;
  chartRating: ChartRating | null;
  newsToday: boolean;
}

// ── V2: Full dilution response shape (from backend) ───────────────────────

export interface DilutionResponse {
  ticker: string;
  offeringRisk: string | null;
  offeringAbility: string | null;
  offeringAbilityDesc: string | null;
  dilutionRisk: string | null;
  dilutionDesc: string | null;
  offeringFrequency: string | null;
  cashNeed: string | null;
  cashNeedDesc: string | null;
  cashRunway: number | null;
  cashBurn: number | null;
  estimatedCash: number | null;
  warrantExercise: string | null;
  warrantExerciseDesc: string | null;
  float: string | null;
  outstanding: string | null;
  marketCap: string | null;
  industry: string | null;
  sector: string | null;
  country: string | null;
  insiderOwnership: number | null;
  institutionalOwnership: number | null;
  news: Headline[];
  registrations: unknown[];
  warrants: RawWarrantItem[];
  convertibles: RawConvertibleItem[];
  // V2 additions
  gapStats: GapStatEntry[];
  offerings: OfferingEntry[];
  ownership: OwnershipData | null;
  chartAnalysis: ChartAnalysis | null;
  stockPrice: number | null;
  mgmtCommentary: string | null;
}

// Raw backend shapes before frontend transformation
export interface RawWarrantItem {
  details: string | null;
  warrants_exercise_price: number | null;
  warrants_remaining: number | null;
  warrants_amount: number | null;
  filed_at: string | null;
  registered: string | null;
}

export interface RawConvertibleItem {
  details: string | null;
  conversion_price: number | null;
  underlying_shares_remaining: number | null;
  filed_at: string | null;
  registered: string | null;
}

// ── V2: API service result types ─────────────────────────────────────────

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; status: 404 | 429 | 500; message: string };
```

---

## 4. API Contracts

### 4.1 Backend HTTP Endpoints

```
GET /api/v1/dilution/{ticker}
  Path param: ticker — validated 1-5 uppercase letters
  Response 200: DilutionV2Response (JSON)
  Response 400: { "detail": "Invalid ticker format: ..." }
  Response 404: { "detail": "Ticker not found" }
  Response 429: { "detail": "Rate limit exceeded" }
  Response 500: { "detail": "Internal server error" }
  Behavior: All sub-calls run concurrently via asyncio.gather.
            Any sub-call that returns None/error contributes null/[]
            to the response — it does NOT cause a 500.

GET /api/v1/gainers
  Response 200: list[GainerEntry] (JSON array, always 200 even if empty)
  Response 500: only if an unhandled exception escapes the route handler
  Behavior: Server-side 60-second TTL cache on the full enriched list.
            TradingView POST happens server-side.
            Enrichment calls run in parallel (asyncio.gather per gainer).
```

### 4.2 New Backend Service Methods

```python
# app/services/dilution.py — additions to DilutionService

async def get_gap_stats(self, ticker: str) -> list[dict]:
    """GET /v1/gap-stats?ticker={ticker}&page=1&limit=100
    Cache key: "gapstats:{ticker}". Returns [] on 404 or error."""

async def get_offerings(self, ticker: str) -> list[dict]:
    """GET /v1/offerings?ticker={ticker}&limit=5
    Cache key: "offerings:{ticker}". Returns [] on 404 or error."""

async def get_ownership(self, ticker: str) -> dict | None:
    """GET /v1/ownership?ticker={ticker}&limit=100
    Returns first result (latest reported_date group) or None.
    Cache key: "ownership:{ticker}". Returns None on 404 or error."""

async def get_chart_analysis(self, ticker: str) -> dict | None:
    """GET /v1/ai-chart-analysis?ticker={ticker}&limit=1
    Returns first result dict or None.
    Cache key: "chart:{ticker}". Returns None on 404 or error."""

async def get_screener_price(self, ticker: str) -> float | None:
    """GET /enterprise/v1/screener?ticker={ticker}
    Returns price field from first result or None.
    Cache key: "price:{ticker}". Returns None on 404 or error."""

async def get_dilution_data_v2(self, ticker: str) -> dict:
    """Replaces get_dilution_detail. Returns full V2 response dict.
    Runs ALL sub-calls (including 5 new endpoints) concurrently.
    Maps None sub-results to null/[] per field — never raises.
    For the news sub-call, bypasses cache.
    Warrant and convertible filtering: items where the strike/conversion
    price exceeds 4x the current stock price are excluded before the
    response is assembled (max_price = stock_price * 4, matching
    das_monitor.py line 415). Requires stockPrice to be fetched first."""

# Internal cache interface (module-level on DilutionService class):
# _cache: dict[str, tuple[float, Any]] = {}

def _cache_get(self, key: str) -> Any | None:
    """Return cached value if present and within TTL, else None."""

def _cache_set(self, key: str, value: Any) -> None:
    """Store value in cache with current timestamp.
    Precondition: value is not None and not an error sentinel."""

async def _make_request_cached(
    self, endpoint: str, params: dict, cache_key: str
) -> dict | None:
    """_make_request with cache layer. Returns None instead of raising
    for 404/error (used for optional sub-calls)."""

async def _make_request_list_cached(
    self, endpoint: str, params: dict, cache_key: str
) -> list:
    """_make_request_list with cache layer. Returns [] on error."""
```

### 4.3 New GainersService

```python
# app/services/gainers.py  (new file)

class GainersService:
    TRADINGVIEW_URL = "https://scanner.tradingview.com/america/scan"
    TV_REQUEST_BODY = { ... }  # as specified in INTAKE.md
    MIN_CHANGE_PCT = 15.0
    TICKER_RE = re.compile(r'^[A-Z]{2,4}$')
    CACHE_TTL_SECS = 60        # 60-second server-side TTL for gainers list

    def __init__(self, dilution_service: DilutionService):
        self._dilution_service = dilution_service
        self._cache: dict[str, tuple[float, list]] = {}
        # key: "gainers", value: (timestamp, enriched_list)

    async def get_gainers(self) -> list[dict]:
        """Return enriched gainers list. Served from cache if < 60 seconds old.
        Always returns a list (empty on failure)."""

    async def _fetch_from_tradingview(self) -> list[dict]:
        """POST TradingView scanner. Filter by TICKER_RE and MIN_CHANGE_PCT.
        Returns raw normalized list or [] on any error."""

    async def _enrich_gainer(self, item: dict) -> dict:
        """Fetch float, dilution rating, chart analysis, and news check
        for a single gainer. All four calls run concurrently.
        Partial failures populate missing fields as None/False."""
```

### 4.4 Frontend API Service

```typescript
// frontend/src/services/api.ts

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function fetchDilution(
  ticker: string,
  signal?: AbortSignal
): Promise<ApiResult<DilutionResponse>>;
// GET {BASE_URL}/api/v1/dilution/{ticker}
// Maps 404 → { ok: false, status: 404, message: "No dilution data available for {ticker}" }
// Maps 429 → { ok: false, status: 429, message: "Rate limit exceeded. Try again later." }
// Maps other errors → { ok: false, status: 500, message: "API error. Please retry." }

export async function fetchGainers(
  signal?: AbortSignal
): Promise<ApiResult<GainerEntry[]>>;
// GET {BASE_URL}/api/v1/gainers
// Maps network/5xx errors → { ok: false, status: 500, message: "..." }
// Never throws; components receive typed result
```

### 4.5 Frontend Component Props

```typescript
// TopGainersSidebar
interface TopGainersSidebarProps {
  selectedTicker: string | null;
  onGainerSelect: (ticker: string) => void;
}
// Manages own internal state: gainers[], isLoading, error, lastUpdated
// Starts 60-second interval on mount; clears on unmount

// GainerRow
interface GainerRowProps {
  gainer: GainerEntry;
  isSelected: boolean;
  onClick: (ticker: string) => void;
}

// GapStats
interface GapStatsProps {
  rawEntries: GapStatEntry[];  // empty array = hide panel
}
// All computation (averages, percentages, color mapping) done inside component

// Offerings
interface OfferingsProps {
  entries: OfferingEntry[];    // empty/null = hide panel
  stockPrice: number | null;
}

// Ownership
interface OwnershipProps {
  data: OwnershipData | null;  // null or empty owners = hide panel
}

// ChartAnalysisBadge
interface ChartAnalysisBadgeProps {
  analysis: ChartAnalysis | null;  // null = render nothing
}

// MgmtCommentary
interface MgmtCommentaryProps {
  text: string | null;  // null or "" = render nothing
}

// Header (updated)
interface HeaderProps {
  data: HeaderData | null;  // null = skeleton
}
// HeaderData now includes: stockPrice, chartAnalysis (see schema)

// InPlayDilution (updated)
interface InPlayDilutionProps {
  data: InPlayDilutionData | null;  // null = skeleton
}
// InPlayDilutionData now includes: convertibles[], stockPrice

// OfferingAbility (updated)
interface OfferingAbilityProps {
  offeringAbilityDesc: string | null;  // null/"" = hide
}
// Replaces OfferingAbilityData; component parses the raw desc string internally

// page.tsx — state shape
interface PageState {
  selectedTicker: string | null;     // drives right panel
  sidebarSelectedTicker: string | null;  // tracks sidebar highlight
  dilutionData: DilutionResponse | null;
  isLoading: boolean;
  error: ApiError | null;
}
// ApiError = { status: number; message: string }
```

---

## 5. Data Flow

### 5.1 Gainer Click Flow

```
User clicks GainerRow (ticker = "MNTK")
  → GainerRow.onClick("MNTK")
  → TopGainersSidebar.onGainerSelect("MNTK")  [prop callback]
  → page.tsx: setSelectedTicker("MNTK")
              setSidebarSelectedTicker("MNTK")
              setIsLoading(true)
              setDilutionData(null)             [clears right panel → shows skeletons]
  → page.tsx: calls apiService.fetchDilution("MNTK")
  → backend: GET /api/v1/dilution/MNTK
  → DilutionService.get_dilution_data_v2("MNTK")
      → asyncio.gather(10 sub-calls concurrently)
      → each sub-call checks cache first; fetches live if stale
      → assembles DilutionV2Response
  → page.tsx: setDilutionData(result.data)
              setIsLoading(false)
  → Right panel re-renders with live data; sidebar highlight stays on "MNTK"
```

### 5.2 Superseded Load Handling

When a second gainer is clicked before the first load completes:

- `page.tsx` uses a `useRef<AbortController>` to track the in-flight request.
- On each new ticker selection, the previous `AbortController.abort()` is called before creating a new fetch.
- The `fetchDilution` service function accepts an `AbortSignal` and passes it to `fetch()`.
- If the aborted response arrives, it is discarded (the result check sees `controller.signal.aborted`).

### 5.3 Ticker Search Flow

```
User types "AAPL" in TickerSearch, presses Enter
  → TickerSearch.onSearch("AAPL")
  → page.tsx: setSelectedTicker("AAPL")
              setSidebarSelectedTicker(null)   [clears sidebar highlight]
              setIsLoading(true)
              [same fetch flow as gainer click]
```

### 5.4 Gainers Auto-Refresh

```
TopGainersSidebar mounts
  → immediate fetch: apiService.fetchGainers()
  → setInterval(60_000, fetchGainers)
  → on each cycle: setIsLoading(true) → fetch → setGainers(data) → setIsLoading(false)
  → Manual refresh button: clears interval, calls fetchGainers immediately, restarts interval
  → Unmount: clearInterval
```

---

## 6. Caching Architecture

### 6.1 Backend In-Memory Cache

The cache lives as a class-level dict on `DilutionService` (module singleton in `routes.py`).

```
_cache: dict[str, tuple[float, Any]]
key format: "{endpoint_name}:{ticker_uppercase}"
value: (unix_timestamp_when_stored, response_data)
```

**Cache keys by endpoint:**

| Cache Key | Endpoint | TTL |
|---|---|---|
| `dilution:{ticker}` | `/enterprise/v1/dilution-rating` | 30 min |
| `float:{ticker}` | `/enterprise/v1/float-outstanding` | 30 min |
| `dildata:{ticker}` | `/enterprise/v1/dilution-data` | 30 min |
| `screener:{ticker}` | `/enterprise/v1/screener` | 30 min (price) |
| `gapstats:{ticker}` | `/v1/gap-stats` | 30 min |
| `offerings:{ticker}` | `/v1/offerings` | 30 min |
| `ownership:{ticker}` | `/v1/ownership` | 30 min |
| `chart:{ticker}` | `/v1/ai-chart-analysis` | 30 min |
| `news:{ticker}` | `/enterprise/v1/news` | **Never cached** |
| `gainers` | TradingView scanner + enrichment | 60 seconds (in GainersService) |

**Rules:**
1. On cache hit within TTL: return stored data without any HTTP call.
2. On cache miss or expired entry: call the live endpoint.
3. If live endpoint returns `None` (error, 404, timeout): do not update cache. Next request will retry live.
4. If live endpoint returns valid non-null data: write to cache with `time.time()` as timestamp.

### 6.2 Gainers Cache (GainersService)

Separate from the per-ticker cache. Key is `"gainers"`, TTL is 60 seconds. The full enriched list is stored. Within the 60-second window, `GET /api/v1/gainers` returns the cached list immediately without re-fetching TradingView or re-enriching.

---

## 7. Error Handling

### 7.1 Backend — Per-Endpoint Graceful Degradation

The critical design decision: `get_dilution_data_v2` must never return a 500 due to a sub-call failure on an optional field.

```python
# Pattern for optional sub-calls:
try:
    gap_stats = await self.get_gap_stats(ticker)
except Exception:
    gap_stats = []

# asyncio.gather with return_exceptions=True prevents one failure
# from canceling all concurrent tasks. Each result is checked:
results = await asyncio.gather(
    self._get_dilution_rating(ticker),
    self._get_float(ticker),
    self.get_news(ticker),
    self._get_dilution_data(ticker),
    self.get_gap_stats(ticker),
    self.get_offerings(ticker),
    self.get_ownership(ticker),
    self.get_chart_analysis(ticker),
    self.get_screener_price(ticker),
    return_exceptions=True,
)
# Each result is checked: isinstance(r, Exception) → use fallback value
```

**Exception-to-HTTP mapping** (existing pattern preserved):
- `TickerNotFoundError` → 404 (raised by `_get_dilution_rating`, propagates to route)
- `RateLimitError` → 429
- `ExternalAPIError` → 500
- Optional sub-call exceptions → absorbed; field returns null/[]

### 7.2 Frontend — Component Error Isolation

Each component receives its data slice as a prop. When the `DilutionResponse` is partially populated (e.g., `gapStats = []`, `ownership = null`), each component independently decides to show data or hide itself. The right panel can render partial data without any component crashing.

```
DilutionResponse
  ├── gapStats = []           → GapStats renders nothing (hidden)
  ├── ownership = null        → Ownership renders nothing (hidden)
  ├── chartAnalysis = null    → ChartAnalysisBadge renders nothing
  ├── offerings = []          → Offerings renders nothing (hidden)
  └── warrants/convertibles   → InPlayDilution shows available subsections
```

### 7.3 Frontend — API Service Error Typing

`fetchDilution` and `fetchGainers` never throw. They return `ApiResult<T>` which is either `{ ok: true, data }` or `{ ok: false, status, message }`. Components check `result.ok` before accessing data.

---

## 8. Configuration

### 8.1 Backend Environment Variables

No new variables are required. The existing `.env` configuration is sufficient:

```env
ASKEDGAR_API_KEY=...         # used for all AskEdgar calls
ASKEDGAR_URL=https://eapi.askedgar.io
REQUEST_TIMEOUT=30           # seconds; applies to all HTTP calls
```

The `config.py` `Settings` class already reads these. The TradingView scanner call requires no API key.

### 8.2 Frontend Environment Variables

```env
# frontend/.env.local  (new file, not committed)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

In production, set `NEXT_PUBLIC_API_BASE_URL` to the deployed backend URL. The `apiService` module reads this at module load time with a fallback to `http://localhost:8000`.

---

## 9. Patterns

| Pattern | Usage | Rationale |
|---|---|---|
| `asyncio.gather(return_exceptions=True)` | All concurrent sub-calls in `get_dilution_data_v2` | Prevents one failing sub-call from canceling others; enables per-field fallback |
| Module-level singleton service | `dilution_service = DilutionService()` in routes.py | Existing pattern; cache dict lives on the instance across all requests |
| `ApiResult<T>` discriminated union | All `apiService` return types | Prevents unhandled promise rejections; forces components to handle error state |
| Prop-driven isolation | Each panel component receives its data slice only | Panels can hide/show independently; no shared state between panels |
| `AbortController` for superseded loads | `page.tsx` ticker fetch | Prevents stale data from a slow first request overwriting a fast second request |
| Computation inside component | Gap stats averages, in-the-money checks, offering_ability_desc parsing | Keeps backend thin; frontend has the display context (stockPrice) needed for the calculation |
| `useRef` for interval ID | `TopGainersSidebar` 60s refresh | Stable reference across renders; cleaned up on unmount to prevent memory leaks |

### Anti-Patterns (Do Not Use)

- **Inline `fetch()` in components**: All HTTP calls go through `frontend/src/services/api.ts`.
- **Redis or external cache**: Requirements explicitly mandate in-memory dict with TTL. No external dependency.
- **Caching error results or None**: A failed fetch is not cached; the next request will retry live.
- **Single large `asyncio.gather` that raises on first failure**: Use `return_exceptions=True` for optional sub-calls.
- **Hardcoded base URL in components**: Use `process.env.NEXT_PUBLIC_API_BASE_URL` via the service module.
- **Storing transformed/computed values in the cache**: Cache stores raw API responses only; transformation happens at response-assembly time.

---

## 10. Dependencies

### 10.1 Backend — No New Dependencies Required

The existing dependencies (`fastapi`, `httpx`, `pydantic`, `pydantic-settings`) cover all new functionality. The TradingView scanner POST uses `httpx.AsyncClient` (already present). The in-memory cache uses a plain Python dict.

### 10.2 Frontend — No New Dependencies Required

The existing `next`, `react`, `tailwindcss`, and `typescript` packages are sufficient. All new components use the same patterns as existing components: `useState`, `useEffect`, `useRef`, Tailwind utility classes, and TypeScript interfaces.

---

## 11. Integration Points

### 11.1 Existing Backend

- `DilutionService.__init__`: The `httpx.AsyncClient` is shared across all methods including new ones. The existing `max_retries` and `retry_delay` apply to all new `_make_request_cached` / `_make_request_list_cached` calls.
- `app/utils/errors.py`: `TickerNotFoundError`, `RateLimitError`, `ExternalAPIError` are used unchanged. New methods that are "optional" (gap stats, offerings, etc.) catch these exceptions internally and return null/[].
- `app/api/v1/routes.py`: One new route `GET /gainers` is added. The existing route handler pattern is followed exactly. A `GainersService` instance is created at module level alongside `dilution_service`.
- `app/core/config.py`: No changes. `settings.askedgar_url`, `settings.askedgar_api_key`, `settings.request_timeout` are used by all new service methods.
- `app/utils/validation.py`: `validate_ticker` is called in the gainers enrichment loop to filter TradingView tickers (note: `validate_ticker` allows 1-5 chars while the gainer filter requires 2-4 chars; the gainer `TICKER_RE = re.compile(r'^[A-Z]{2,4}$')` is applied in `GainersService` before calling `validate_ticker`).

### 11.2 Existing Frontend

- `frontend/src/types/dilution.ts`: Extended in-place. `OfferingAbilityData` is replaced (breaking change in shape; `OfferingAbility.tsx` receives `offeringAbilityDesc: string | null` directly). `InPlayDilutionData` adds `convertibles` and `stockPrice`. `HeaderData` adds `stockPrice` and `chartAnalysis`.
- `frontend/src/app/globals.css`: No changes. Existing CSS custom properties (`--color-bg-card`, `--color-accent-green`, `--color-risk-low`, etc.) are used by all new components via Tailwind.
- `frontend/src/app/layout.tsx`: No changes. Space Grotesk and JetBrains Mono fonts are already loaded.
- `TickerSearch.tsx`: No changes to the component itself. `page.tsx` passes a new `onSearch` handler that routes through `apiService.fetchDilution`.

### 11.3 External APIs

- **AskEdgar** (`https://eapi.askedgar.io`): All calls use `API-KEY` header. Five new endpoints added. Existing retry logic applied.
- **TradingView Scanner** (`https://scanner.tradingview.com/america/scan`): POST with no API key. Called only from `GainersService` on the backend. Never called from browser.

---

## 12. Component-to-Requirement Traceability

| Requirement | Architecture Coverage |
|---|---|
| US-01 Two-Panel Layout | `page.tsx` rewrite with flex layout; left panel 260px fixed, right panel flex-1 |
| US-02 Top Gainers Sidebar | `TopGainersSidebar`, `GainerRow`, `GET /api/v1/gainers`, `GainersService` |
| US-03 Click-to-Load Gainer | `onGainerSelect` prop callback in `page.tsx`; `sidebarSelectedTicker` state drives highlight |
| US-04 Ticker Search Wired to API | `TickerSearch.onSearch` → `apiService.fetchDilution`; clears sidebar highlight |
| US-05 Gap Statistics Panel | `GapStats` component; `gapStats` field in `DilutionV2Response`; `get_gap_stats` service method |
| US-06 Recent Offerings Panel | `Offerings` component; `offerings` field; `get_offerings` service method |
| US-07 Ownership Panel | `Ownership` component; `ownership` field; `get_ownership` service method |
| US-08 AI Chart Analysis Badge | `ChartAnalysisBadge`; `chartAnalysis` field; `get_chart_analysis` service method; `Header` updated |
| US-09 In-Play Dilution Convertibles | `InPlayDilution` update; `ConvertibleItem` type; in-the-money computed from `stockPrice` |
| US-10 Offering Ability Parsed | `OfferingAbility` update; receives raw `offeringAbilityDesc` string; parses comma-segments internally |
| US-11 Management Commentary | `MgmtCommentary` component; `mgmtCommentary` field from `dilution-rating` response |
| US-12 Stock Price in Header | `Header` update; `stockPrice` in `DilutionV2Response`; `get_screener_price` service method |
| US-13 API Response Caching | `_cache` dict on `DilutionService`; `_cache_get`/`_cache_set` methods; 30-min TTL |
| US-14 Gainers Auto-Refresh | `setInterval` in `TopGainersSidebar`; 60-second server-side TTL in `GainersService` |
| US-15 Error States | `ApiResult<T>` discriminated union; per-component error display; 404/429/500 mapped in `apiService` |
| US-16 Loading Skeletons | All components already have skeleton pattern (`if (!data) return <Skeleton />`); extended to new components |
| US-17 Frontend API Service Layer | `frontend/src/services/api.ts`; no raw fetch in components |
| US-18 Extended Dilution Endpoint | `get_dilution_data_v2` service method; `DilutionV2Response` shape; `return_exceptions=True` gather |
| US-19 New Gainers Backend Endpoint | `GET /api/v1/gainers` route; `GainersService`; server-side TradingView POST |

---

## 13. Incremental Implementation Order

The architecture is designed to be implemented in stages without breaking existing functionality:

1. **Stage 1 — Backend cache + prefix fix**: Add `_cache_get`/`_cache_set` to `DilutionService`; fix existing endpoint prefixes (`/v1/` → `/enterprise/v1/`). No frontend change.
2. **Stage 2 — Backend V2 endpoint expansion**: Add five new service methods; update `get_dilution_data_v2`; add Pydantic response models. The existing `GET /api/v1/dilution/{ticker}` now returns V2 fields.
3. **Stage 3 — Backend gainers endpoint**: Create `GainersService`; add `GET /api/v1/gainers` route.
4. **Stage 4 — Frontend API service + types**: Create `api.ts`; extend `dilution.ts`. No UI change yet.
5. **Stage 5 — Frontend new components**: Build `GapStats`, `Offerings`, `Ownership`, `ChartAnalysisBadge`, `MgmtCommentary`, `GainerRow`, `TopGainersSidebar`.
6. **Stage 6 — Frontend updated components**: Update `Header`, `InPlayDilution`, `OfferingAbility`.
7. **Stage 7 — page.tsx rewrite**: Wire two-panel layout; connect all components to API service; implement AbortController for superseded loads.

---

## Appendix A: Sector Abbreviation Map

The `GainerRow` component abbreviates sector names for display in the compact sidebar row. This map is frontend-only (not backend).

```typescript
// frontend/src/lib/sectorAbbreviations.ts  (new utility file)
export const SECTOR_ABBR: Record<string, string> = {
  "Technology": "Tech",
  "Healthcare": "Health",
  "Consumer Defensive": "Cons Def",
  "Consumer Cyclical": "Cons Cyc",
  "Financial Services": "Financ",
  "Communication Services": "Comms",
  "Basic Materials": "Materials",
  "Industrials": "Indust",
  "Real Estate": "RE",
  "Utilities": "Util",
  "Energy": "Energy",
};
```

## Appendix B: HISTORY_MAP

```typescript
// frontend/src/lib/historyMap.ts  (new utility file)
export const HISTORY_MAP: Record<string, { label: string; color: string }> = {
  green:  { label: "Strong",      color: "#2F7D57" },
  yellow: { label: "Semi-Strong", color: "#B9A816" },
  orange: { label: "Mixed",       color: "#B96A16" },
  red:    { label: "Fader",       color: "#A93232" },
};
```

## Appendix C: mgmt_commentary Field Assumption

Requirements and INTAKE.md assume `mgmt_commentary` is a field already returned by the existing `/enterprise/v1/dilution-rating` endpoint (not a new endpoint call). The backend service method `get_dilution_data_v2` extracts it from the dilution-rating result as `dilution_data.get("mgmt_commentary")`. If this field is absent from the live API response, the field returns `null` gracefully — no code change needed.
