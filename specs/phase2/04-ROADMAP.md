# Phase 2 Implementation Roadmap
## Ask Edgar Dilution Monitor - Web UI Redesign

---

## Overview

This roadmap breaks the Phase 2 redesign into 10 ordered implementation slices. Each slice is independently testable with clear done criteria and explicit file specifications.

---

## Slice 1: Design System & CSS Foundation

**Purpose**: Establish the global visual language - colors, typography, spacing, and utility classes.

**Dependencies**: None (foundation slice)

**Files**:

| Action | File | Description |
|--------|------|-------------|
| NEW | `styles/variables.css` | CSS custom properties for colors, typography, spacing |
| NEW | `styles/base.css` | Reset, box-sizing, body/html base styles |
| NEW | `styles/utilities.css` | Helper classes for layout, text colors, margins |
| MODIFY | `index.html` | Link new CSS files, update meta tags |

**Test Criteria**:
- [ ] All CSS variables render correctly (inspect in dev tools)
- [ ] Dark background (#1a1a1a) displays on body
- [ ] Typography renders with Consolas for data, system UI for text
- [ ] Utility classes (.text-primary, .text-secondary, .card, etc.) work in isolation
- [ ] No console errors from CSS

**Done Definition**: Design system CSS loads without errors; basic card renders with correct colors.

---

## Slice 2: Header Component & Layout Shell

**Purpose**: Create the draggable header and overall app layout structure.

**Dependencies**: Slice 1 complete

**Files**:

| Action | File | Description |
|--------|------|-------------|
| NEW | `components/HeaderComponent.js` | Header with logo, title, drag handle |
| NEW | `styles/components/header.css` | Header-specific styles |
| MODIFY | `index.html` | Add header container div |
| MODIFY | `js/main.js` | Instantiate HeaderComponent on load |
| NEW | `js/drag-handler.js` | Window drag functionality (for desktop) |

**Test Criteria**:
- [ ] Header renders with "ASK EDGAR" (white) + "DILUTION MONITOR" (cyan)
- [ ] Header is at correct height (48px) with proper background (#2d2d2d)
- [ ] Logo/icon displays at 24x24px on left
- [ ] Bottom border renders (1px solid #444)
- [ ] Drag functionality works (if desktop context)
- [ ] Header remains fixed at top on scroll

**Done Definition**: Header visible, properly styled, interactive elements respond to hover.

---

## Slice 3: Ticker Input Section (Enhanced)

**Purpose**: Build the enhanced ticker input with states, validation, and loading indicators.

**Dependencies**: Slice 2 complete

**Files**:

| Action | File | Description |
|--------|------|-------------|
| NEW | `components/TickerInputSection.js` | Enhanced input with validation |
| NEW | `styles/components/ticker-input.css` | Input-specific styles |
| MODIFY | `js/validators.js` | Add ticker format validation (1-5 alphanumeric) |
| MODIFY | `index.html` | Add ticker section container |
| MODIFY | `js/main.js` | Wire up input events |

**Test Criteria**:
- [ ] Input auto-converts to uppercase on typing
- [ ] Border becomes cyan on focus (#00bcd4)
- [ ] Search button displays with magnifying glass icon
- [ ] Enter key submits ticker
- [ ] "LOADING" state shows spinner after submit
- [ ] Validation rejects <1 or >5 characters
- [ ] Label "ENTER TICKER FOR DILUTION DATA" displays in gray, uppercase
- [ ] Placeholder "AAPL" visible when empty

**Done Definition**: User can type ticker, submit triggers loading state, validation works.

---

## Slice 4: Share Structure Section (Enhanced)

**Purpose**: Display authorized, outstanding, and float shares with M/K notation.

**Dependencies**: Slice 3 complete

**Files**:

| Action | File | Description |
|--------|------|-------------|
| MODIFY | `components/ShareStructureSection.js` | Enhanced with 3-row layout |
| NEW | `styles/components/share-structure.css` | Row layouts, flexbox alignment |
| MODIFY | `js/formatters.js` | fmt_millions formatter for M/K/B notation |
| MODIFY | `index.html` | Update share structure container |

**Test Criteria**:
- [ ] 3 rows display: Authorized, Outstanding, Float
- [ ] Labels left-aligned in gray text
- [ ] Values right-aligned in white monospace
- [ ] Correct M/K/B formatting:
  - Values <1K: show exact
  - Values 1K-1M: show as "XXX.XK"
  - Values 1M-1B: show as "XXX.XM"
  - Values >1B: show as "X.XB"
- [ ] Section has header "Share Structure"
- [ ] Proper spacing between rows (12px)

**Done Definition**: All 3 share values display with correct formatting; aligns to right.

---

## Slice 5: JMT415 Section (Dilution Alert Feed)

**Purpose**: Scrollable table of dilution alerts with color-coded row highlights.

**Dependencies**: Slice 4 complete

**Files**:

| Action | File | Description |
|--------|------|-------------|
| NEW | `components/JMT415Section.js` | Table with expandable rows |
| NEW | `styles/components/jmt415.css` | Table styles, row colors, scrollbar |
| NEW | `js/parsers/jmt415-parser.js` | Parse SEC filing data into alert format |
| MODIFY | `index.html` | Add JMT415 container |

**Test Criteria**:
- [ ] Section header shows "JMT415" with info/expand icon
- [ ] Table has 3 columns: Symbol | Alert Description | Time
- [ ] Alternating row backgrounds (dark vs slightly lighter)
- [ ] New dilution filings have yellow/orange tint background
- [ ] Significant dilution rows have red tint background
- [ ] Hover on row shows highlight effect and cursor pointer
- [ ] Alert syntax renders correctly: "DILUTION ALERT: X Million", "Total Outstanding: X Million", etc.
- [ ] Timestamp shows relative time ("4 hours ago")
- [ ] Vertical scrollbar appears when >5-7 rows
- [ ] Click on row logs to console (placeholder for detail view)

**Done Definition**: Table renders with sample data; color-coded rows visible; hover interactions work.

---

## Slice 6: Risk Assessment Section

**Purpose**: Display risk score badge with tooltip and link behavior.

**Dependencies**: Slice 5 complete

**Files**:

| Action | File | Description |
|--------|------|-------------|
| NEW | `components/RiskAssessmentSection.js` | Risk badge with level display |
| NEW | `styles/components/risk.css` | Badge colors, tooltip styles |
| MODIFY | `index.html` | Add risk section container |

**Test Criteria**:
- [ ] Section header "Risk Score" displays
- [ ] Badge renders for each risk level:
  - HIGH: Red background (#f44336), white text
  - MEDIUM: Orange background (#ff9800), white text
  - LOW: Green background (#4caf50), white text
  - N/A: Gray background (#9e9e9e), white text
- [ ] Badge text displays risk level ("HIGH", "MEDIUM", "LOW", "N/A")
- [ ] Hover on badge shows tooltip with risk breakdown
- [ ] Click on badge opens askedgar.io/risk/{ticker} in new tab (or logs action)
- [ ] Qualitative description text appears below badge

**Done Definition**: Badge displays with correct colors per level; interactions work.

---

## Slice 7: Headlines/News Section

**Purpose**: Display scrollable news feed with source tags, headlines, and timestamps.

**Dependencies**: Slice 6 complete

**Files**:

| Action | File | Description |
|--------|------|-------------|
| NEW | `components/HeadlinesSection.js` | News feed list component |
| NEW | `styles/components/headlines.css` | News list styles, hover effects |
| NEW | `js/parsers/news-parser.js` | Parse news data into display format |
| MODIFY | `index.html` | Add headlines container |

**Test Criteria**:
- [ ] Section header shows "Headlines"
- [ ] Each news item displays:
  - Source tag (e.g., "GROK", "NEWS") as small colored badge
  - Headline text truncated to ~240 chars with ellipsis
  - Timestamp ("2 hrs ago", "Yesterday", or date)
  - External link indicator (arrow icon)
- [ ] Alternating row backgrounds (subtle)
- [ ] Hover on row highlights entire row, cursor changes to hand
- [ ] Click on row opens news source URL in new tab
- [ ] Scrollbar appears when >5 news items

**Done Definition**: News feed renders with sample data; hover/click interactions work; scrollable.

---

## Slice 8: Offering Ability Section

**Purpose**: Display offering ability description with color-coded capacity indicators.

**Dependencies**: Slice 7 complete

**Files**:
| Action | File | Description |
|--------|------|-------------|
| NEW | `components/OfferingAbilitySection.js` | Offering ability display with capacity bars |
| NEW | `styles/components/offering-ability.css` | Capacity indicator styles, color coding |
| MODIFY | `js/parsers/offering-parser.js` | Parse offering_ability_desc into structured data |
| MODIFY | `index.html` | Add offering ability container |

**Test Criteria**:
- [ ] Section header shows "Offering Ability"
- [ ] Description text parses and displays as bullet items
- [ ] Capacity indicators show:
  - Green (#4CAF50) for available capacity >$0
  - Red (#FF4444) for $0 capacity
  - Yellow for pending/expiring soon
- [ ] Each item shows: label + value + status indicator
- [ ] Items stack vertically with proper spacing

**Done Definition**: Offering ability data displays with correct color coding per capacity status.

---

## Slice 9: In-Play Dilution Section

**Purpose**: Show warrants and convertibles near current price with in-the-money indicators.

**Dependencies**: Slice 8 complete

**Files**:
| Action | File | Description |
|--------|------|-------------|
| NEW | `components/InPlayDilutionSection.js` | Warrants and convertibles display |
| NEW | `styles/components/in-play.css` | Section styles, price indicator colors |
| MODIFY | `js/parsers/dilution-parser.js` | Parse warrant/convertible data |
| MODIFY | `index.html` | Add in-play dilution container |

**Test Criteria**:
- [ ] Section header shows "In Play Dilution"
- [ ] Two subsections: WARRANTS and CONVERTIBLES (yellow labels)
- [ ] Each item displays:
  - Description/truncated text
  - Remaining amount (M/K formatted)
  - Strike/conversion price
  - Filed date
  - Price indicator (green if in-the-money, orange if out)
- [ ] Click on row opens source URL or Ask Edgar page
- [ ] Empty state shows when no in-play dilution

**Done Definition**: Warrants and convertibles display with correct price indicators; click interactions work.

---

## Slice 10: Integration & Final QA

**Purpose**: Wire all sections together, implement error handling, loading states, and final polish.

**Dependencies**: Slices 1-9 complete

**Files**:
| Action | File | Description |
|--------|------|-------------|
| MODIFY | `js/main.js` | Integrate all sections, orchestrate data flow |
| MODIFY | `js/state.js` | Add section-specific loading/error states |
| MODIFY | `js/api.js` | Add error handling, retry logic |
| MODIFY | `styles/main.css` | Final polish, transitions, animations |
| MODIFY | `index.html` | Final structure verification |

**Test Criteria**:
- [ ] All 7 sections render in correct order
- [ ] Ticker change triggers data fetch for all sections
- [ ] Loading states show per-section (not global)
- [ ] Error states display when API fails
- [ ] Retry button works on error
- [ ] No console errors
- [ ] Responsive scroll behavior works
- [ ] All click interactions functional
- [ ] Visual polish: transitions, hover effects, shadows

**Done Definition**: Full app functional end-to-end; all sections integrated; error handling works; no critical bugs.

---

## Sequence Rules

1. Complete each slice fully before starting next
2. No partial slice work
3. If blocked → HALT, do not skip ahead
4. Each slice must pass tests before proceeding
5. No new slices without human approval

---

## Deferred (Not This Roadmap)

- Price data, % change, live market feed — deferred to scanner module
- Window scraper / platform detection — desktop-only, not applicable
- Real-time WebSocket updates — polling only for Phase 2
- User authentication — single API key per deployment
- Mobile-responsive design — desktop-optimized only
- Historical data charts — current data only
- Data export / download — view-only