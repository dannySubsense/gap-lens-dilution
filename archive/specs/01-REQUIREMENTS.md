# Requirements Document: Gap Lens Dilution (Phase 1 - MVP)

**Version:** 1.0
**Date:** 2026-03-22
**Status:** Approved for Implementation

---

## 1. Overview

Gap Lens Dilution is a financial analysis tool that provides dilution metrics and historical price visualization for publicly traded companies. Phase 1 focuses on single-ticker analysis with static Ask-Edgar data display.

---

## 2. User Stories

### US-1: Ticker Input and Data Retrieval
**As a** financial analyst
**I want to** enter a stock ticker symbol and retrieve dilution metrics
**So that** I can assess the company's capital structure and dilution risk

**Acceptance Criteria:**
- User can input a single ticker symbol (e.g., "AAPL", "TSLA")
- Input is case-insensitive
- System validates ticker format (letters only, 1-5 characters)
- System fetches data from Ask-Edgar API on submission
- Loading indicator displays during data fetch
- Success: Display metrics and chart
- Failure: Display appropriate error message

**Priority:** P0 (Critical)

---

### US-2: Priority Metrics Display
**As a** financial analyst
**I want to** view key dilution and financial metrics in a structured format
**So that** I can quickly assess offering risk and capital position

**Acceptance Criteria:**
- Display all priority metrics with labels and values:
  - `overall_offering_risk` (composite score)
  - `offering_ability` (rating)
  - `dilution` (rating)
  - `cash_need` (rating)
  - `cash_remaining_months` (months)
  - `estimated_cash` (dollars)
  - `cash_burn` (monthly)
  - `float` (shares)
  - `outstanding` (shares)
  - `market_cap_final` (dollars)
  - `insider_percent` (percentage)
  - `institutions_percent` (percentage)
- Format numbers with commas, decimals, and currency symbols
- Handle null/missing values (display "N/A")
- Metrics refresh on each new ticker search

**Priority:** P0 (Critical)

---

### US-3: Historical Price Chart
**As a** financial analyst
**I want to** view a historical price chart for the ticker
**So that** I can understand price trends and volatility

**Acceptance Criteria:**
- Display TradingView Lightweight Charts component
- Chart shows historical price data (candlestick/OHLC)
- Chart includes volume bars
- Interactive features: zoom, pan, crosshair
- Chart updates when new ticker is searched
- No dilution overlay in Phase 1

**Priority:** P0 (Critical)

---

### US-4: Error Handling - Ticker Not Found (404)
**As a** user
**I want to** receive clear feedback when a ticker doesn't exist
**So that** I can correct my input

**Acceptance Criteria:**
- Detect 404 response from Ask-Edgar API
- Display message: "Ticker '[SYMBOL]' not found. Please verify the symbol."
- Clear previous data from display
- Allow immediate retry with different ticker
- Log error for debugging

**Priority:** P0 (Critical)

---

### US-5: Error Handling - Rate Limit (429)
**As a** user
**I want to** be informed when I've exceeded API rate limits
**So that** I know when to retry

**Acceptance Criteria:**
- Detect 429 response from Ask-Edgar API
- Display message: "Rate limit exceeded. Please wait [X] seconds before retrying."
- Extract retry-after header if available
- Log rate limit event

**Priority:** P0 (Critical)

---

### US-6: Error Handling - Server and Network Errors
**As a** user
**I want to** receive appropriate feedback for server or network failures
**So that** I understand the issue and can take action

**Acceptance Criteria:**
- Detect 5xx responses (500, 502, 503, 504)
- Detect network timeout errors
- Detect connection unavailable errors
- Display messages:
  - 5xx: "Service temporarily unavailable. Please try again later."
  - Network: "Network error. Please check your connection and try again."
- Provide retry mechanism
- Log full error details

**Priority:** P0 (Critical)

---

### US-7: Design System Compliance
**As a** user
**I want** the interface to match Gap Research design patterns
**So that** I have a consistent experience

**Acceptance Criteria:**
- Use Gap Research color palette
- Use Gap Research typography (fonts, sizes, weights)
- Follow Gap Research card layout patterns
- Match Gap Research spacing and padding
- Use Gap Research button/input styles
- Use Gap Research alert styles for errors

**Priority:** P0 (Critical)

---

## 3. Edge Cases

### EC-1: Malformed Ticker Input
- **Scenario:** User enters numbers, special characters, spaces, or >5 characters
- **Expected:** Frontend validation prevents API call, inline error shown

### EC-2: Partial Data from API
- **Scenario:** Ask-Edgar returns 200 with some metrics null/missing
- **Expected:** Display available metrics, show "N/A" for missing, no error state

### EC-3: Large Numeric Values
- **Scenario:** Market cap in trillions, billions
- **Expected:** Format with commas, maintain readability, no UI layout break

### EC-4: Concurrent Requests
- **Scenario:** User rapidly submits multiple tickers
- **Expected:** Cancel previous request, display latest result only

### EC-5: Chart Data Unavailable
- **Scenario:** Price history not available for valid ticker
- **Expected:** Display metrics without chart, show "Chart data unavailable"

### EC-6: Empty API Response
- **Scenario:** API returns 200 with empty/null body
- **Expected:** Treat as error, display "No data available for this ticker"

---

## 4. Out of Scope (Phase 1)

Explicitly **NOT** included in Phase 1:

- Dilution events overlay on price chart
- Multi-ticker comparison
- Historical dilution tracking over time
- User authentication or accounts
- Saved searches or watchlists
- Data export (CSV, PDF)
- Custom date range selection
- Advanced chart indicators
- Real-time data updates (WebSockets)
- Gap Research platform integration
- Mobile-responsive design
- Dark mode toggle

---

## 5. Non-Functional Requirements

### NFR-1: Performance
- API response time < 3 seconds (95th percentile)
- Chart renders within 1 second of data availability
- Input validation feedback < 100ms

### NFR-2: Reliability
- Target 99% uptime during business hours
- All errors handled (no silent failures)
- Consistent number formatting, no precision loss

### NFR-3: Usability
- Adhere to Gap Research design system
- Keyboard navigation for input and buttons
- Clear, actionable, non-technical error messages

### NFR-4: Maintainability
- Type hints in Python code
- Consistent naming conventions
- Inline comments for complex logic
- README with setup instructions

### NFR-5: Security
- Input validation prevents injection attacks
- CORS configured for frontend-backend communication
- API keys stored in environment variables (never committed)

### NFR-6: Scalability
- Core logic modular for future platform integration
- Configuration externalized (API endpoints, timeouts)

---

## 6. Technical Constraints

### TC-1: Technology Stack
- **Backend:** FastAPI (Python 3.10+)
- **Frontend:** Vanilla JavaScript (ES6+), HTML5, CSS3
- **Charting:** TradingView Lightweight Charts
- **API:** Ask-Edgar for dilution metrics
- **Design System:** Gap Research design tokens

### TC-2: Architecture
- Standalone FastAPI app (not integrated into broader platform)
- Designed for modular extraction into shared library later

### TC-3: Data
- Ask-Edgar API primary source (static data only)
- On-demand fetch per query
- No caching or database required in Phase 1

### TC-4: Browser Support
- Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- IE11 not supported

### TC-5: Deployment
- ASGI server (Uvicorn) for FastAPI
- Environment variables for configuration
- Logs to standard output

---

## 7. Assumptions

1. Ask-Edgar API has <5% error rate under normal load
2. Users understand valid ticker symbols (no autocomplete needed)
3. Data is static/periodic, not real-time
4. Users access from desktop/laptop (not mobile-optimized)
5. Users have stable internet connection
6. Price data available for most US-listed tickers
7. Gap Research design system is documented and accessible
8. UI text in English only

---

## 8. Dependencies

### External APIs
- Ask-Edgar API for dilution metrics
- Price data source for TradingView chart

### Libraries
- FastAPI (backend)
- TradingView Lightweight Charts (frontend)
- Python requests/httpx (HTTP client)

### Infrastructure
- ASGI server (Uvicorn)
- Static file serving

---

## 9. Phase 1 Completion Criteria

**MVP is complete when:**

✅ User can enter ticker and view priority metrics
✅ Historical price chart displays
✅ All error types (404, 429, 5xx, network) handled with clear messages
✅ Input validation prevents malformed queries
✅ Design matches Gap Research system
✅ Standalone FastAPI service runs without platform integration
✅ Code modular for future integration
✅ Errors logged for debugging

---

## 10. Open Questions

1. **Price Data Source:** Which service provides OHLC data for TradingView?
2. **Ask-Edgar Rate Limits:** What are actual limits? Retry strategy?
3. **Design System Assets:** Location of Gap Research CSS/tokens?
4. **Deployment Target:** Local dev, cloud VM, or containerized?
5. **Error Logging:** Stdout, file, or external service?

---

**Status:** ✅ READY FOR ARCHITECTURE DESIGN
**Next Step:** @architect designs system architecture
