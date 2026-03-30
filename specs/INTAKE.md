# Gap Lens Dilution — Intake Notes

**Project:** gap-lens-dilution  
**Date:** 2026-03-22  
**Status:** Planning complete, ready for spec phase  
**Prepared by:** Danny + Major Tom  
**Hand-off to:** Claude Code (`/spec-start`)

---

## Project Overview

Web-based stock dilution risk analysis dashboard. A web adaptation of the Ask-Edgar Dilution Monitor desktop overlay.

**Phase 1 Scope:** Manual ticker input → Ask-Edgar API → static display + TradingView chart  
**Phase 2 (Future):** Live data feed (IBKR or FMP Ultimate)  
**Phase 3 (Future):** AI stock analyst agent (BYO key)

**Architecture:** Standalone FastAPI app now, integration module for Gap Research later  
**Visual Language:** Gap Research design system (colors, typography, card layouts)

---

## Core Requirements

### Functional
- **Ticker Input:** Single ticker at a time (text field, user types symbol)
- **Ask-Edgar Integration:** Fetch dilution risk data from API
- **Display:** Risk ratings, float/shares, cash runway, ownership percentages
- **TradingView Chart:** Historical price chart (chart only, no overlays for Phase 1)
- **Error Handling:** Invalid ticker, rate limit, API failures, network errors

### Technical
- **Backend:** FastAPI (Python)
- **Frontend:** Vanilla JS (no React/Vue build step)
- **Charts:** TradingView Lightweight Charts
- **Styling:** Gap Research CSS variables, Space Grotesk typography
- **API Key:** Environment variable (`.env`), never committed

---

## Data Model (Ask-Edgar API)

**Key Endpoints:**
- `GET /v1/dilution-data/{ticker}` — Core dilution metrics
- `GET /v1/float-outstanding/{ticker}` — Share structure

**Priority Fields to Display:**
| Field | Source | Description |
|-------|--------|-------------|
| `overall_offering_risk` | dilution-data | Composite risk score |
| `offering_ability` | dilution-data | Can they raise quickly? |
| `dilution` | dilution-data | Dilution risk level |
| `cash_need` | dilution-data | Cash runway risk |
| `cash_remaining_months` | dilution-data | Runway in months |
| `estimated_cash` | dilution-data | Cash on hand |
| `cash_burn` | dilution-data | Monthly burn rate |
| `float` | float-outstanding | Float shares |
| `outstanding` | float-outstanding | Outstanding shares |
| `market_cap_final` | float-outstanding | Market cap |
| `insider_percent` | float-outstanding | Insider ownership % |
| `institutions_percent` | float-outstanding | Institutional ownership % |

**Risk Color Coding:**
- Green: Low risk (`#36d29a` or `#44ff44`)
- Orange: Medium risk (`#f7b731`)
- Red: High risk (`#ff6b6b` or `#ff4444`)

---

## Visual Design System

**Colors (from Gap Research):**
```css
--bg: #0e111a        /* Main background */
--bg-alt: #141a24    /* Alternate background */
--card: #1b2230      /* Card backgrounds */
--accent: #ff4fa6    /* Primary accent (pink) */
--text: #eef1f8      /* Primary text */
--muted: #9aa7c7     /* Secondary text */
--stroke: #2a3447    /* Borders */
--success: #36d29a   /* Positive/green */
--warning: #f7b731   /* Warning/orange */
```

**Typography:**
- Primary: `Space Grotesk`
- Monospace: `JetBrains Mono` (for numbers/data)

**Layout Patterns:**
- Hero section with title + meta cards
- KPI grid for metrics
- Card-based panels with subtle borders
- Responsive grid layout

---

## Error Handling Requirements

| Error | API Status | User Message |
|-------|-----------|--------------|
| Invalid ticker | 404 | "Ticker not found" |
| Rate limit | 429 | "Rate limit reached, try again later" |
| API failure | 5xx | "Service temporarily unavailable" |
| Network error | — | "Connection failed, check internet" |

---

## API Credentials

**Base URL:** `https://eapi.askedgar.io/v1`  
**API Key:** `ask-live-48767ebd773d2f821b5748ea5c788deed38969eb42039048b297e3a44b557d2d`  
**Rate Limit:** 50 unique tickers/day per endpoint

---

## Out of Scope (Phase 1)

- Live data feed (IBKR/FMP) — Phase 2
- AI analyst agent — Phase 3
- Dilution overlay on chart — Phase 2
- Multiple tickers simultaneously
- User authentication
- Database persistence

---

## References

- **Ask-Edgar GitHub:** https://github.com/jasontange/Ask-Edgar-Dilution-Monitor-Public
- **Ask-Edgar API Docs:** `/home/d-tuned/life/resources/AlgoTradingIdeas/ask-edgar/api-docs.json`
- **Gap Research Styles:** `/home/d-tuned/Gap Research/app/static/styles.css`
- **TradingView Charts:** Already in Gap Research at `/static/vendor/lightweight-charts.standalone.production.js`

---

**END OF INTAKE NOTES**
