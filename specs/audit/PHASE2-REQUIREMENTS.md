# Ask Edgar Dilution Monitor - Phase 2 Requirements

## Overview
This document specifies the features and functionality of the Ask Edgar Dilution Monitor desktop application based on analysis of the source code (`das_monitor.py`) and README.md.

## Core Purpose
A real-time desktop overlay that monitors trading platforms (DAS Trader Pro, thinkorswim) for ticker changes and automatically displays dilution risk data from the Ask Edgar API.

## Supported Platforms
- **OS**: Any (web-based)
- **Browsers**: Modern browsers (Chrome, Firefox, Safari, Edge)
- **API Access**: Requires Ask Edgar API trial key

## UI/UX Features

### General Appearance
- Dark-themed, always-on-top overlay panel
- Positioned alongside trading platform
- Updates automatically when ticker changes
- Resizable window with minimum dimensions (400x300)
- Default size: 480x620 pixels at position (50,50)
- Draggable header for repositioning

### Visual Design Elements
- **Color Scheme**:
  - Background: `#0D1014` (dark blue-gray)
  - Card backgrounds: `#151A20` (slightly lighter)
  - Row backgrounds: `#1B2128` / `#181D24` (alternating)
  - Borders: `#232A33` (outer), `#20262E` (inner)
  - Foreground: `#E6EAF0` (light gray), `#8B949E` (dimmed), `#B7C0CC` (info)
  - Accent: `#63D3FF` (bright cyan-blue)
- **Risk Level Colors**:
  - High: `#A93232` (red)
  - Medium: `#B96A16` (orange)
  - Low: `#2F7D57` (green)
  - N/A: `#4A525C` (gray)
- **Font Styles**:
  - Ticker: Segoe UI Semibold, 24pt
  - Header: Segoe UI Semibold, 13pt
  - UI Bold: Segoe UI Semibold, 10pt
  - UI Regular: Segoe UI, 10pt
  - Mono: Consolas, 9pt
  - Mono Bold: Consolas, 9pt bold

### Interactive Elements
- **Draggable Interface**: Header card can be clicked and dragged to reposition window
- **Click-to-Open Links**: 
  - Risk badges link to Ask Edgar dilution page for ticker
  - News items link to source documents/articles
  - Entire feed rows are clickable when URL available
- **Hover Indicators**: Cursor changes to hand for clickable elements
- **Auto-Scroll**: Content area scrolls when content exceeds window size

## Data Display Sections

### Header Section
- **Ticker Display**: Large, prominent display of current stock ticker (e.g., "AAPL")
- **Overall Risk Badge**: Shows "RISK: [LEVEL]" with color-coded background based on risk level
- **Info Line**: Displays float/outstanding shares, market cap, sector, and country when float data available

### Content Cards (Scrollable)

#### 1. Waiting State
Displayed when no ticker is detected:
- Text: "Load a ticker in DAS or thinkorswim\nto see dilution data here."
- Centered, muted text

#### 2. Loading State
Displayed while fetching data for new ticker:
- Ticker shown in header
- "Loading..." status
- "Fetching data for [TICKER]..." message

#### 3. No Data State
Displayed when API returns no data for ticker:
- "NO DATA" badge in header
- "No dilution data available for [TICKER]." message

#### 4. Feed Card (News & Grok)
Displayed when news or Grok data available:
- **Source Stripes**: Color-coded left column indicating source type
  - News: `#1F8FB3` (blue) with "NEWS" label
  - 8-K/6-K: `#A85C14` (orange) with "8-K"/"6-K" label
  - Grok: `#7B3FA0` (purple) with "GROK" label
- **Content Area**:
  - Date (when available)
  - Headline/truncated summary (wraps, limited to ~240 chars for Grok)
  - Entire row clickable to open source URL

#### 5. Risk Badges Card
Displayed when dilution data available:
- Horizontal row of color-coded badges:
  - Overall Risk
  - Offering Ability
  - Dilution Level
  - Offering Frequency
  - Cash Need
  - Warrant Exercise
- Each badge shows label and level (e.g., "Overall Risk: High")
- Background color corresponds to risk level
- Entire card clickable to open Ask Edgar dilution page for ticker

#### 6. Offering Ability Card
Displayed when offering ability description available:
- Section header: "Offering Ability"
- Vertically stacked items parsed from description string
- Color-coded segments:
  - Pending S-1/F-1: Green (`#4CAF50`)
  - Shelf/ATM/Equity Line Capacity: 
    - Green if >$0.00 (`#4CAF50`)
    - Red if $0.00 (`#FF4444`)
  - Other items: Default foreground color
- Bold font for capacity-related items

#### 7. In Play Dilution Card
Displayed when warrants or convertibles near current price:
- Section header: "In Play Dilution"
- Two subsections:
  - **WARRANTS** (yellow label: `#FFD600`)
  - **CONVERTIBLES** (yellow label: `#FFD600`)
- Each item displays:
  - Details/truncated description
  - Remaining amount (formatted as M/K)
  - Strike/conversion price
  - Filed date
  - Color-coded price indicator:
    - Green (`#4CAF50`) if in-the-money (strike/conv price ≤ stock price)
    - Orange (`#FF9800`) if out-of-the-money
  - Entire row clickable to open source URL or Ask Edgar dilution page

#### 8. JMT415 Previous Notes Card
Displayed when JMT415 notes available:
- Section header: "JMT415 Previous Notes"
- Alternating row backgrounds (`#1B2128` / `#181D24`)
- Each note shows:
  - Filed date (YYYY-MM-DD)
  - Note text/summary
  - Monospace date, regular text note
  - Text wrapping with reflow on resize

#### 9. Management Commentary Card
Displayed when management commentary available:
- Section header: "Mgmt Commentary"
- Text content with word wrapping
- Reflows on container resize

## Data Sources & API Endpoints

The application fetches data from multiple Ask Edgar API endpoints:

1. **Dilution Rating** (`DILUTION_API_URL`)
   - Endpoint: `https://eapi.askedgar.io/enterprise/v1/dilution-rating`
   - Parameters: ticker, offset=0, limit=10
   - Returns: overall_offering_risk, offering_ability, dilution, offering_frequency, cash_need, warrant_exercise, offering_ability_desc, mgmt_commentary

2. **Float/Outstanding** (`FLOAT_API_URL`)
   - Endpoint: `https://eapi.askedgar.io/enterprise/v1/float-outstanding`
   - Parameters: ticker, offset=0, limit=100
   - Returns: float, outstanding, market_cap_final, sector, country

3. **News & Filings** (`NEWS_API_URL`)
   - Endpoint: `https://eapi.askedgar.io/enterprise/v1/news`
   - Parameters: ticker, offset=0, limit=100
   - Returns: news, 8-K, 6-K, grok, jmt415 filings with summary, title, url, document_url, created_at, filed_at

4. **Dilution Data** (`DILDATA_API_URL`)
   - Endpoint: `https://eapi.askedgar.io/enterprise/v1/dilution-data`
   - Parameters: ticker, offset=0, limit=40
   - Returns: warrants data (warrants_exercise_price, warrants_remaining) and convertibles data (conversion_price, underlying_shares_remaining)

5. **Screener/Price** (`SCREENER_API_URL`)
   - Endpoint: `https://eapi.askedgar.io/v1/screener`
   - Parameters: ticker, limit=1
   - Returns: current price for in-the-money calculations

## Platform Detection Mechanics

### DAS Trader Pro
- **Montage Windows**: Matches pattern `^[A-Z]{1,5}\s+\d` (e.g., "AAPL     0 -- 0     Company Name...")
  - Extracts ticker as first whitespace-delimited token
- **Chart Windows**: Matches pattern `^[A-Z]{1,5}--` (e.g., "AAPL--5 Minute--")
  - Extracts ticker as portion before first "--"
- **Detection Method**: Polls all visible windows every `POLL_INTERVAL` (1.0 seconds)
- **Change Detection**: Compares current window titles to previous poll to detect ticker changes

### thinkorswim
- **Chart Windows**: Looks for "thinkorswim" in title and " - Charts - " substring
  - Format: `"PRSO, MOBX, TURB - Charts - 61612650SCHW Main@thinkorswim [build 1990]"`
  - Extracts ticker portion before " - Charts - ", splits by comma
- **Limitations**: 
  - Only detects *detached* chart windows (embedded charts in main ToS window not supported)
  - Switching between existing chart tabs doesn't trigger change (all tickers always in title)
  - Best results with detached windows and entering new tickers

### Change Detection Algorithm
1. Poll DAS montage/windows and ToS chart windows every second
2. For DAS: Track hwnd → ticker mapping, detect when ticker changes for same hwnd or new hwnd appears
3. For ToS: Track hwnd → [tickers] mapping, detect new tickers appearing in same hwnd or new hwnd
4. On ticker change: Show loading state, fetch all data in background thread, update UI on completion

## Technical Implementation

### Architecture
- FastAPI backend
- Vanilla JavaScript frontend
- HTTP API calls to AskEdgar endpoints
- Environment variables for configuration

### Key Components
1. **Configuration**: API keys and endpoints loaded from environment/.env file
2. **Window Monitoring**: 
   - `find_montage_windows()`: Detects DAS windows
   - `find_tos_tickers()`: Detects thinkorswim windows
3. **API Functions**:
   - `fetch_dilution_data()`, `fetch_float_data()`, `fetch_news_and_grok()`, `fetch_last_price()`, `fetch_in_play_dilution()`
4. **UI Class** (`DilutionOverlay`):
   - Tkinter root window with `-topmost` attribute
   - Header with drag-and-drop functionality
   - Scrollable canvas-based content area
   - Methods for each display state (`_show_waiting`, `_show_loading`, `_show_no_data`, `_show_data`)
   - Helper methods for creating UI components (cards, badges, feed items, etc.)
5. **Monitor Thread**: Background thread polling for ticker changes
6. **Fetch Thread**: Background thread for API calls when ticker changes

### Styling & Layout
- Consistent padding and spacing (8px outer, 6px between cards)
- Card-based layout with borders and subtle elevation
- Responsive text wrapping with `<Configure>` event bindings
- Cursor indicators for interactive elements
- Text truncation with ellipsis for lengthy content

### Error Handling
- API call exceptions caught and logged to console
- Missing API key results in startup error message
- No data available state shown when APIs return empty results
- Graceful degradation when optional data sections unavailable

## Customization Options
As noted in README, the single-file Python structure allows easy modification:

### Via Geometry
- Window size/position: `self.root.geometry("480x620+50+50")`

### Via Constants
- Colors: Defined at top of file (BG, BG_CARD, ACCENT, RISK_BG, etc.)
- Fonts: Defined near top (FONT_UI, FONT_HEADER, etc.)
- Poll speed: `POLL_INTERVAL = 1.0` (seconds)
- News count: Limited in `fetch_news_and_grok()` function

### Browser Extension
- Future consideration: Browser extension for automatic ticker detection from trading platforms

## Data Formatting Utilities
- `fmt_millions()`: Formats large numbers as M (millions) or K (thousands)
- `risk_bg()`: Returns background color based on risk level string
- `extract_headline()`: Pulls headline from API item (title or HEADLINE: prefixed summary)
- Date formatting: Truncates ISO timestamps to YYYY-MM-DD HH:MM

## Security Considerations
- API key stored in `.env` file (not checked into git)
- No data persistence - all data fetched fresh on ticker change
- Web links open in system default browser via `webbrowser.open()`
- No external dependencies beyond standard library and listed packages

## Limitations & Known Issues
- Windows-only due to win32gui dependency
- thinkorswim only works with detached chart windows
- API rate limits not handled (reliant on request timeouts)
- No offline caching or data persistence
- Single ticker focus - displays data for most recently detected ticker
- No manual ticker entry or search functionalityry or search functionality
- No manual ticker entry or search functionalityry or search functionality