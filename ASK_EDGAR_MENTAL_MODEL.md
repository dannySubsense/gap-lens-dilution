# Ask Edgar API Mental Model

## API Endpoints

### 1. Dilution Rating Endpoint
**URL:** `https://eapi.askedgar.io/enterprise/v1/dilution-rating`
**Purpose:** Overall dilution risk assessment
**Key Fields:**
- `overall_risk`: String ("High", "Medium", "Low", "N/A")
- `offering_ability`: String (risk level)
- `dilution`: String (risk level)
- `frequency`: String (offering frequency)
- `cash_need`: String (cash runway risk)
- `warrants`: String (warrant risk level)

### 2. Float/Outstanding Endpoint
**URL:** `https://eapi.askedgar.io/enterprise/v1/float-outstanding`
**Purpose:** Share structure and ownership data
**Key Fields:**
- `float`: Integer (shares)
- `outstanding`: Integer (shares)
- `market_cap`: Float (market capitalization)
- `sector`: String (industry sector)
- `country`: String (country code)
- `insider_percent`: Float (insider ownership %)
- `institutions_percent`: Float (institutional ownership %)

### 3. News/SEC Filings Endpoint
**URL:** `https://eapi.askedgar.io/enterprise/v1/news`
**Purpose:** Recent news, 8-K, 6-K, grok summaries, analyst notes
**Key Fields:**
- `form_type`: String ("news", "8-K", "6-K", "grok", "jmt415")
- `title`: String (headline)
- `summary`: String (content)
- `url`: String (source URL)
- `filed_at`: String (date YYYY-MM-DD)
- `created_at`: String (timestamp)

### 4. Dilution Data Endpoint
**URL:** `https://eapi.askedgar.io/enterprise/v1/dilution-data`
**Purpose:** Warrants, convertibles, and in-play dilution instruments
**Key Fields:**
- `warrants_exercise_price`: Float (strike price)
- `warrants_remaining`: Integer (shares remaining)
- `conversion_price`: Float (convertible conversion price)
- `underlying_shares_remaining`: Integer (shares)
- `registered`: String ("Registered" or "Not Registered")
- `details`: String (instrument description)
- `filed_at`: String (filing date)

### 5. Screener/Price Endpoint
**URL:** `https://eapi.askedgar.io/v1/screener`
**Purpose:** Current stock price
**Key Fields:**
- `price`: Float (last price)

## Risk Color Coding

| Risk Level | Color | Hex Code |
|------------|-------|----------|
| High | Red | #A93232 |
| Medium | Orange | #B96A16 |
| Low | Green | #2F7D57 |
| N/A | Gray | #4A525C |

## In-Play Dilution Logic

### Warrants
- Filter: `warrants_exercise_price <= current_price * 4`
- Must have `warrants_remaining > 0`
- Color: Green if strike <= current price (in the money), Orange otherwise

### Convertibles
- Filter: `conversion_price <= current_price * 4`
- Must have `underlying_shares_remaining > 0`
- Exclude "Not Registered" unless filed > 6 months ago

### Registration Status
- "Not Registered" items excluded by default
- Override: Allow if convertible and filed_at > 6 months ago

## Authentication
- Header: `API-KEY: {key}`
- Content-Type: `application/json`
- Rate limit: 50 unique tickers/day per endpoint (from INTAKE.md)

## Response Format
All endpoints return:
```json
{
  "status": "success",
  "results": [...]
}
```

## Key Insights for Gap Lens Dilution

1. **Multiple API calls required per ticker** (5 endpoints)
2. **Enterprise endpoints** use `/enterprise/v1/` path
3. **Complex filtering logic** for in-play dilution (price proximity + registration + age)
4. **Color-coded risk levels** with specific hex values
5. **News includes multiple form types** (news, 8-K, 6-K, grok AI summary, jmt415 analyst notes)
6. **Cash/burn data** comes from dilution-rating endpoint, not dilution-data
