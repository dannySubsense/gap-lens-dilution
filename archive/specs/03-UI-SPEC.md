# UI Specification: Gap Lens Dilution Phase 1

**Version:** 1.0
**Date:** 2026-03-22
**Status:** APPROVED

---

## 1. Overview

This document defines the complete user interface for Gap Lens Dilution, including screen layouts, components, interactions, and visual design.

---

## 2. Main Screen Layout

```
┌──────────────────────────────────────────────┐
│  Gap Lens: Dilution Risk Analysis            │
├──────────────────────────────────────────────┤
│                                              │
│  Ticker: [________] [Analyze]                │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ Overall Risk    Offering Ability       │  │
│  │ 87% HIGH RISK   72% MODERATE           │  │
│  ├────────────────────────────────────────┤  │
│  │ Dilution        Cash Need              │  │
│  │ 42.5%           $23.4M                 │  │
│  ├────────────────────────────────────────┤  │
│  │ Cash Remaining  Est. Cash              │  │
│  │ 3.2 months      $8.1M                  │  │
│  ├────────────────────────────────────────┤  │
│  │ Cash Burn       Float                  │  │
│  │ $2.5M/month     45.2M shares           │  │
│  ├────────────────────────────────────────┤  │
│  │ Outstanding     Market Cap             │  │
│  │ 67.8M           $156.3M                │  │
│  ├────────────────────────────────────────┤  │
│  │ Insider Own     Institutional Own      │  │
│  │ 12.3%           34.7%                  │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │  [Price Chart - 6 Month Historical]    │  │
│  │  [1M] [3M] [6M]                        │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  Data from Ask-Edgar | Updated: 2026-03-22  │
└──────────────────────────────────────────────┘
```

**Container:**
- Max-width: 1440px
- Top padding: 32px
- Side margins: 40px
- Section spacing: 24px

---

## 3. Components

### 3.1 Search Input

**Layout:**
```
Ticker Symbol: [________] [Analyze]
```

**Input Properties:**
- Width: 200px
- Height: 48px
- Border: 2px solid #E0E0E0
- Border radius: 4px
- Focus: 2px solid #0066CC
- Font: 16px, system font
- Padding: 12px 16px

**Button Properties:**
- Width: 120px
- Height: 48px
- Background: #0066CC
- Hover: #0052A3
- Text: white, 16px bold
- Border-radius: 4px

**States:**
- Empty: Placeholder "Enter ticker..."
- Typing: Real-time validation
- Valid: Green checkmark
- Invalid: Red error message
- Loading: Disabled, gray background

**Validation Rules:**
- 1-10 uppercase letters
- No special characters
- Auto-convert to uppercase

### 3.2 Metrics Grid

**Layout:** 2-column grid, 6 rows

**Card Properties:**
- Padding: 20px
- Border: 1px solid #E8E8E8
- Border-radius: 8px
- Background: #FFFFFF
- Shadow: 0 2px 4px rgba(0,0,0,0.06)
- Gap: 16px horizontal, 20px vertical

**Metric Card Structure:**
```
Label (uppercase, 14px, gray)
━━━━━━━━━━━━━━━━━━
[Visualization]
Value (32px, bold, black)
Unit (18px, gray)
```

**Metric Details:**

1. **Overall Offering Risk**
   - Progress bar (0-100%)
   - Color: Red if >66%, Yellow 34-66%, Green <33%
   - Label: HIGH/MODERATE/LOW RISK

2. **Offering Ability**
   - Progress bar (0-100%)
   - Same color scale as risk

3. **Dilution**
   - Percentage display
   - Red if >30%, Yellow 15-30%, Green <15%

4. **Cash Need**
   - Currency format: $XXM or $X.XB

5. **Cash Remaining**
   - Months display: X.X months
   - Red if <3 months, Yellow 3-6, Green >6

6. **Estimated Cash**
   - Currency format: $XXM

7. **Cash Burn**
   - Format: $X.XM/month
   - Red if >$5M, Yellow $1-5M, Green <$1M

8. **Float**
   - Shares: XXM or X.XB

9. **Outstanding Shares**
   - Count: XXM or X.XB

10. **Market Cap**
    - Currency: $XXXM or $X.XB

11. **Insider Ownership**
    - Percentage: XX.X%
    - Green >10%, Yellow 5-10%, Red <5%

12. **Institutional Ownership**
    - Percentage: XX.X%
    - Green >30%, Yellow 15-30%, Red <15%

### 3.3 Price Chart

**Container:**
```
PRICE CHART
──────────────────
[TradingView Chart]

[1M] [3M] [6M ✓]
```

**Properties:**
- Width: 100% of container
- Height: 400px
- Background: white
- Border: 1px solid #E8E8E8
- Border-radius: 8px

**Chart Type:** Candlestick with volume bars
**Default Range:** 6 months
**Interactive Features:**
- Zoom and pan
- Crosshair with tooltip
- Hover price display

**Timeframe Buttons:**
- Height: 32px
- Padding: 8px 16px
- Active: #0066CC background, white text
- Inactive: #F5F5F5 background, gray text

### 3.4 Error Messages

**Error Message Structure:**
```
┌──────────────────────────┐
│ ⚠ Error Title            │
│                          │
│ Description of error.    │
│ What went wrong.         │
│                          │
│ [Action] [Action]        │
└──────────────────────────┘
```

**Error Types:**

**404 - Ticker Not Found:**
- Background: #FEF9E7 (light yellow)
- Border: 2px #F59E0B (yellow)
- Icon: ⚠️
- Message: "Ticker '[X]' not found. Verify the symbol and try again."
- Suggestions: Check for typos, verify SEC registration
- Action: "Try Another Ticker"

**429 - Rate Limited:**
- Background: #FEF9E7 (light yellow)
- Border: 2px #F59E0B (yellow)
- Message: "Too many requests. Wait [X] seconds."
- Action: "Wait" (countdown timer)

**5xx - Server Error:**
- Background: #FEF2F2 (light red)
- Border: 2px #EF4444 (red)
- Message: "Service unavailable. Try again later."
- Action: "Retry" button

**Network Error:**
- Background: #FEF2F2 (light red)
- Border: 2px #EF4444 (red)
- Message: "Connection failed. Check internet."
- Action: "Retry" button

---

## 4. Color Palette

**Gap Research Design System:**

| Use | Color | Hex |
|-----|-------|-----|
| Primary | Blue | #0066CC |
| Primary Hover | Dark Blue | #0052A3 |
| Primary Light | Light Blue | #E6F2FF |
| Success | Green | #10B981 |
| Warning | Yellow | #F59E0B |
| Danger | Red | #EF4444 |
| Text Primary | Dark Gray | #1A1A1A |
| Text Secondary | Medium Gray | #666666 |
| Border | Light Gray | #E8E8E8 |
| Background | White | #FFFFFF |
| Background Alt | Light Gray | #F9FAFB |

---

## 5. Typography

**Font Family:**
```
-apple-system, BlinkMacSystemFont, 'Segoe UI',
Roboto, Helvetica, Arial, sans-serif
```

**Type Scale:**
- H1: 32px, bold, #1A1A1A
- H2: 24px, semi-bold, #1A1A1A
- Body Large: 16px, regular, #1A1A1A
- Body: 14px, regular, #666666
- Small: 12px, regular, #999999
- Label: 14px, semi-bold, uppercase, #666666
- Metric Value: 32px, bold, #1A1A1A

**Font Weights:**
- Regular: 400
- Semi-bold: 600
- Bold: 700

---

## 6. Spacing System

**Base Unit:** 4px

**Scale:**
- xs: 4px
- sm: 8px
- md: 16px
- lg: 24px
- xl: 32px
- 2xl: 48px

**Component Spacing:**
- Card padding: 20px
- Button padding: 12px 24px
- Input padding: 12px 16px
- Section gaps: 24px

---

## 7. Shadows & Effects

**Elevation:**
- Level 1 (Cards): `0 2px 4px rgba(0,0,0,0.06)`
- Level 2 (Dropdowns): `0 4px 12px rgba(0,0,0,0.12)`
- Level 3 (Modals): `0 8px 24px rgba(0,0,0,0.18)`

**Focus State:**
```css
box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.2);
outline: none;
```

**Transitions:** 0.2s ease-in-out

---

## 8. Interaction Flows

### 8.1 Primary Search Flow

```
User types ticker → Validate → Submit → Show loading
  ↓
API returns 200 → Display metrics + chart
  ↓
User sees all data
```

### 8.2 Error Flow

```
API returns error → Show error message
  ↓
User clicks retry → Re-submit request
  ↓
Success or error again
```

### 8.3 Chart Interaction

```
User clicks timeframe (1M, 3M, 6M) → Load chart data → Re-render
```

---

## 9. States

**Application States:**
1. **Empty:** No data loaded, show placeholder
2. **Loading:** Show spinner and skeleton loaders
3. **Success:** Display all metrics and chart
4. **Error:** Show error message with retry
5. **Disabled:** Input/buttons disabled during loading

**Component States:**
- Input: empty, typing, valid, invalid, loading
- Metrics: hidden, loading, visible, error
- Chart: hidden, loading, visible, error

---

## 10. Loading States

**Main Loading:**
```
⟳ Loading...
Fetching dilution data for TSLA
[████░░░░░░░░] 40%
```

**Skeleton Loaders:**
- Metrics cards: Gray pulse animation
- Chart: Simplified wireframe with pulse

**Animations:**
- Spinner: 1.5s rotation
- Pulse: 1.5s opacity animation
- Fade-in: 0.4s ease-out

---

## 11. Accessibility

**WCAG 2.1 AA Compliance:**
- Color contrast: 4.5:1 minimum for text
- Keyboard navigation: Tab order documented
- Screen reader: ARIA labels on all interactive elements
- Focus indicators: Visible 3px outlines

**Keyboard Navigation:**
1. Search input
2. Analyze button
3. Chart timeframe buttons
4. Refresh button

**Screen Reader Labels:**
- Input: "Enter stock ticker symbol"
- Button: "Analyze ticker dilution risk"
- Error: role="alert", aria-live="assertive"
- Loading: role="status", aria-live="polite"

---

## 12. Responsive Design

**Desktop-First (Phase 1):**
- Minimum width: 1280px
- Optimal: 1440px - 1920px
- Max-width: 1440px container

**Future Mobile (Phase 2):**
- Single column layout
- Sticky search bar
- Touch-friendly buttons (48px minimum)
- Collapsible sections

---

## 13. Browser Support

**Supported:**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Requirements:**
- ES6 JavaScript
- CSS Grid & Flexbox
- Fetch API
- SVG support

---

## 14. Implementation Checklist

- [ ] Search input with validation
- [ ] Metrics grid display (2 columns, 6 rows)
- [ ] Progress bars and color coding
- [ ] TradingView chart integration
- [ ] Loading indicators
- [ ] Error message display
- [ ] Keyboard navigation
- [ ] Screen reader support
- [ ] Accessibility compliance
- [ ] Design system colors applied
- [ ] Typography correctly sized
- [ ] Spacing follows 4px grid
- [ ] Animations and transitions smooth

---

**Status:** ✅ READY FOR ROADMAP PLANNING
