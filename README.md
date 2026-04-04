# Gap Lens Dilution

Real-time dilution risk dashboard for active traders. Pulls SEC filing data from AskEdgar V2, displays dilution analysis alongside live TradingView charts, and surfaces top gainers from TradingView and Massive sources.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Gainers Sidebar │     │  Dilution Data   │     │  TradingView    │
│  TradingView +   │     │  Header, Risk,   │     │  Charts (4x)    │
│  Massive columns │     │  Headlines, etc. │     │  5m/15m/D/M     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                        │
         └───────────────────────┼────────────────────────┘
                                 │
                          ┌──────┴──────┐
                          │  FastAPI    │
                          │  Backend    │
                          └──────┬──────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
              AskEdgar V2   TradingView   Massive
              (dilution)    (gainers)     (gainers)
```

- **Backend**: FastAPI at `app/` — proxies AskEdgar V2 enterprise API, TradingView gainers, and Massive gainers
- **Frontend**: Next.js 16 at `frontend/` — single-page dashboard with 3-column layout
- **Charts**: TradingView Advanced Chart free embeds via CDN script injection (no API key needed)

## Running

### Backend

```bash
cd /home/d-tuned/projects/gap-lens-dilution
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

Production builds are required for Tailscale access (dev server HMR websockets fail over non-localhost).

```bash
cd frontend
npx next build
npx next start -p 3001 -H 0.0.0.0
```

Access at `http://100.70.21.69:3001` (Tailscale IP).

### Environment

Frontend API base URL is set in `frontend/.env.local`:
```
NEXT_PUBLIC_API_BASE=http://100.70.21.69:8000
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/v1/dilution/{ticker}` | Full dilution analysis from AskEdgar V2 |
| `GET /api/v1/gainers` | TradingView top gainers |
| `GET /api/v1/gainers/massive` | Massive top gainers |

## Frontend Components

| Component | Purpose |
|-----------|---------|
| `Header` | Ticker, price, float/OS/MC, risk badge, chart analysis |
| `Headlines` | SEC filings and news with filing-type badges |
| `RiskBadges` | Overall, offering, dilution risk indicators |
| `OfferingAbility` | ATM/shelf registration status |
| `InPlayDilution` | Active warrants and convertible notes |
| `Offerings` | Historical offering table |
| `GapStats` | Gap fill statistics |
| `JMT415Notes` | Analyst notes |
| `MgmtCommentary` | Management commentary |
| `Ownership` | Institutional/insider ownership |
| `TradingViewChart` | Live TradingView chart embed (CDN script injection) |
| `GainerPanel` | Scrollable gainer list with auto-refresh |
| `TickerSearch` | Ticker search bar |

## Layout

3-column layout filling the browser viewport:

1. **Left sidebar** (fixed width) — dual gainer panels (TradingView + Massive) with auto-refresh
2. **Middle column** (flex) — ticker search, dilution data components, scrollable
3. **Right column** (flex) — 4 stacked TradingView charts (5min, 15min, Daily, Monthly), no scroll, fills viewport height

## Tech Stack

- **Backend**: Python 3.12, FastAPI, httpx, Pydantic
- **Frontend**: Next.js 16, React 19, Tailwind CSS 4, TypeScript
- **Charts**: TradingView Advanced Chart (free embed widget)
- **Testing**: pytest, Playwright (Python)
- **Deployment**: Tailscale (production builds only)

## Tests

```bash
# Backend API tests
python3 -m pytest tests/test_api.py -v

# TradingView chart widget Playwright tests
python3 -m pytest tests/test_tradingview_chart.py -v
```
