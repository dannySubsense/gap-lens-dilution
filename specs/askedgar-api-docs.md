# AskEdgar API Documentation

**Base URL:** `https://eapi.askedgar.io`  
**Authentication:** All data endpoints require an API key in the request header:
```
API-KEY: your_api_key_here
```

---

## Quick Start

```bash
curl "https://eapi.askedgar.io/v1/reverse-splits?ticker=AAPL" \
  -H "API-KEY: your_api_key_here"
```

```python
import requests
response = requests.get(
    "https://eapi.askedgar.io/v1/reverse-splits",
    params={"ticker": "AAPL"},
    headers={"API-KEY": "your_api_key_here"}
)
data = response.json()
```

```javascript
const response = await fetch(
    "https://eapi.askedgar.io/v1/reverse-splits?ticker=AAPL",
    { headers: { "API-KEY": "your_api_key_here" } }
);
const data = await response.json();
```

---

## Common Patterns

### Standard Response Wrapper

All data endpoints return:

```json
{
  "status": "success",
  "count": 42,
  "results": [ ... ]
}
```

### Pagination

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 0 | Page number (starts at 0) |
| `limit` | integer | 100 | Results per page (max per request) |

### Percentage and Decimal Field Conventions

| Fields | Format | Example | Meaning |
|--------|--------|---------|---------|
| All `gain_*` fields | Percentage | 15.0 | 15% gain |
| `feerate` | Percentage | 5.0 | 5% annual cost |
| `short_float` | Decimal | 0.065 | 6.5% of float is short |
| `insider_percent`, `affiliate_percent`, `institutions_percent` | Decimal | 0.125 | 12.5% ownership |

### Date Filtering

Dates are always in `YYYY-MM-DD` format.

| Parameter | Description |
|-----------|-------------|
| `date` | Exact date match |
| `date_from` | Start of date range (inclusive) |
| `date_to` | End of date range (inclusive) |

Some endpoints use `filed_at_from` / `filed_at_to` to filter on SEC filing date.

### Rating Values

Where you see a `Rating` type: `"High"`, `"Medium"`, `"Low"`

### Risk Level Values

Where you see a `RiskLevel` type: `"high"`, `"medium"`, `"low"` *(lowercase)*

### Error Responses

**401 — Invalid or missing API key:**
```json
{
  "status": "error",
  "error": {
    "code": "missing_api_key",
    "message": "API key is required. Pass it in the API-KEY header.",
    "details": {}
  },
  "request_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab"
}
```

**422 — Validation error:**
```json
{
  "status": "error",
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": {
      "fields": [
        {
          "field": "ticker",
          "reason": "Value error, Field 'ticker' must contain only uppercase letters, numbers, dots, hyphens, or carets."
        }
      ]
    }
  }
}
```

---

## Endpoints

### 1. Reverse Splits
`GET /v1/reverse-splits`

Look up reverse stock splits.

**Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | No | Filter by stock ticker |
| `date` | date | No | Exact date |
| `date_from` | date | No | Start of date range |
| `date_to` | date | No | End of date range |
| `page` | integer | No | Page number (default: 0) |
| `limit` | integer | No | Results per page (default: 100) |

**Example Response**
```json
{
  "status": "success",
  "count": 1,
  "results": [
    {
      "ticker": "AAPL",
      "execution_date": "2021-01-01",
      "split_from": 2,
      "split_to": 1
    }
  ]
}
```

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock ticker |
| `execution_date` | date | When the reverse split took effect |
| `split_from` | number | Original share count in the ratio |
| `split_to` | number | New share count in the ratio |

---

### 2. Float, Outstanding, Market Cap & Key Data
`GET /v1/float-outstanding`

Get current float, outstanding shares, market cap, and ownership breakdown.

**Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | No | Filter by stock ticker |
| `min_float` | integer | No | Minimum float |
| `max_float` | integer | No | Maximum float |
| `min_outstanding` | integer | No | Minimum outstanding shares |
| `max_outstanding` | integer | No | Maximum outstanding shares |
| `page` | integer | No | Page number |
| `limit` | integer | No | Results per page |

**Example Response**
```json
{
  "status": "success",
  "count": 1,
  "results": [
    {
      "ticker": "AAPL",
      "float": 1000000,
      "outstanding": 1000000,
      "market_cap_final": 2500000000.0,
      "industry": "Technology",
      "sector": "Electronic Equipment",
      "country": "United States",
      "isadr": false,
      "insider_percent": 0.125,
      "affiliate_percent": 0.45,
      "institutions_percent": 0.325
    }
  ]
}
```

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock ticker |
| `float` | integer | Shares held by non-affiliates |
| `outstanding` | integer | Total outstanding shares |
| `market_cap_final` | number | Market capitalization in dollars |
| `industry` | string | Industry classification |
| `sector` | string | Sector classification |
| `country` | string | Country of incorporation |
| `isadr` | boolean | Whether this is an ADR |
| `insider_percent` | number | Insider ownership (decimal) |
| `affiliate_percent` | number | Affiliate ownership (decimal) |
| `institutions_percent` | number | Institutional ownership (decimal) |

---

### 3. Dilution Rating
`GET /v1/dilution-rating`

Get AskEdgar's proprietary dilution risk rating for a stock.

**Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | No | Filter by stock ticker |
| `offering_ability` | Rating | No | Filter by offering ability rating |
| `dilution` | Rating | No | Filter by dilution rating |
| `offering_frequency` | Rating | No | Filter by offering frequency |
| `cash_need` | Rating | No | Filter by cash need urgency |
| `nasdaq_compliance` | Rating | No | Filter by Nasdaq compliance risk |
| `overall_offering_risk` | Rating | No | Filter by overall offering risk |
| `regsho` | boolean | No | Filter by Reg SHO threshold list status |
| `page` | integer | No | Page number |
| `limit` | integer | No | Results per page |

**Example Response**
```json
{
  "status": "success",
  "count": 1,
  "results": [
    {
      "ticker": "ASTC",
      "offering_ability": "Low",
      "offering_ability_desc": "No Shelf, No ATM, No S-1 Offering",
      "dilution": "Medium",
      "dilution_desc": "48.6%",
      "offering_frequency": "Low",
      "cash_need": "Medium",
      "cash_need_desc": "The company has 23.23 months of cash left...",
      "overall_offering_risk": "Low",
      "regsho": false,
      "estimated_cash": 22440000.0,
      "cash_burn": 2900000.0,
      "cash_remaining_months": 23.23,
      "total_debt_final": 1500000.0
    }
  ]
}
```

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock ticker |
| `offering_ability` | string | Rating — can company issue new shares? |
| `offering_ability_desc` | string | Human-readable explanation |
| `dilution` | string | Rating — how much have shares been diluted |
| `dilution_desc` | string | Dilution percentage |
| `offering_frequency` | string | Rating — how often company does offerings |
| `cash_need` | string | Rating — how urgently company needs cash |
| `cash_need_desc` | string | Explanation with months of cash remaining |
| `nasdaq_compliance` | string | Compliance risk rating |
| `overall_offering_risk` | string | Overall risk of future dilutive offerings |
| `regsho` | boolean | On Reg SHO threshold list |
| `warrant_exercise` | string | Warrant exercise risk rating |
| `estimated_cash` | number | Estimated current cash (dollars) |
| `cash_burn` | number | Quarterly cash burn (dollars) |
| `cash_remaining_months` | number | Months of cash remaining |
| `total_debt_final` | number | Total debt (dollars) |

---

### 4. Nasdaq Compliance
`GET /v1/nasdaq-compliance`

Get Nasdaq compliance deficiency notices and status.

**Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | No | Filter by ticker |
| `date` | date | No | Exact date |
| `date_from` / `date_to` | date | No | Date range |
| `deficiency` | string | No | Filter by deficiency type |
| `added_date_from` / `added_date_to` | date | No | When deficiency was added |
| `page` / `limit` | integer | No | Pagination |

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock ticker |
| `date` | date | Date of compliance notice |
| `deficiency` | string | Type of listing deficiency |
| `company` | string | Company name |
| `market` | string | Exchange |
| `risk` | string | Risk assessment |
| `notes` | string | Additional notes |
| `status` | string | Current status |

---

### 5. Offerings
`GET /v1/offerings`

Get stock offerings — direct, public, PIPEs, ATM, and more.

**Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | No | Filter by ticker |
| `date` / `date_from` / `date_to` | date | No | Date filters |
| `headline` | string | No | Search offering headlines (min 4 chars) |
| `offering_type` | string | No | Filter by type: `REGISTERED OFFERING`, `ATM USED`, `PRIVATE PLACEMENT`, `DEBT OFFERING`, `DEBT CONVERSION`, `SHARE ISSUANCE FOR ACQUISITION`, `NEW EQUITY LINE`, `CREDIT FACILITY`, `IPO`, `UPLIST` |
| `page` / `limit` | integer | No | Pagination |

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock ticker |
| `headline` | string | Short description |
| `filed_at` | date | SEC filing date |
| `form_type` | string | SEC form type |
| `offering_type` | string | Type of offering |
| `shares_amount` | number | Number of shares |
| `warrants_amount` | number | Number of warrants |
| `share_price` | number | Price per share |
| `offering_amount` | number | Total dollar amount |
| `conversion_price` | number | Conversion price (if applicable) |
| `askedgar_url` | string | Link to offering on AskEdgar |

---

### 5b. Offerings — Funds & Underwriters (Advanced)
`GET /v1/offerings-advanced`

Same as `/v1/offerings` with additional `investors` and `bank` fields.

> **Access:** Restricted to institutional/professional-tier API access.

Additional parameters: `investors` (fund name search), `bank` (investment bank search).

Additional response fields: `investors` (fund names), `bank` (underwriting bank).

---

### 6. Dilution Data (Warrants & Convertibles)
`GET /v1/dilution-data`

Get detailed warrant and convertible security data. **`ticker` is required.**

**Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ticker` | string | **Yes** | Stock ticker |
| `page` / `limit` | integer | No | Pagination |

**Warrant Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `details` | string | Description of the warrant issuance |
| `warrants_amount` | number | Total warrants issued |
| `warrants_remaining` | number | Warrants still outstanding |
| `warrants_exercise_price` | number | Price to exercise |
| `registered` | string | Registration status |
| `prefunded_cost` | number | Cost already paid for pre-funded warrants |
| `exercisable_date` | string | Date warrants become exercisable |
| `expiration_date` | string | Expiration date |
| `filed_at` | string | SEC filing date |
| `askedgar_url` | string | Link to filing |

**Convertible Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `details` | string | Description of the convertible |
| `conversion_price` | number | Price at which debt converts to shares |
| `registered` | string | Registration status |
| `convertible_date` | string | Issue date |
| `maturity_date` | string | Maturity date |
| `offering_amount` | number | Original dollar amount |
| `convertible_debt_remaining` | number | Remaining unconverted debt |
| `underlying_shares_remaining` | number | Shares created if all debt converts |
| `filed_at` | string | SEC filing date |
| `askedgar_url` | string | Link to filing |

---

### 7. Dilution Data — Funds & Underwriters (Advanced)
`GET /v1/dilution-data-advanced`

Same as `/v1/dilution-data` with additional bank, fund, and price protection fields.

> **Access:** Restricted to institutional/professional-tier API access.

---

### 8. Historical Float & Market Cap (Pro)
`GET /v1/historical-float-pro`

Historical float, outstanding shares, and ownership data from SEC filings.

> **Note:** `reported_date` is the "as of" date, not the filing date. Use `filed_at` for when the document was filed.

**Key Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | Filter by ticker |
| `latest_data` | boolean | `true` = only most recent data point per ticker |
| `filed_at_from` / `filed_at_to` | date | SEC filing date range |
| `reported_date_from` / `reported_date_to` | date | "As of" date range |
| `is_adr` | boolean | Set `false` to exclude ADRs for accuracy |

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock ticker |
| `filed_at` | date | SEC filing date |
| `reported_date` | date | "As of" date for the share data |
| `outstanding_shares` | integer | Total outstanding shares |
| `float` | integer | Non-affiliate shares |
| `tradable_float` | integer | True tradable float |
| `affiliate_shares` | integer | Affiliate-held shares |
| `insider_percent` | number | Insider ownership (decimal) |
| `affiliate_percent` | number | Affiliate ownership (decimal) |
| `institutions_percent` | number | Institutional ownership (decimal) |
| `market_cap` | integer | Market capitalization |
| `is_adr` | boolean | Whether this is an ADR |

---

### 9. News & Filings
`GET /v1/news`

Get news articles and SEC filings for a ticker.

> `body`, `title`, `author`, and `channels` fields are only populated for `form_type = "news"`. For SEC filings, use `summary`.

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | Filter by ticker |
| `date` / `date_from` / `date_to` | date | Date filters |
| `tag` | string | Filter by topic tag (see full list below) |
| `query` | string | Full-text search |
| `hide_news` | boolean | Show only SEC filings |
| `hide_filings` | boolean | Show only news |

**Valid `tag` values:** `Earnings`, `Contracts`, `Expansion Plans`, `Product Launches`, `Dividends`, `Mergers`, `Acquisitions`, `Management Changes`, `FDA`, `Divestures`, `Restructuring`, `Financial Trouble`, `Offerings`, `Dilution`, `Legal Disputes`, `Payment Defaults`, `Credit Rating Changes`, `Operational Disruptions`, `Accounting Changes`, `Workforce Reduction`, `Investor Conferences`, `Delisting Actions`, `IPOs`, `Name Changes`, `Offer for sale`, `Earnings Calls`, `Partnerships`, `License Agreements`, `Upcoming Events`, `Financial Performance`, `Insider Selling`, `Insider Buying`, `Positive Data`, `Negative Data`, `Clinical Trials`, `Stock Splits`, `Executive Compensation`, `Cryptocurrency`, `Patents`, `Bankruptcy`, `Buyback`, `Capital Structure`, `Financing Activity`, `Cannabis`, `Shareholder Vote`, `AI`, `Cash Runway`, `Other`

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock ticker |
| `filed_at` | date | Filing or article date |
| `form_type` | string | `"news"`, `"grok"`, `"jmt415"`, or SEC form type |
| `summary` | string | Short summary (all types) |
| `body` | string | Full text (news only) |
| `title` | string | Article title (news only) |
| `author` | string | Author name (news only) |
| `tags` | array | Topic tags |
| `document_url` | string | URL to original document |

---

### 10. SEC Registrations
`GET /v1/registrations`

Shelf registrations, equity lines, ATM programs, and share resale registrations.

**Registration Types (`type` parameter)**

| Value | Description |
|-------|-------------|
| `SHELF` | Shelf registration — sell shares over time (up to 3 years) |
| `SPA` | Equity line — continuous sales to a single institutional investor |
| `OFFERING` | New primary offering |
| `SHARE RESALE` | Previously issued shares registered for public resale |

**Key Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | Filter by ticker |
| `effective_status` | boolean | `true` = currently effective |
| `is_atm` | boolean | Filter for ATM programs |
| `over_baby_shelf` | boolean | Filter for companies over baby shelf limit |
| `type` | string | Registration type |
| `bank` | string | Filter by investment bank |

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock ticker |
| `headline` | string | Description of the registration |
| `filed_at` | date | SEC filing date |
| `effective_date` | date | Date registration became effective |
| `effective_status` | boolean | Currently effective |
| `expiration_date` | date | Expiration date |
| `offering_amount` | number | Total amount registered |
| `is_atm` | boolean | Is an ATM program |
| `bank` | string | Investment bank |
| `amount_remaining_atm` | number | Remaining ATM amount |
| `over_baby_shelf` | boolean | Exceeds baby shelf threshold |
| `askedgar_url` | string | Link on AskEdgar |

---

### 11. Agreements
`GET /v1/agreements`

Registration rights, participation rights, and equity restriction agreements.

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | Filter by ticker |
| `agreement_type` | string | `registration_rights`, `equity_restriction`, `participation_rights` |
| `filed_at_from` / `filed_at_to` | date | Filing date range |

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `agreement_type` | string | Type of agreement |
| `is_registration_rights` | boolean | Includes registration rights |
| `is_restriction_present` | boolean | Includes equity restrictions |
| `is_right_of_participation` | boolean | Includes participation rights |
| `investor_names` | string | Names of investors |
| `registration_deadline` | integer | Days until registration must be filed |
| `penalties` | string | Penalty for missing deadlines |
| `equity_restriction_end_date` | date | End of equity restriction |

---

### 12. Pump & Dump Tracker
`GET /v1/pump-and-dump-tracker`

Stocks showing characteristics of potential pump-and-dump schemes.

**Risk Level Parameters**

| Parameter | Values | Description |
|-----------|--------|-------------|
| `country_risk` | `high`, `medium`, `low` | `high` = Asian countries |
| `scam_risk` | `high`, `medium`, `low` | `high` = recent coordinated pump evidence |
| `float_risk` | `high`, `medium`, `low` | `high` = under 5M tradable float |
| `underwriter_risk` | `high`, `medium`, `low` | `high` = underwriter linked to prior P&Ds |

**Key Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | Stock ticker |
| `tradable_float` | integer | Tradable float shares |
| `number_liquidations` | integer | Number of liquidation events |
| `lock_up_expiration` | date | IPO lock-up expiration |
| `country_risk` | string | Country risk level |
| `scam_risk` | string | Coordinated pump evidence level |
| `float_risk` | string | Float risk level |
| `underwriter_risk` | string | Underwriter risk level |
| `scam_description` | string | Description of scam indicators |
| `gain_1_day` / `gain_7_day` / etc. | number | Price change percentages |

---

### 13. Stock Screener
`GET /v1/screener`

Screen stocks by 60+ financial criteria.

**Basic Filters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticker` | string | Filter by ticker |
| `industry` / `sector` / `country` / `exchange` | string | Use `/v1/screener/options` for valid values |
| `isadr` | boolean | Filter for ADRs |
| `isactivelytrading` | boolean | Filter for actively trading stocks |

**Price & Market Cap**

| Parameter | Description |
|-----------|-------------|
| `min_market_cap` / `max_market_cap` | Market cap range |
| `min_price` / `max_price` | Price range |

**Share Structure**

| Parameter | Description |
|-----------|-------------|
| `min_float` / `max_float` | Float range |
| `min_tradable_float` / `max_tradable_float` | Tradable float range |
| `min_outstanding` / `max_outstanding` | Outstanding shares range |

**Short Selling**

| Parameter | Description |
|-----------|-------------|
| `min_short_float` / `max_short_float` | Short float as decimal |
| `min_feerate` / `max_feerate` | Borrow fee rate % |
| `min_days_to_cover` / `max_days_to_cover` | Days to cover |

**Price Performance** (values are percentages, e.g., 15.0 = 15%)

`min_gain_1_day`, `max_gain_1_day`, `min_gain_7_day`, `max_gain_7_day`, `min_gain_14_day`, `max_gain_14_day`, `min_gain_30_day`, `max_gain_30_day`, `min_gain_60_day`, `max_gain_60_day`, `min_gain_90_day`, `max_gain_90_day`, `min_gain_180_day`, `max_gain_180_day`, `min_gain_365_day`, `max_gain_365_day`

---

### 14. Screener Options
`GET /v1/screener/options`

Get valid values for a screener dropdown field.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `field` | string | **Yes** | `industry`, `sector`, `country`, `exchange`, `state`, `currency` |

---

### 15. Right of First Refusal & Tail Financings
`GET /v1/rofr`

ROFR and tail financing data from SEC filings.

> **Access:** Restricted to institutional/professional-tier API access.

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `bank_name` | string | Investment bank |
| `right_of_first_refusal_present` | boolean | ROFR provision exists |
| `right_of_first_refusal_duration` | number | Duration in days |
| `right_of_first_refusal_end_date` | date | ROFR expiration |
| `tail_financing_payments_present` | boolean | Tail financing provision exists |
| `tail_financing_payments_duration` | number | Duration in days |

---

### 16. Ownership
`GET /v1/ownership`

Ownership data grouped by reported date. **`ticker` is required.**

**Response** — grouped by `reported_date`, each containing an array of `owners`:

| Field | Type | Description |
|-------|------|-------------|
| `owner_name` | string | Name of the owner |
| `owner_type` | string | `Executive`, `Director`, `10+ Percent Investor`, `5-10 Percent Investor` |
| `title` | string | Role (e.g., "CEO") |
| `common_shares_amount` | integer | Common shares held |
| `options_amount` | integer | Options held |
| `warrants_amount` | integer | Warrants held |
| `outstanding_shares_final` | number | Total outstanding at time of report |

---

### 17. AI Chart Analysis (Gap Analysis)
`GET /v1/ai-chart-analysis`

AI-generated chart analysis for gap-up days. **`ticker` is required.**

> Generated within a few minutes of a ticker hitting +20% on the day. Poll this endpoint — no webhook available.

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `gain_percentage` | number | How much stock was up when analysis generated |
| `chart_count` | integer | Number of historical gap-up days analyzed |
| `analysis_text` | string | AI-generated analysis |
| `rating` | string | `green` (closes strong), `yellow` (mixed), `orange` (mostly weak), `red` (always weak) |
| `created_at` | datetime | When analysis was generated |

---

### 18. Research Reports

All three require `ticker`. Generated within minutes of +40% on the day. Poll — no webhook.

#### 18a. Full Research Report
`GET /v1/research-reports`

| Field | Type | Description |
|-------|------|-------------|
| `report_text` | string | Full research report |
| `gain_percentage` | number | How much stock was up |
| `created_at` | datetime | When generated |

#### 18b. Short Research Report
`GET /v1/research-reports-short`

More data sources; takes 10–15 minutes after +40%. Same fields as full report, plus `tradable_float`, `outstanding`, `country`, `industry`.

#### 18c. TLDR Research Report
`GET /v1/research-reports-tldr`

| Field | Type | Description |
|-------|------|-------------|
| `tldr_text` | string | Very short TLDR summary |
| `report_id` | integer | ID linking to full report |

---

### 19. Market Strength
`GET /v1/market-strength`

AI-generated analysis of overall small-cap market strength. Generated daily at 2:30 AM CST.

| Parameter | Type | Description |
|-----------|------|-------------|
| `date` | date | Specific date |
| `latest` | boolean | `true` = most recent analysis |

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `date` | date | Date of analysis |
| `analysis` | string | AI-generated market analysis |
| `performance` | string | AI-generated performance summary |

---

### 20. Filing Titles
`GET /v1/filing-titles`

AI-generated human-readable filing headlines.

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `headline` | string | AI-generated one-liner (e.g., "Announces $50M ATM offering") |
| `form_type` | string | SEC form type |
| `filed_at` | date | Filing date |
| `document_url` | string | URL to SEC document |

---

### 21. Gap Stats
`GET /v1/gap-stats`

Historical gap-up statistics per ticker. **`ticker` is required.** Day 1 gaps only (excludes multi-day runs). Results ordered by date descending.

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `date` | date | Date of gap-up |
| `market_open` | number | Open price |
| `market_close` | number | Close price |
| `gap_percentage` | number | Gap-up % vs previous close |
| `intraday_high` | number | Intraday high |
| `intraday_high_time` | string | Timestamp of intraday high |
| `vwap` | number | Volume-weighted average price |
| `premarket_high` | number | Premarket high |
| `premarket_volume` | integer | Premarket volume |
| `volume` | integer | Total day volume |
| `form_types` | array | Associated SEC form types |
| `tags` | array | Tags associated with the gap event |

---

## Common Use Cases

### Show dilution risk for a stock
1. `GET /v1/dilution-rating?ticker=XXXX` — overall risk profile
2. `GET /v1/dilution-data?ticker=XXXX` — specific warrants and convertibles
3. `GET /v1/registrations?ticker=XXXX&effective_status=true` — active shelf registrations

### Find risky small-cap stocks
1. `GET /v1/screener?max_market_cap=300000000&max_float=5000000&isactivelytrading=true`
2. For each result: `GET /v1/dilution-rating?ticker=XXXX`

### Get recent offerings
1. `GET /v1/offerings?ticker=XXXX&date_from=2024-01-01`

### Get AI report on a runner
- +20%: poll `GET /v1/ai-chart-analysis?ticker=XXXX`
- +40%: poll `GET /v1/research-reports-tldr?ticker=XXXX` (available within minutes)
- Wait 10–15 min: `GET /v1/research-reports-short?ticker=XXXX`
- Full deep-dive: `GET /v1/research-reports?ticker=XXXX`

### Check market conditions
- `GET /v1/market-strength?latest=true`

### Check pump & dump risk
- `GET /v1/pump-and-dump-tracker?ticker=XXXX`

### Track float over time
- `GET /v1/historical-float-pro?ticker=XXXX`

---

## Full Endpoint Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/v1/reverse-splits` | GET | API-KEY | Reverse stock splits |
| `/v1/float-outstanding` | GET | API-KEY | Float, outstanding, market cap, ownership |
| `/v1/dilution-rating` | GET | API-KEY | Dilution risk ratings |
| `/v1/nasdaq-compliance` | GET | API-KEY | Nasdaq compliance deficiency notices |
| `/v1/offerings` | GET | API-KEY | Stock offerings |
| `/v1/offerings-advanced` | GET | API-KEY | Offerings + fund & bank details *(institutional)* |
| `/v1/dilution-data` | GET | API-KEY | Warrants & convertibles *(ticker required)* |
| `/v1/dilution-data-advanced` | GET | API-KEY | Dilution data + bank & fund details *(institutional)* |
| `/v1/historical-float-pro` | GET | API-KEY | Historical float & market cap |
| `/v1/news` | GET | API-KEY | News articles & SEC filings |
| `/v1/registrations` | GET | API-KEY | SEC registrations (shelf, ATM, equity line) |
| `/v1/agreements` | GET | API-KEY | Registration rights, participation rights, equity restrictions |
| `/v1/rofr` | GET | API-KEY | Right of first refusal & tail financing *(institutional)* |
| `/v1/ownership` | GET | API-KEY | Ownership data *(ticker required)* |
| `/v1/pump-and-dump-tracker` | GET | API-KEY | Pump & dump risk tracker |
| `/v1/screener` | GET | API-KEY | Stock screener with 60+ filters |
| `/v1/screener/options` | GET | API-KEY | Valid values for screener filters |
| `/v1/ai-chart-analysis` | GET | API-KEY | AI gap analysis *(ticker required)* |
| `/v1/research-reports` | GET | API-KEY | Full AI research report *(ticker required)* |
| `/v1/research-reports-short` | GET | API-KEY | Short AI research report *(ticker required)* |
| `/v1/research-reports-tldr` | GET | API-KEY | TLDR AI research report *(ticker required)* |
| `/v1/market-strength` | GET | API-KEY | AI small-cap market strength analysis |
| `/v1/filing-titles` | GET | API-KEY | AI-generated filing headlines |
| `/v1/gap-stats` | GET | API-KEY | Historical gap-up statistics *(ticker required)* |
