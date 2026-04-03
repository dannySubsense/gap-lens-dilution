# Ask Edgar Dilution Monitor - Phase 2 Architecture

## Overview
This document maps the Phase 2 requirements to AskEdgar API endpoints and identifies what needs to be added to the gap-lens-dilution web application.

## API Endpoint Mapping

Based on the requirements analysis, the application uses the following AskEdgar API endpoints:

### 1. Dilution Rating API
- **Endpoint**: `https://eapi.askedgar.io/enterprise/v1/dilution-rating`
- **Parameters**: `ticker`, `offset=0`, `limit=10`
- **Data Used For**:
  - Overall Risk Badge (`overall_offering_risk`)
  - Info Line (sector, country) - *partial*
  - Risk Badges Card (all risk categories: `offering_ability`, `dilution`, `offering_frequency`, `cash_need`, `warrant_exercise`)
  - Offering Ability Card (`offering_ability_desc`)
  - Management Commentary Card (`mgmt_commentary`)

### 2. Float/Outstanding API
- **Endpoint**: `https://eapi.askedgar.io/enterprise/v1/float-outstanding`
- **Parameters**: `ticker`, `offset=0`, `limit=100`
- **Data Used For**:
  - Info Line (float, outstanding shares, market cap, sector, country)

### 3. News & Filings API
- **Endpoint**: `https://eapi.askedgar.io/enterprise/v1/news`
- **Parameters**: `ticker`, `offset=0`, `limit=100`
- **Data Used For**:
  - Feed Card (News & Grok) (`news`, `8-K`, `6-K`, `grok` filings)
  - JMT415 Previous Notes Card (`jmt415` filings)

### 4. Dilution Data API
- **Endpoint**: `https://eapi.askedgar.io/enterprise/v1/dilution-data`
- **Parameters**: `ticker`, `offset=0`, `limit=40`
- **Data Used For**:
  - In Play Dilution Card (warrants and convertibles data)

### 5. Screener/Price API
- **Endpoint**: `https://eapi.askedgar.io/v1/screener`
- **Parameters**: `ticker`, `limit=1`
- **Data Used For**:
  - In Play Dilution Card (current price for in-the-money calculations)

## Feature-to-Endpoint Mapping

### Header Section
- **Ticker Display**: Platform detection (window scraping) - No API needed
- **Overall Risk Badge**: Dilution Rating API (`overall_offering_risk`)
- **Info Line**: 
  - Float/Outstanding API (`float`, `outstanding`, `market_cap_final`)
  - Dilution Rating API (`sector`, `country`)

### Content Cards

#### 1. Waiting State
- No data required

#### 2. Loading State
- Ticker from platform detection - No API needed

#### 3. No Data State
- Ticker from platform detection - No API needed

#### 4. Feed Card (News & Grok)
- News & Filings API (`news`, `8-K`, `6-K`, `grok`)

#### 5. Risk Badges Card
- Dilution Rating API (`overall_offering_risk`, `offering_ability`, `dilution`, `offering_frequency`, `cash_need`, `warrant_exercise`)

#### 6. Offering Ability Card
- Dilution Rating API (`offering_ability_desc`)

#### 7. In Play Dilution Card
- Dilution Data API (warrants and convertibles data)
- Screener/Price API (current price for ITM calculations)

#### 8. JMT415 Previous Notes Card
- News & Filings API (`jmt415` filings)

#### 9. Management Commentary Card
- Dilution Rating API (`mgmt_commentary`)

## Web Application Requirements

Based on the mapping, the gap-lens-dilution web app needs to implement:

### API Integration Layer
1. Service functions for each AskEdgar endpoint:
   - `getDilutionRating(ticker)`
   - `getFloatOutstanding(ticker)`
   - `getNewsAndFilings(ticker)`
   - `getDilutionData(ticker)`
   - `getCurrentPrice(ticker)`

### Data Processing Components
1. Header Component:
   - Displays ticker (from props/state)
   - Overall risk badge (from dilution rating)
   - Info line (combines float data and dilution rating sector/country)

2. Feed Card Component:
   - Renders news, 8-K, 6-K, grok items with source stripes
   - Clickable rows opening source URLs

3. Risk Badges Component:
   - Horizontal row of 6 color-coded badges
   - Each badge clickable to open AskEdgar dilution page

4. Offering Ability Component:
   - Parses and displays offering ability description
   - Color-codes capacity-related items

5. In Play Dilution Component:
   - Warrants and convertibles sections
   - Price-based color coding (ITM/OTM)
   - Clickable rows

6. JMT415 Notes Component:
   - Lists previous notes with filed dates

7. Management Commentary Component:
   - Displays commentary text with word wrapping

### State Management
- Ticker state (updated via platform detection integration)
- Loading states for each data type
- Error handling for API failures
- Data caching to minimize redundant calls

### UI/UX Implementation
- Responsive, dark-themed design matching desktop specifications
- Draggable interface for repositioning
- Auto-scroll for overflow content
- Hover indicators on clickable elements
- Consistent spacing and padding (8px outer, 6px between cards)

### Platform Detection Integration
- Web-based equivalent of window monitoring (to be determined based on web app context)
- May require manual ticker entry or integration with trading platform web versions

### Styling & Theme
- Color scheme matching desktop app:
  - Background: `#0D1014`
  - Card backgrounds: `#151A20`
  - Row backgrounds: alternating `#1B2128` / `#181D24`
  - Accent: `#63D3FF`
  - Risk level colors as specified

### Technical Considerations
- Environment variables for API keys
- Loading states and error boundaries
- Responsive design for various screen sizes
- Accessibility considerations (color contrast, keyboard navigation)