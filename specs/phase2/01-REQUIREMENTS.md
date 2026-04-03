# Phase 2 Requirements: Ask Edgar Dilution Monitor Web UI

## Document Information
- **Project**: gap-lens-dilution
- **Phase**: Phase 2 - Web UI Redesign
- **Output**: `/home/d-tuned/projects/gap-lens-dilution/specs/phase2/01-REQUIREMENTS.md`
- **Based On**: Reference Image (AskEdgar Dilution App.png) + Phase 2 Audit Document

---

## 1. Global Application Specification

### 1.1 Visual Theme
| Property | Specification |
|----------|---------------|
| Theme | Dark mode (consistent throughout) |
| Background | #1a1a1a or equivalent dark background |
| Card Background | #2d2d2d or slightly lighter shade for cards |
| Text Primary | #ffffff (white) for main text |
| Text Secondary | #a0a0a0 (gray) for labels/descriptions |
| Accent/Highlight | Cyan/blue (#00bcd4 or similar) for active elements |
| Border Color | #444444 for card borders and separators |

### 1.2 Typography
| Element | Font | Size | Weight | Color |
|---------|------|------|--------|-------|
| App Title | Segoe UI / System | 14-16px | Bold | White + Cyan accent |
| Section Headers | Segoe UI | 13-14px | Bold | White |
| Labels | Segoe UI | 11-12px | Regular | Gray (#a0a0a0) |
| Data Values | Consolas / Monospace | 12-14px | Regular | White |
| Warning/Alert | Segoe UI | 12px | Bold | Red/Orange |

### 1.3 Window/Screen Specifications
| Property | Specification |
|----------|---------------|
| Default Size | 480x620 pixels (fixed aspect) |
| Minimum Size | 400x300 pixels |
| Default Position | 50,50 from screen origin |
| Layout | Vertical scroll container with stacked cards |

---

## 2. Header Section

### 2.1 Visual Elements
- **Draggable Header Bar**: Full-width top section for window repositioning
- **App Icon/Logo**: Small icon at left of title
- **Title Text**: "Ask Edgar" in white + "Dilution Monitor" in cyan/blue
- **Window Controls**: Minimize/maximize/close buttons (right-aligned) [optional for web]

### 2.2 Interactive Behaviors
| Interaction | Behavior |
|-------------|----------|
| Drag Header | Drag window to reposition (if desktop window) |
| Hover on Controls | Cursor changes to hand, highlight effect |

---

## 3. Ticker Input Section

### 3.1 Visual Elements
- **Label**: "ENTER TICKER FOR DILUTION DATA" (uppercase, gray text)
- **Input Field**: 
  - Single-line text input
  - Dark background with light border
  - Uppercase display
  - Placeholder: AAPL
- **Status Indicator**: Small icon/badge showing loading/searching state

### 3.2 Data Requirements
- Input masking: Auto-convert to uppercase
- Validation: Accept 1-5 alphanumeric characters
- Submit trigger: Enter key or auto-submit on 4+ characters

### 3.3 State Behaviors
| State | Display |
|-------|---------|
| Empty | Placeholder "AAPL" visible |
| Typing | User input in uppercase |
| Loading | Spinner or "Fetching..." indicator |
| Success | Data populated in all sections |
| Error | "NO DATA" or error message |

---

## 4. Gap Analyzer Section

### 4.1 Visual Elements
- **Section Header**: "Gap Analyzer" with dividing line
- **Data Cards**: 3-column grid layout
- **Metrics Displayed**:
  - Previous Close: [value]
  - Current Price: [value]
  - % Change: [value with color coding]

### 4.2 Color Coding
| Value | Color |
|-------|-------|
| Positive change | Green (#4caf50 or similar) |
| Negative change | Red (#f44336 or similar) |
| Neutral | White/Gray |

---

## 5. Share Structure Section

### 5.1 Visual Elements
- **Section Header**: "Share Structure"
- **Three Data Rows**:
  - **Authorized**: Label + numeric value
  - **Outstanding**: Label + numeric value
  - **Float**: Label + numeric value

### 5.2 Data Formatting
| Field | Format | Example |
|-------|--------|---------|
| Authorized | M/K notation (fmt_millions) | "1,500M" or "1.5B" |
| Outstanding | M/K notation | "845.2M" |
| Float | M/K notation | "820.4M" |

### 5.3 Layout
- Left-aligned labels in gray
- Right-aligned values in white monospace font
- Consistent spacing between rows

---

## 6. JMT415 Section (Dilution Alert Feed)

### 6.1 Visual Elements
- **Section Header**: "JMT415" with info/expand icon
- **Feed Table** with 3 columns:
  - Symbol/Ticker
  - Alert Type/Dilution Event
  - Timestamp

### 6.2 Table Row Design
- Alternating row backgrounds (dark vs slightly lighter)
- Each row represents a dilution alert
- **Columns**:
  1. **Symbol**: Ticker symbol (bold, white)
  2. **Alert**: Description text with syntax highlighting:
     - "DILUTION ALERT: [X] Million"
     - "Total Outstanding: [X] Million"
     - "Shares Added: [X] Million"
     - "At: $[price]"
     - "Percent Change: [X]%"
  3. **Time**: "4 hours ago" or timestamp

### 6.3 Row Color Coding
| Alert Type | Background | Text Color |
|------------|------------|------------|
| New dilution filing | Yellow/Orange tint | Black/Dark text |
| Significant dilution | Red tint | White text |
| Normal alert | Dark default | White text |

### 6.4 Interactive Behaviors
| Interaction | Behavior |
|-------------|----------|
| Hover on row | Highlight row, cursor changes to hand |
| Click row | Open detailed view or external link |
| Scroll/Overflow | Auto-scroll or vertical scrollbar |

---

## 7. Risk Assessment Section

### 7.1 Visual Elements
- **Section Header**: "Risk Score"
- **Risk Badge**: Large colored indicator
- **Qualitative Text**: Additional risk description

### 7.2 Risk Level Display
| Level | Color | Background |
|-------|-------|------------|
| High Risk | Red (#f44336) | Red badge with white text |
| Medium Risk | Orange/Yellow (#ff9800) | Orange badge |
| Low Risk | Green (#4caf50) | Green badge |
| N/A | Gray (#9e9e9e) | Gray badge |

### 7.3 Interactive Behavior
- Click on risk badge → Navigate to Ask Edgar risk detail page
- Hover → Tooltip with risk breakdown

---

## 8. Headlines/News Feed Section

### 8.1 Visual Elements
- **Section Header**: "Headlines"
- **News List** vertical layout:
  - Each item is a clickable row
  - Source icon/logo (optional)
  - Headline text (truncated if needed)
  - Timestamp
  - External link indicator

### 8.2 News Item Structure
| Element | Display |
|---------|---------|
| Source Tag | Small badge with source name (e.g., "GROK", "NEWS") |
| Headline | Main text, ~240 char truncation with ellipsis |
| Timestamp | "2 hrs ago", "Yesterday", or date |
| Link Icon | Arrow or external link icon |

### 8.3_row Styling
- Alternating backgrounds (subtle)
- Hover: Highlight entire row
- Click: Open news source URL in new tab

---

## 9. Status/Error States

### 9.1 Loading State
**Visual**: 
- Spinner or "Fetching data for [TICKER]..." message
- Semi-transparent overlay or inline text
- Progress indication optional

### 9.2 Waiting State
**Visual**:
- Centered message: "Load a ticker in DAS or thinkorswim to see dilution data here."
- Subtle gray text on dark background
- App logo/icon above text (optional)

### 9.3 No Data State
**Visual**:
- "NO DATA" red badge/alert
- Message: "No dilution data available for [TICKER]."
- Suggestion text below (optional)

### 9.4 Error State
**Visual**:
- Red warning icon
- Error message text
- Retry button (optional)

---

## 10. Scroll & Overflow Behavior

### 10.1 Auto-Scroll Specifications
| Container | Behavior |
|-----------|----------|
| Main Window | Vertical scroll when content > window height |
| JMT415 Section | Scrollable if > 5-7 alerts visible |
| Headlines Section | Scrollable if > 5 news items |

### 10.2 Scrollbar Styling
- Dark theme scrollbar (gray thumb on darker track)
- Width: 8-10px
- Hover: Lighter gray thumb

---

## 11. Interactive Specifications Summary

| Element | Click | Hover | Scroll | Drag |
|---------|-------|-------|--------|------|
| Header | - | - | - | Yes (reposition window) |
| Ticker Input | Submit | - | - | - |
| Risk Badges | Open link | Highlight | - | - |
| JMT415 Row | Open link | Highlight | - | - |
| Headline Row | Open link | Highlight | - | - |

---

## 12. Out of Scope

The following features are explicitly **NOT** included in Phase 2:

- **Price data, % change, and live market feed** — Deferred to future scanner module
- **Window scraper / platform detection** — Desktop-only feature, not applicable to web app
- **Real-time WebSocket updates** — Polling-based refresh only
- **User authentication / accounts** — Single API key per deployment
- **Mobile-responsive design** — Desktop-optimized layout only
- **Data export / download** — View-only interface
- **Historical data charts** — Current data only

---

## 13. Constraints

- Must use existing AskEdgar API endpoints only
- Must maintain dark theme UI consistency
- Must support modern browsers (Chrome, Firefox, Safari, Edge)
- Must handle API rate limits gracefully