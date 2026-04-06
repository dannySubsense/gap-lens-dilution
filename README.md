# Gap Lens Dilution

Real-time dilution risk dashboard for active traders. Pulls SEC filing data from AskEdgar V2, displays dilution analysis alongside live TradingView charts, and surfaces top gainers from three independent sources.

Adapted from [jasontange/Top-Gainers-Dilution-Monitor-V2-Public](https://github.com/jasontange/Top-Gainers-Dilution-Monitor-V2-Public), which is a desktop application (Electron/WPF). This project reimplements the concept as a full-stack web app (FastAPI + Next.js). Key differences from the original:

- **Web-native** — runs in the browser
- **3 gainer sources** — TradingView, Massive, and FMP side by side (original uses a single source)
- **2-4 configurable live charts** — stacked in one view via TradingView embeds, with chart count selector
- **AskEdgar V2 enterprise API** — full dilution analysis with risk badges, offering ability, in-play dilution, gap stats, and analyst notes

## Screenshots

![Dashboard with dilution data and charts](screenshots/gap-lens-dilution-1.png)

![Dashboard scrolled to show offering ability, warrants, offerings, and gap stats](screenshots/gap-lens-dilution-2.png)

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  Toolbar  │  Logo + Chart Count + Add to Watchlist + Settings        │
├─────────────┬──────────────┬───────────────────────┬─────────────────┤
│   Gainers   │  TradingView │  Dilution Data        │  Watchlist      │
│   TV +      │  Charts      │  Header, Risk, etc    │  Column         │
│   Massive + │  (2-4x)      │                       │                 │
│   FMP       │              │                       │                 │
└─────────────┴──────────────┴───────────────────────┴─────────────────┘
                                    │
                             ┌──────┴──────┐
                             │  FastAPI    │
                             │  Backend    │
                             └──────┬──────┘
                                    │
                       ┌────────────┼────────────┐
                       │            │            │
                 AskEdgar V2   TradingView   Massive / FMP
                 (dilution)    (gainers)     (gainers)
```

- **Backend**: FastAPI at `app/` — proxies AskEdgar V2 enterprise API, TradingView gainers, Massive gainers, and FMP gainers
- **Frontend**: Next.js 16 at `frontend/` — single-page dashboard with 4-column layout + top toolbar
- **Charts**: TradingView Advanced Chart free embeds via CDN script injection (no API key needed)

## Running

### Backend

```bash
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

Backend API keys in `.env`:
```
ASKEDGAR_API_KEY=<your-key>
MASSIVE_API_KEY=<your-key>
FMP_API_KEY=<your-key>
```

Frontend API base URL in `frontend/.env.local`:
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
| `GET /api/v1/gainers/fmp` | FMP top gainers |

## Frontend Components

| Component | Purpose |
|-----------|---------|
| `Header` | Ticker, price, float/OS/MC, risk badge, chart analysis |
| `Headlines` | SEC filings and news with filing-type badges, collapsible with chevron toggle |
| `RiskBadges` | Overall, offering, dilution risk indicators |
| `OfferingAbility` | ATM/shelf registration status |
| `InPlayDilution` | Active warrants and convertible notes |
| `Offerings` | Historical offering table |
| `GapStats` | Gap fill statistics |
| `JMT415Notes` | Analyst notes |
| `MgmtCommentary` | Management commentary |
| `Ownership` | Institutional/insider ownership |
| `TradingViewChart` | Live TradingView chart embed (CDN script injection), independent mode with per-chart ticker dropdown |
| `GainerPanel` | Scrollable gainer list with auto-refresh, toggleable visibility via settings |
| `TickerSearch` | Ticker search bar |
| `Toolbar` | Top toolbar with app branding, chart count selector, add-to-watchlist, settings gear |
| `SettingsModal` | Gainer column visibility toggles, linked/independent chart mode |
| `WatchlistColumn` | 4th column with tracked tickers, multi-select delete |
| `WatchlistCard` | Single watchlist entry with gainer-style card layout |
| `AppSettingsContext` | Settings and watchlist state provider with localStorage persistence |

## Layout

4-column layout filling the browser viewport:

1. **Top toolbar** (fixed height) — app logo, chart count selector (2/3/4), add-to-watchlist button, settings gear
2. **Left sidebar** (fixed width, toggleable) — gainer panels (TradingView + Massive + FMP) with auto-refresh, individually hideable
3. **Middle column** (flex) — 2-4 stacked TradingView charts, configurable count, linked or independent mode
4. **Right column** (flex) — ticker search, dilution data components, collapsible news panel, scrollable
5. **Watchlist column** (fixed width) — tracked tickers with multi-select delete

## Tech Stack

- **Backend**: Python 3.12, FastAPI, httpx, Pydantic
- **Frontend**: Next.js 16, React 19, Tailwind CSS 4, TypeScript
- **Charts**: TradingView Advanced Chart (free embed widget)
- **Data**: AskEdgar V2 (dilution), TradingView (gainers), Massive/Polygon (gainers), FMP (gainers)
- **Testing**: pytest, Playwright (Python)
- **Deployment**: Tailscale (production builds only)

## Tests

```bash
# Backend API tests
python3 -m pytest tests/test_api.py -v

# TradingView chart widget Playwright tests
python3 -m pytest tests/test_tradingview_chart.py -v

# Full Playwright QC suite (requires both services running)
python3 -m pytest tests/test_playwright_qc.py -v
```
