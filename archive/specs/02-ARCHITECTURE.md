# Architecture Document: Gap Lens Dilution Phase 1

**Version:** 1.0
**Date:** 2026-03-22
**Status:** APPROVED

---

## 1. System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (Client)                         │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Frontend (Vanilla JS + HTML/CSS)              │  │
│  │                                                      │  │
│  │  Ticker Input → Dilution Display → Chart Component │  │
│  │                    ↑                                 │  │
│  │                API Client                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────┬──────────────────────────────┘
                              │ HTTPS
                              │
┌─────────────────────────────▼──────────────────────────────┐
│              Backend (FastAPI + Python)                    │
│                                                             │
│  API Routes → Business Logic → Edgar API Client            │
│                                                             │
│  ├─ Error Handling (404, 429, 5xx, network)               │
│  ├─ Request Validation                                     │
│  ├─ Response Transformation                                │
│  └─ Retry Logic with Backoff                               │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                   Ask-Edgar API                            │
│              (External Service)                             │
└────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Frontend:**
- Vanilla JavaScript (ES6+)
- HTML5 / CSS3
- TradingView Lightweight Charts v4.x
- Gap Research Design System

**Backend:**
- Python 3.10+
- FastAPI 0.104+
- Pydantic 2.x (data validation)
- httpx 0.25+ (async HTTP client)
- uvicorn (ASGI server)

---

## 2. Frontend Architecture

### Component Structure

```
frontend/
├── index.html              # Main HTML
├── css/
│   ├── main.css           # Main styles
│   ├── components.css     # Component styles
│   └── gap-design.css     # Design system
├── js/
│   ├── main.js            # App controller
│   ├── api-client.js      # Backend communication
│   ├── ticker-input.js    # Input component
│   ├── dilution-display.js # Display component
│   ├── chart-component.js # Chart integration
│   ├── error-handler.js   # Error handling
│   └── utils.js           # Utilities
└── assets/                # Static files
```

### Key Components

**Main Application (`main.js`)**
- Initializes all components
- Coordinates user interactions
- Manages data flow between components

**API Client (`api-client.js`)**
- Communicates with backend
- Handles network errors (timeout, connection issues)
- Transforms API responses

**Ticker Input (`ticker-input.js`)**
- Input field for ticker symbol
- Client-side validation
- Case normalization (to uppercase)

**Dilution Display (`dilution-display.js`)**
- Renders metrics in structured format
- Formats numbers (commas, currency, percentages)
- Handles "N/A" for missing data

**Chart Component (`chart-component.js`)**
- Integrates TradingView Lightweight Charts
- Renders historical price data
- Responsive sizing

**Error Handler (`error-handler.js`)**
- Centralized error display
- Toast notifications
- User-friendly error messages

### Frontend Data Flow

```
User Input
   ↓
Ticker Input (validates)
   ↓
API Client (fetch)
   ↓
Response Handler
   ├─ Success → Update UI (metrics + chart)
   └─ Error → Error Handler (display message)
```

---

## 3. Backend Architecture

### Project Structure

```
backend/
├── app/
│   ├── main.py           # FastAPI app
│   ├── config.py         # Configuration
│   ├── api/
│   │   ├── routes.py     # Endpoints
│   │   └── dependencies.py
│   ├── models/
│   │   ├── requests.py   # Request schemas
│   │   └── responses.py  # Response schemas
│   ├── services/
│   │   ├── dilution.py   # Business logic
│   │   └── edgar_client.py # API client
│   ├── core/
│   │   ├── errors.py     # Custom exceptions
│   │   ├── retry.py      # Retry logic
│   │   └── logging.py    # Logging setup
│   └── utils/
│       └── validators.py # Input validation
├── tests/               # Test suite
└── requirements.txt     # Dependencies
```

### API Endpoints

**GET /health**
- Health check endpoint
- Returns system status

**GET /api/dilution/{ticker}**
- Fetch dilution metrics for ticker
- Path: ticker symbol (1-5 uppercase letters)
- Response: Dilution metrics + chart data
- Errors: 404, 429, 503

### Response Schema

```
{
  "ticker": "AAPL",
  "companyName": "Apple Inc.",
  "sharesOutstanding": {
    "current": 15000000000,
    "yearAgo": 14500000000,
    "change": 500000000,
    "percentChange": 3.45
  },
  "marketCap": {
    "current": 2500000000000,
    "yearAgo": 2200000000000
  },
  "dilutionRate": 3.45,
  "chartData": [
    { "date": "2025-03-22", "sharesOutstanding": 14500000000 },
    ...
  ],
  "lastUpdated": "2026-03-22T10:30:00Z"
}
```

---

## 4. Error Handling

### Error Classification

| Error | HTTP Status | Code | Retry | User Message |
|-------|----------|------|-------|--------------|
| Ticker not found | 404 | `TICKER_NOT_FOUND` | No | "Ticker '[X]' not found. Please verify." |
| Rate limit | 429 | `RATE_LIMIT_EXCEEDED` | Wait | "Too many requests. Wait [X] seconds." |
| Server error | 500 | `INTERNAL_ERROR` | No | "Unexpected error. Try again later." |
| Service unavailable | 503 | `SERVICE_UNAVAILABLE` | Yes (60s) | "Service unavailable. Try again later." |
| Network error | N/A | `NETWORK_ERROR` | Yes (3x) | "Connection failed. Check internet." |
| Validation error | 400 | `INVALID_TICKER` | No | "Invalid format. Use 1-5 uppercase letters." |

### Error Handling Strategy

**Backend:**
- Validate ticker format (regex: `^[A-Z]{1,5}$`)
- Retry Edgar API calls (3 attempts, exponential backoff)
- Never retry 404 (ticker not found)
- Never retry 429 without waiting
- Transform all errors into standard error response

**Frontend:**
- Validate ticker client-side before API call
- Handle all HTTP status codes appropriately
- Display user-friendly error messages
- Provide retry mechanism for transient errors

---

## 5. Edgar API Client

### Responsibilities

- HTTP communication with Ask-Edgar API
- Request timeout handling (10 seconds)
- Error classification and propagation
- Retry logic with exponential backoff (3 attempts)
- Rate limit handling

### Retry Strategy

```
Attempt 1 (immediate)
  ├─ Success → return data
  └─ Failure → wait 1 second
Attempt 2 (1 second delay)
  ├─ Success → return data
  └─ Failure → wait 2 seconds
Attempt 3 (3 second delay)
  ├─ Success → return data
  └─ Failure → raise error
```

**Does NOT retry:**
- 404 (Ticker Not Found) - permanent failure
- 429 (Rate Limit) - requires client wait, handled separately
- 400 (Bad Request) - client error
- Request timeout on 3rd attempt

---

## 6. Design System Integration

### Gap Research Colors

```css
--color-primary: #1a73e8        /* Blue */
--color-error: #ea4335          /* Red */
--color-success: #34a853        /* Green */
--color-warning: #fbbc04        /* Yellow */
--color-text-primary: #202124   /* Dark gray */
--color-text-secondary: #5f6368 /* Medium gray */
--color-background: #ffffff     /* White */
--color-surface: #f8f9fa        /* Light gray */
--color-border: #dadce0         /* Border gray */
```

### Typography

- Font: Inter, -apple-system, BlinkMacSystemFont
- Body: 14px, 400 weight
- Headings: 18px, 600 weight
- Small text: 12px, 400 weight

### Component Patterns

**Input Fields:**
- Border: 1px solid --color-border
- Padding: 8px 12px
- Radius: 4px
- Focus: --color-primary border

**Buttons:**
- Padding: 8px 16px
- Radius: 4px
- Background: --color-primary
- Text: white

**Cards:**
- Border: 1px solid --color-border
- Radius: 8px
- Padding: 16px
- Shadow: 0 1px 2px rgba(0,0,0,0.05)

---

## 7. Security Considerations

### Input Validation

**Backend:**
- Ticker format: regex `^[A-Z]{1,5}$`
- Reject request if invalid
- Never pass unsanitized input to Edgar API

**Frontend:**
- Validate ticker before API call
- Prevent XSS: no `innerHTML` for user input
- Sanitize error messages

### API Security

**CORS:**
- Configure allowed origins
- Allow credentials if needed
- Restrict to GET/POST methods

**Headers:**
- Use HTTPS only
- Set `Content-Type: application/json`
- Set `X-Content-Type-Options: nosniff`

**Secrets:**
- Store Ask-Edgar API key in environment variables
- Never commit `.env` file
- Use `.env.example` for documentation

---

## 8. Performance Targets

| Metric | Target |
|--------|--------|
| API Response Time | < 2 seconds (p95) |
| Page Load Time | < 1 second |
| Chart Render Time | < 500ms |
| Input Validation | < 100ms |

### Optimization Strategies

**Backend:**
- Async/await for non-blocking I/O
- Connection pooling for httpx
- Efficient data transformation

**Frontend:**
- Minimal JavaScript bundle
- Lazy-load TradingView library
- Debounce ticker input (300ms)

---

## 9. Deployment

### Development Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
# Serve static files (index.html, css/, js/)
# Access: http://localhost:3000
```

### Environment Variables

**Backend (.env):**
```
EDGAR_API_BASE_URL=https://api.ask-edgar.com
EDGAR_API_KEY=sk_live_...
LOG_LEVEL=INFO
```

**Frontend (hardcoded or config.js):**
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

---

## 10. Testing Strategy

### Backend Unit Tests
- Data transformation logic
- Input validation
- Error handling flows

### Backend Integration Tests
- API endpoints with mocked Edgar client
- Retry logic
- Error responses

### Frontend Manual Testing
- All user stories
- All error scenarios
- Browser compatibility

---

## 11. Logging

**Backend Logging:**
- Request start/end with duration
- API calls to Edgar (success/failure)
- Errors with full context
- Rate limits and retries

**Log Format:**
```json
{
  "timestamp": "2026-03-22T10:30:00Z",
  "level": "ERROR",
  "message": "Edgar API error",
  "ticker": "AAPL",
  "status_code": 503,
  "duration_ms": 5000
}
```

---

## 12. Future Integration Path

### Current (Phase 1)
- Standalone FastAPI app
- Standalone HTML/JS frontend
- Self-contained deployment

### Future (Phase 2+)
- Extract backend as reusable module
- Export frontend as widget component
- Integrate into Gap Research platform
- Share authentication/design system

**Design Principles Supporting Integration:**
- Clear API contracts
- Configurable endpoints
- Modular component structure
- No hard-coded dependencies

---

## 13. Dependencies

### Backend (requirements.txt)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
httpx==0.25.1
python-dotenv==1.0.0
```

### Frontend
- TradingView Lightweight Charts (CDN)
- No build tools required
- No npm dependencies

---

## 14. Success Criteria

✅ All 7 user stories implemented
✅ All error cases handled (404, 429, 5xx, network)
✅ Design system compliance verified
✅ < 2s API response time (p95)
✅ Zero unhandled exceptions
✅ Standalone deployment working

---

**Status:** READY FOR UI SPECIFICATION
**Next Step:** @ui-spec-writer creates detailed UI specification
