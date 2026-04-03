# UI Specification: AskEdgar Dilution Monitor - Phase 2

## Document Information
- **Project**: gap-lens-dilution
- **Phase**: Phase 2 - Web UI Redesign
- **Output**: `/home/d-tuned/projects/gap-lens-dilution/specs/phase2/03-UI-SPEC.md`
- **Based On**: Reference Image (AskEdgar Dilution App.png) + Phase 2 Requirements

---

## 1. Application Overview

### 1.1 Purpose
A dark-themed web dashboard for monitoring stock dilution data, displaying gap analysis, share structure, dilution alerts, risk assessment, and news headlines.

### 1.2 Design Philosophy
- Clean, information-dense dark UI
- Vertical scroll with stacked card sections
- Color-coded data for quick comprehension
- Consistent spacing and visual hierarchy

---

## 2. Visual Design System

### 2.1 Color Palette

| Token | Hex Code | Usage |
|-------|----------|-------|
| `--bg-primary` | #1a1a1a | Main window background |
| `--bg-card` | #2d2d2d | Card/section backgrounds |
| `--bg-card-hover` | #333333 | Card hover state |
| `--bg-input` | #252525 | Input field background |
| `--text-primary` | #ffffff | Main headings, values |
| `--text-secondary` | #a0a0a0 | Labels, descriptions |
| `--text-muted` | #666666 | Disabled/placeholder |
| `--border-color` | #444444 | Card borders, dividers |
| `--border-input` | #555555 | Input borders |
| `--accent-cyan` | #00bcd4 | Brand accent, active states |
| `--accent-cyan-hover` | #00acc1 | Cyan hover state |
| `--positive` | #4caf50 | Positive change, low risk |
| `--negative` | #f44336 | Negative change, high risk, errors |
| `--warning` | #ff9800 | Medium risk, warnings |
| `--alert-bg-yellow` | #fff3cd | Alert row background (yellow) |
| `--alert-bg-red` | #3d1f1f | Alert row background (red) |

### 2.2 Typography

| Element | Font Family | Size | Weight | Line Height | Letter Spacing |
|---------|-----------|------|--------|-------------|----------------|
| App Title | System UI / Segoe UI | 16px | 700 (Bold) | 1.2 | 0.5px |
| Section Header | System UI | 14px | 600 (Semibold) | 1.3 | 0.3px |
| Label | System UI | 12px | 400 (Regular) | 1.4 | 0.2px |
| Data Value | Monospace (Consolas) | 14px | 400 (Regular) | 1.2 | 0 |
| Metric Value | Monospace | 16px | 500 (Medium) | 1.2 | 0 |
| Alert Text | System UI | 12-13px | 400 (Regular) | 1.4 | 0 |
| Timestamp | System UI | 11px | 400 (Regular) | 1.2 | 0 |

### 2.3 Spacing System

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | 4px | Tight internal spacing |
| `--space-sm` | 8px | Component internal padding |
| `--space-md` | 12px | Standard element spacing |
| `--space-lg` | 16px | Card padding, section gaps |
| `--space-xl` | 24px | Major section separations |
| `--space-xxl` | 32px | Page-level padding |

### 2.4 Border Radius

| Element | Radius |
|---------|--------|
| Cards/Sections | 6px |
| Input fields | 4px |
| Buttons | 4px |
| Badges/Pills | 12px (fully rounded) |

### 2.5 Elevation/Shadows

```css
--shadow-card: 0 2px 4px rgba(0, 0, 0, 0.2);
--shadow-elevated: 0 4px 8px rgba(0, 0, 0, 0.3);
```

---

## 3. Screen Specifications

### 3.1 Layout Dimensions

| Property | Value |
|----------|-------|
| Default Width | 480px (fixed) |
| Min Width | 400px |
| Max Width | 600px |
| Min Height | 400px |
| Default Padding | 16px horizontal |
| Section Spacing | 16px between sections |

### 3.2 Overall Layout Structure

```
┌─────────────────────────────────────────┐
│           HEADER COMPONENT              │
├─────────────────────────────────────────┤
│         TICKER INPUT SECTION            │
├─────────────────────────────────────────┤
│          GAP ANALYZER SECTION           │
│  [Previous Close | Current | % Change]  │
├─────────────────────────────────────────┤
│         SHARE STRUCTURE SECTION         │
│  [Authorized]                         │
│  [Outstanding]                        │
│  [Float]                              │
├─────────────────────────────────────────┤
│           JMT415 SECTION              │
│  ┌───────────────────────────────────┐  │
│  │ ▶ Symbol │ Alert Description    │ Time│
│  │ ▶ ...                              │  │
│  └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│       RISK ASSESSMENT SECTION         │
│           [RISK BADGE]                  │
├─────────────────────────────────────────┤
│         HEADLINES SECTION               │
│  ┌───────────────────────────────────┐  │
│  │ Source │ Headline text...    │ Time│
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 3.3 Pages & States

**Primary Screen: Dashboard**
- All sections visible
- Vertical scroll if content exceeds viewport

**States:**
1. **Idle/Empty**: No ticker loaded, shows placeholder message
2. **Loading**: Spinner overlay while fetching data
3. **Active**: Ticker data displayed across all sections
4. **Error**: Red error message at top

---

## 4. Navigation & User Flows

### 4.1 User Flow Diagram

```
┌─────────────┐
│  App Load   │
└──────┬──────┘
       ▼
┌─────────────┐
│  Wait State │ ──────► [Show: "Load ticker in DAS or thinkorswim..."]
└──────┬──────┘
       │
       ▼ User enters ticker
┌─────────────┐
│   Loading   │ ──────► [Show spinner, "Fetching data for {TICKER}..."]
└──────┬──────┘
       │
       ├──────► Error ─────► [Show error message, allow retry]
       │
       ▼ Success
┌─────────────┐
│   Active    │ ──────► [Populate all sections with data]
└──────┬──────┘
       │
       ├──────► Click news item ─────► Open external link
       ├──────► Click JMT415 row ─────► Open detail/external
       ├──────► Click Risk badge ─────► Navigate to Ask Edgar risk page
       └──────► Scroll sections ─────► Smooth scroll experience
```

### 4.2 Navigation Map

```
Dashboard (Single Page)
├── Header (static)
├── Ticker Input (focus triggers keyboard)
├── Gap Analyzer (data display)
├── Share Structure (data display)
├── JMT415 Feed (scrollable, clickable rows)
├── Risk Assessment (clickable badge)
└── Headlines Feed (scrollable, clickable items)
```

### 4.3 Deep Links / External Navigation

| Action | Destination | Context |
|--------|-------------|---------|
| Click Risk Badge | askedgar.io/risk/{ticker} | New tab |
| Click News Item | news source URL | New tab |
| Click JMT415 Row | SEC filing or detail page | New tab |

---

## 5. Screen Specifications

### 5.1 Header Component

**Layout:**
```
┌─────────────────────────────────────────┐
│ [Logo] ASK EDGAR ✕ DILUTION MONITOR │
└─────────────────────────────────────────┘
```

- **Height**: 48px
- **Background**: `--bg-card` (#2d2d2d)
- **Border-bottom**: 1px solid `--border-color`
- **Logo**: 24x24px, left margin 16px
- **Title**: "ASK EDGAR" white, "DILUTION MONITOR" cyan accent
- **Font**: 16px bold, `--text-primary`

**Interactions:**
- Drag handle (for desktop window repositioning)

---

### 5.2 Ticker Input Section

**Layout:**
```
┌─────────────────────────────────────────┐
│ ENTER TICKER FOR DILUTION DATA          │
│ ┌────────────────────────────────┐ [🔍]  │
│ │ Enter ticker symbol...       │       │
│ └────────────────────────────────┘      │
└─────────────────────────────────────────┘
```

**Specifications:**
- **Section Padding**: 16px all sides
- **Label**: Uppercase, `--text-secondary`, 11px, letter-spacing 0.5px
- **Input Height**: 40px
- **Input Padding**: 12px horizontal
- **Input Border**: 1px solid `--border-input`, radius 4px
- **Input BG**: `--bg-input`
- **Input Text**: 14px uppercase, monospace
- **Placeholder**: "AAPL" (uppercase, `--text-muted`)
- **Search Button**: 36x36px, right side, `--accent-cyan` background, white icon

**States:**

| State | Visual |
|-------|--------|
| Default | Border `--border-input`, label gray |
| Focus | Border `--