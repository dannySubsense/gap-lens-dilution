# Gap Lens Dilution

A web-based stock dilution risk analysis dashboard powered by Ask-Edgar API and Financial Modeling Prep (FMP).

## Overview

Gap Lens Dilution provides real-time dilution risk metrics and historical price visualization for publicly traded companies. Built with FastAPI backend and vanilla JavaScript frontend.

## Features

- **Dilution Risk Analysis** - Overall risk, offering ability, cash need, dilution level
- **Share Structure** - Float, outstanding shares, insider/institutional ownership
- **Historical Charts** - TradingView Lightweight Charts with OHLC data
- **Error Handling** - Graceful handling of API failures, rate limits, invalid tickers

## Tech Stack

- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Charts:** TradingView Lightweight Charts
- **Data Sources:**
  - Ask-Edgar API (dilution metrics)
  - Financial Modeling Prep (FMP) Ultimate (price data)

## Quick Start

1. Clone the repository
2. Copy `.env.example` to `.env` and add your API keys:
   - `ASK_EDGAR_API_KEY` - from askedgar.io
   - `FMP_API_KEY` - from financialmodelingprep.com
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python main.py`
5. Open http://localhost:8000

## Project Structure

```
gap-lens-dilution/
├── specs/              # Specification documents
│   ├── 01-REQUIREMENTS.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-UI-SPEC.md
│   ├── 04-ROADMAP.md
│   └── 05-REVIEW.md
├── app/                # Application code
│   ├── main.py
│   ├── api/
│   ├── services/
│   └── static/
├── tests/              # Test suite
└── README.md
```

## Spec Documents

This project follows a spec-forge methodology. All specifications are in the `specs/` directory:

1. **Requirements** - User stories, acceptance criteria, constraints
2. **Architecture** - System design, component structure, data flow
3. **UI Spec** - Layouts, interactions, error states
4. **Roadmap** - 6-slice implementation plan
5. **Review** - Spec quality assessment

## Phase 1 Scope

- Single ticker analysis
- Manual ticker input
- Static data display (no real-time updates)
- Local development deployment

## Out of Scope (Future Phases)

- Live data feeds
- Multi-ticker comparison
- User authentication
- Mobile app
- Data export

## License

MIT
