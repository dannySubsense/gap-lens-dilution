# Implementation Roadmap: Gap Lens Dilution Phase 1

**Version:** 1.0
**Date:** 2026-03-22
**Status:** READY FOR IMPLEMENTATION

---

## Overview

16 implementation slices broken into 4 phases: Setup (3), Core (6), Enhancement (5), Polish (2).

Each slice:
- Delivers testable functionality
- Has clear acceptance criteria
- Takes 2-4 hours
- Lists exact files and functions

Backend and frontend can develop in parallel after Slice 3.

---

## Phase 1: Setup (Slices 1-3)

### Slice 1: Project Scaffold
**Duration:** 2-3 hours
**Dependencies:** None

**Create:**
- `backend/main.py` - FastAPI app with health endpoint
- `backend/config.py` - Environment configuration
- `backend/requirements.txt` - Dependencies
- `frontend/index.html` - Basic structure
- `frontend/css/styles.css` - Empty stylesheet
- `frontend/js/app.js` - Entry point
- `.env.example` - Template
- `.gitignore` - Git configuration

**Acceptance:**
- ✅ `uvicorn backend.main:app --reload` starts without error
- ✅ `GET /health` returns `{"status": "ok"}`
- ✅ Environment variables load from `.env`
- ✅ CORS allows frontend origin

---

### Slice 2: Polygon.io API Client
**Duration:** 3-4 hours
**Dependencies:** Slice 1

**Create:**
- `backend/clients/polygon_client.py` - PolygonClient class
- `backend/tests/test_polygon_client.py` - Test suite

**Methods:**
- `get_ticker_details(symbol: str)` - Company info
- `get_stock_splits(symbol: str, from_date, to_date)` - Splits
- `get_previous_close(symbol: str)` - Latest price

**Error Handling:**
- TickerNotFoundError (404)
- RateLimitError (429)
- PolygonAPIError (5xx)
- Network timeouts

**Acceptance:**
- ✅ Fetches real data from Polygon.io
- ✅ Rate limiting handled correctly
- ✅ All error types tested
- ✅ Tests pass: `pytest backend/tests/test_polygon_client.py`

---

### Slice 3: API Schemas
**Duration:** 2-3 hours
**Dependencies:** Slice 1

**Create:**
- `backend/models/requests.py` - Request schemas
- `backend/models/responses.py` - Response schemas
- `backend/tests/test_models.py` - Validation tests

**Schemas:**
```python
class AnalysisRequest:
    ticker: str (1-10 uppercase letters)

class MetricValue:
    value: float | None
    label: str
    interpretation: str

class AnalysisResponse:
    ticker: str
    company_name: str
    metrics: dict[str, MetricValue]  # 12 metrics
    chart_data: ChartData
    timestamp: str
```

**Acceptance:**
- ✅ All models validate correctly
- ✅ Invalid tickers rejected
- ✅ All 12 metrics defined
- ✅ Tests pass

---

## Phase 2: Core (Slices 4-9)

### Slice 4: Dilution Calculator
**Duration:** 3-4 hours
**Dependencies:** Slices 2, 3

**Create:**
- `backend/services/dilution_calculator.py`
- `backend/tests/test_dilution_calculator.py`

**Methods:**
- `calculate_gap_lens_dilution(splits: list, days: int)` → float
- `calculate_cumulative_dilution(splits: list)` → float
- `calculate_annualized_rate(total: float, days: int)` → float

**Acceptance:**
- ✅ Correct for single split
- ✅ Cumulative dilution across multiple splits
- ✅ Proper annualization (365-day year)
- ✅ Handle edge cases (no splits, reverse splits)
- ✅ Coverage > 90%

---

### Slice 5: Metrics Service
**Duration:** 3-4 hours
**Dependencies:** Slices 2, 3, 4

**Create:**
- `backend/services/metric_service.py`
- `backend/tests/test_metric_service.py`

**Computes 12 Metrics:**
1. 1-Year Dilution %
2. 3-Year Dilution %
3. 5-Year Dilution %
4. Cumulative Dilution %
5. Annualized Rate
6. Split Count (1Y)
7. Split Count (3Y)
8. Split Count (5Y)
9. Days Since Last Split
10. Largest Split %
11. Average Split Size
12. Trend (accelerating/stable/decelerating)

**Method:**
- `compute_all_metrics(ticker_data: dict, splits: list)` → dict

**Acceptance:**
- ✅ All 12 metrics compute correctly
- ✅ Interpretations are human-readable
- ✅ Null data handled gracefully
- ✅ Coverage > 95%

---

### Slice 6: Chart Data Service
**Duration:** 2-3 hours
**Dependencies:** Slices 2, 3

**Create:**
- `backend/services/chart_service.py`
- `backend/tests/test_chart_service.py`

**Method:**
- `prepare_chart_data(ticker: str, splits: list)` → ChartData

**Output:**
```python
class ChartData:
    candles: list[Candle]  # OHLCV data
    dilution_markers: list[DilutionMarker]
    overlays: list[OverlayLine]
```

**Acceptance:**
- ✅ Data format matches TradingView spec
- ✅ Markers at correct dates
- ✅ Overlays calculated correctly
- ✅ Validates against schema

---

### Slice 7: Analysis Endpoint
**Duration:** 3-4 hours
**Dependencies:** Slices 2, 3, 4, 5, 6

**Modify:**
- `backend/main.py` - Add endpoint
- `backend/tests/test_endpoints.py` - Tests

**Endpoint:**
```
POST /api/analyze
Body: {"ticker": "AAPL"}
Response: AnalysisResponse
```

**Orchestrates:**
1. Fetch ticker details
2. Fetch splits (5-year)
3. Calculate metrics
4. Prepare chart data
5. Assemble response

**Error Handling:**
- 404 for invalid ticker
- 422 for malformed request
- 429 for rate limit
- 503 for API errors

**Acceptance:**
- ✅ Returns valid AnalysisResponse
- ✅ All error codes correct
- ✅ Response time < 3 seconds
- ✅ All tests pass

---

### Slice 8: Frontend Core
**Duration:** 2-3 hours
**Dependencies:** Slice 3, 7

**Modify:**
- `frontend/index.html` - Structure
- `frontend/css/styles.css` - Design system
- `frontend/js/app.js` - Controller
- `frontend/js/api.js` - API client

**Structure:**
- Gap Research masthead
- Ticker input form
- Loading container
- Error display
- Results container

**API Client:**
- `analyzeTicker(symbol)` - Fetch analysis
- Error handling
- Response parsing

**Acceptance:**
- ✅ Form validates client-side
- ✅ Loading spinner shows
- ✅ Errors display in alert
- ✅ Design matches Gap Research
- ✅ Works in Chrome, Firefox, Safari

---

### Slice 9: TradingView Chart
**Duration:** 3-4 hours
**Dependencies:** Slices 6, 8

**Create:**
- `frontend/js/chart.js` - Chart integration
- Add TradingView CDN to `index.html`
- Add chart styling to `styles.css`

**Functions:**
- `createChart(containerId)` - Initialize
- `updateChart(chartData)` - Render data

**Features:**
- Candlestick data
- Dilution markers (red, down arrows)
- Overlay lines
- Responsive sizing
- Dark theme matching Gap Research

**Acceptance:**
- ✅ Chart renders with data
- ✅ Markers at correct dates
- ✅ Overlay lines show
- ✅ Responsive design works
- ✅ Tooltip shows dilution on hover

---

## Phase 3: Enhancement (Slices 10-14)

### Slice 10: Metrics Dashboard
**Duration:** 3-4 hours
**Dependencies:** Slice 8

**Create:**
- `frontend/js/metrics.js` - Metrics rendering
- Modify `index.html` - Add grid
- Add styles to `styles.css`

**Method:**
- `renderMetrics(metricsData)` - Create 12 cards

**Cards:**
- Display value, label, interpretation
- Color code (red for high dilution)
- Grid layout (3 columns desktop)

**Acceptance:**
- ✅ All 12 metrics display
- ✅ Color coding applied
- ✅ Null values show "N/A"
- ✅ Typography correct
- ✅ Proper spacing/shadows

---

### Slice 11: Error Handling UI
**Duration:** 2-3 hours
**Dependencies:** Slice 8

**Create:**
- `frontend/js/errors.js` - Error display

**Methods:**
- `displayError(error)` - Show error message
- `clearErrors()` - Remove error

**Messages:**
- 404: "Ticker not found. Please verify."
- 422: "Invalid format. Uppercase letters only."
- 429: "Rate limit exceeded. Try again later."
- 503: "Data provider unavailable."
- Network: "Connection failed. Check internet."

**Acceptance:**
- ✅ Each error shows appropriate message
- ✅ Error box dismissible
- ✅ Previous errors clear on new search
- ✅ 404 includes ticker symbol

---

### Slice 12: Loading States
**Duration:** 2 hours
**Dependencies:** Slice 8

**Create:**
- `frontend/js/loading.js` - Loading UI

**Methods:**
- `showLoading(message)` - Show spinner
- `hideLoading()` - Remove spinner

**Features:**
- Spinner animation
- Skeleton screens for metrics
- Progress indicator
- Disable form during loading

**Acceptance:**
- ✅ Spinner appears immediately
- ✅ Form disabled during loading
- ✅ Skeleton screens show
- ✅ Cleared on success/error
- ✅ Smooth animations

---

### Slice 13: Responsive Design
**Duration:** 3 hours
**Dependencies:** Slices 8, 9, 10

**Modify:**
- `frontend/css/styles.css` - Media queries

**Breakpoints:**
- Desktop: 1200px+
- Tablet: 768px-1199px
- Mobile: <768px

**Layouts:**
- Metrics grid: 3→2→1 columns
- Chart: full width
- Input: stack on mobile
- Touch targets: 44px minimum

**Acceptance:**
- ✅ Works on iPhone SE, iPhone 14, iPad, Desktop
- ✅ No horizontal scrolling
- ✅ Touch-friendly buttons
- ✅ Readable text at all sizes

---

### Slice 14: Performance
**Duration:** 2-3 hours
**Dependencies:** Slices 9, 10

**Optimize:**
- Chart lazy loading
- DOM batch insertions
- Minimize reflows
- Request debouncing
- Memory management

**Targets:**
- First render: <100ms
- Chart render: <500ms
- Metrics display: <200ms
- Lighthouse score: >90

**Testing:**
- Chrome DevTools Performance
- Memory profiling
- Multiple analyses (no leaks)

**Acceptance:**
- ✅ < 100ms first render
- ✅ < 500ms chart
- ✅ No memory leaks
- ✅ Smooth interactions
- ✅ Lighthouse >90

---

## Phase 4: Polish (Slices 15-16)

### Slice 15: Documentation
**Duration:** 2-3 hours
**Dependencies:** All prior slices

**Create:**
- `README.md` - Project overview
- `docs/SETUP.md` - Setup guide
- `docs/API.md` - API documentation
- `docs/TESTING.md` - Testing guide
- Update `.env.example`

**Sections:**
- Quick start (< 10 min)
- All environment variables
- API endpoint examples
- Testing instructions
- Troubleshooting

**Acceptance:**
- ✅ New dev can set up in < 10 min
- ✅ All env vars documented
- ✅ API docs with examples
- ✅ Testing instructions clear
- ✅ Includes screenshots/links

---

### Slice 16: E2E Testing
**Duration:** 3-4 hours
**Dependencies:** All prior slices

**Create:**
- `backend/tests/test_e2e.py` - E2E test suite

**Tests:**
- Full analysis flow
- All error scenarios
- Edge cases (no splits, many splits)
- Performance testing
- Browser compatibility

**Checklists:**
- Security audit
- Production checklist
- Manual test cases

**Acceptance:**
- ✅ E2E tests pass 100%
- ✅ Manual tests pass
- ✅ No security vulnerabilities
- ✅ Works in all browsers
- ✅ Rate limiting verified
- ✅ Error logging complete

---

## Testing Strategy

**Unit Tests:**
- Coverage: >90%
- Tools: pytest, pytest-asyncio
- Command: `pytest backend/tests/ -v --cov=backend`

**Integration Tests:**
- Endpoints with mocked Polygon client
- Service orchestration
- Error scenarios

**E2E Tests:**
- Complete user flows
- All error paths
- Browser compatibility

**Manual Tests:**
- Valid ticker (AAPL)
- Invalid ticker (NOTREAL)
- Malformed ticker (aapl)
- No splits scenario
- Many splits scenario
- Network disconnection
- Responsive layout
- Mobile devices
- All browsers

---

## Deployment Checkpoints

**Checkpoint 1: Backend Core (After Slice 7)**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
# Expected: Complete JSON response
```

**Checkpoint 2: Frontend Core (After Slice 10)**
- Open index.html in browser
- Submit ticker
- Verify metrics display

**Checkpoint 3: Full Integration (After Slice 14)**
- All tests pass
- Manual checklist complete
- Performance metrics met
- Error handling verified

**Checkpoint 4: Production (After Slice 16)**
- Public URL accessible
- HTTPS configured
- Environment variables set
- Monitoring enabled

---

## Risk Mitigation

**Risk 1: Polygon.io Rate Limits**
- Mitigation: Client-side caching (5-min), exponential backoff, clear messages, consider paid tier

**Risk 2: TradingView Chart Complexity**
- Mitigation: Use official examples, test early with real data, fallback to HTML table

**Risk 3: Missing Split Data**
- Mitigation: Handle null gracefully, display "No splits" message, show available metrics

**Risk 4: Browser Compatibility**
- Mitigation: Use vanilla JS, test across browsers early, well-supported APIs only

**Risk 5: Performance on Low-End Devices**
- Mitigation: Optimization slice, lazy loading, minimize DOM manipulation, test on low-end

---

## Dependencies Map

```
Slice 1
├─ Slice 2
│  ├─ Slice 4 ─ Slice 5 ─ Slice 7
│  ├─ Slice 5 ─ Slice 7
│  ├─ Slice 6 ─ Slice 7, 9
│  └─ Slice 7
├─ Slice 3
│  ├─ Slice 4, 5, 6, 7
│  └─ Slice 8 ─ Slices 9, 10, 11, 12, 13
└─ All ─ Slices 15, 16
```

---

## Success Metrics

**Technical:**
- Coverage: >90%
- API response: <3s (p95)
- Frontend render: <1s
- Zero critical bugs
- Browser compatibility: Chrome, Firefox, Safari, Edge

**User Experience:**
- Time to result: <5s
- Error rate: <1%
- Mobile parity: 100%
- Accessibility: WCAG 2.1 AA

---

**Status:** ✅ READY FOR IMPLEMENTATION
