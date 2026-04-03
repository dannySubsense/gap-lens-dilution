# Phase 2 UI Redesign Technical Architecture

## Document Information
- **Project**: gap-lens-dilution
- **Phase**: Phase 2 - Web UI Redesign
- **Output**: `/home/d-tuned/projects/gap-lens-dilution/specs/phase2/02-ARCHITECTURE.md`

## Overview
The Phase 2 UI redesign expands the current single-view dilution dashboard into a multi-section application displaying comprehensive dilution monitoring data. The architecture follows the existing component-based pattern while introducing new sections and enhanced data flows.

## Core Principles
1. **Component-Based Architecture**: Each UI section is a self-contained component
2. **State Management**: Centralized state handling via State class
3. **API Service Layer**: Abstracted API communication through ApiService
4. **Event-Driven Updates**: Components react to state changes and user interactions
5. **Consistent Styling**: Adheres to specified dark theme and visual specifications
6. **Extensibility**: Easy to add new sections or modify existing ones

## Component Hierarchy
```
App
├── HeaderComponent
├── TickerInputSection
├── GapAnalyzerSection
├── ShareStructureSection
├── JMT415Section
├── RiskAssessmentSection
└── HeadlinesSection
```

## Data Flow
1. User enters ticker in TickerInputSection
2. Main.js validates input and triggers data fetch
3. ApiService calls multiple AskEdgar endpoints in parallel:
   - `/v1/float-outstanding` for share structure data
   - `/v1/dilution-rating` for risk assessment data
   - `/v1/news` (filtered) for JMT415 and Headlines sections
   - Additional endpoints as needed for Gap Analyzer
4. State updates with fetched data
5. Components re-render with new data
6. Loading/error states handled globally

## Component Specifications

### 1. HeaderComponent
- **Purpose**: Displays app title and draggable handle (for desktop)
- **State**: None (static UI)
- **API Calls**: None
- **Events**: None (drag handled externally if needed)

### 2. TickerInputSection (Enhanced)
- **Purpose**: Ticker entry with loading/status indicators
- **State**: Current ticker, input state (idle/loading/error)
- **API Calls**: None (handled by Main.js)
- **Events**: 
  - `ticker-change`: When user submits ticker
  - `input-change`: As user types

### 3. GapAnalyzerSection
- **Purpose**: Shows previous close, current price, % change with color coding
- **State**: Previous close, current price, percent change
- **API Calls**: Requires new endpoint or combination (to be determined)
- **Events**: None

### 4. ShareStructureSection (Enhanced)
- **Purpose**: Displays authorized, outstanding, float shares with formatting
- **State**: Authorized, outstanding, float values
- **API Calls**: `/v1/float-outstanding`
- **Events**: None

### 5. JMT415Section
- **Purpose**: Shows dilution alert feed with expand/collapse functionality
- **State**: Array of dilution alerts, expanded state
- **API Calls**: `/v1/news` with tag="Dilution" or form_type="jmt415"
- **Events**:
  - `row-click`: When user clicks alert row
  - `toggle-expand`: When user clicks expand/collapse icon

### 6. RiskAssessmentSection
- **Purpose**: Displays risk score badge with tooltip and click-through
- **State**: Risk level (high/medium/low/n/a), risk description
- **API Calls**: `/v1/dilution-rating`
- **Events**:
  - `badge-click`: Navigate to AskEdgar risk detail page
  - `badge-hover`: Show tooltip

### 7. HeadlinesSection
- **Purpose**: Shows scrollable news feed with source tags
- **State**: Array of news items
- **API Calls**: `/v1/news` (general news, possibly excluding dilution)
- **Events**:
  - `item-click`: Open news source URL in new tab

## API Service Extensions
The existing ApiService will be extended with methods for each endpoint:
- `getFloatOutstanding(ticker)`
- `getDilutionRating(ticker)`
- `getNews(ticker, options)` where options includes tag, form_type, limit, etc.
- `getGapAnalyzerData(ticker)` - TBD based on available data
- `getAuthorizedShares(ticker)` - may need different endpoint

## State Management
The State class will be enhanced to include:
- Current ticker
- Loading states per section
- Error states per section
- Data for each section:
  - gapAnalyzer: {previousClose, currentPrice, percentChange}
  - shareStructure: {authorized, outstanding, float}
  - jmt415: [{symbol, alert, timestamp}, ...]
  - riskAssessment: {level, description}
  - headlines: [{source, headline, timestamp, url}, ...]

## Implementation Approach
1. Create new component classes following existing patterns
2. Extend ApiService with new endpoint methods
3. Enhance State class to manage section-specific data
4. Update Main.js to orchestrate data fetching and distribution
5. Implement CSS updates to match dark theme specifications
6. Add loading/skeleton states for better UX
7. Handle responsive behavior for different screen sizes

## Integration with Existing Code
- Reuse existing formatters.js for share structure formatting
- Reuse validators.js for ticker validation
- Leverage existing event handling patterns
- Maintain backward compatibility where possible
- Update index.html structure to accommodate new sections

## Performance Considerations
- Parallel API calls where possible
- Debounce ticker input to prevent excessive requests
- Cache recent ticker data
- Implement request deduplication
- Lazy-load sections as they enter viewport (if needed)

## Error Handling
- Global error boundaries per section
- Retry mechanisms for failed requests
- User-friendly error messages
- Loading states during data fetch
- Fallback UI for missing data

## Security Considerations
- API key handled by backend proxy (current /api/v1/dilution/{ticker} endpoint)
- Input validation to prevent XSS
- Safe HTML rendering in components
- CSP considerations for external links