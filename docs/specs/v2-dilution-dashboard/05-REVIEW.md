# Spec Review: v2-dilution-dashboard

**Version:** 2.0
**Date:** 2026-04-03
**Status:** APPROVED -- Ready for Implementation
**Reviewer:** @spec-reviewer
**Review iteration:** 2 (re-review after fixes)

---

## Executive Summary

This is the second review iteration. The first review identified 4 blockers, 8 warnings, and 5 notes. Three agents applied fixes across the requirements, architecture, and UI spec documents. This re-review confirms that **all 4 blockers are resolved**. Two minor warnings remain (a "10 sub-calls" typo in the architecture and a HISTORY_MAP color discrepancy in the roadmap) and one new note was identified (the 4x filter is missing from the roadmap Slice 4 implementation notes). None of these are blocking -- all can be corrected during implementation without ambiguity, because the authoritative documents (architecture and UI spec) are now internally consistent.

The spec suite is **approved for implementation**.

---

## 1. Blocker Resolution Status

### BLOCKER-1: Sidebar Error Behavior -- Internal UI Spec Contradiction
**Status: RESOLVED**

The UI spec Section 10.2 (lines 819-833) now clearly distinguishes two cases:
- **Refresh failure** (prior data exists): stale rows are retained; a "Refresh failed" indicator appears in the sidebar header.
- **Initial load failure** (no prior data): full error state with message + Retry button replaces the list.

This is consistent with Flow 4 (line 80: "previously loaded list remains visible") and Section 7.3 (line 715: "previously loaded rows remain visible"). The contradiction is eliminated.

---

### BLOCKER-2: Sector Abbreviation Map Inconsistency
**Status: RESOLVED**

Architecture Appendix A (lines 935-947) now uses the same abbreviations as the UI spec and reference implementation:
- Consumer Defensive: "Cons Def" (was "Con Def")
- Consumer Cyclical: "Cons Cyc" (was "Con Cyc")
- Financial Services: "Financ" (was "Fin Svcs")
- Communication Services: "Comms" (was "Comm Svcs")
- Industrials: "Indust" (was "Ind")

All three documents (architecture Appendix A, UI spec Section 4.1 + Appendix A, roadmap Slice 8 line 515) now use identical abbreviations.

---

### BLOCKER-3: `fetchDilution` Signature Missing `AbortSignal` Parameter
**Status: RESOLVED**

Architecture Section 4.4 (lines 562-565) now reads:
```
export async function fetchDilution(
  ticker: string,
  signal?: AbortSignal
): Promise<ApiResult<DilutionResponse>>;
```

The `signal?: AbortSignal` parameter is present. `fetchGainers` also accepts an optional `signal` parameter (line 571-573). This is consistent with Section 5.2 (superseded load handling) and the roadmap Slice 6 (line 344).

---

### BLOCKER-4: HISTORY_MAP "yellow" Color Discrepancy
**Status: RESOLVED (with one residual note)**

The architecture and UI spec are now aligned:
- Architecture Appendix B (line 956): `yellow: { label: "Semi-Strong", color: "#B9A816" }`
- UI Spec Section 4.9 (line 484): `yellow: "HISTORY: Semi-Strong", bg: "#B9A816" (gold)`
- UI Spec Appendix B (line 924): `yellow: { label: "HISTORY: Semi-Strong", bg: "#B9A816" }`

The `#B9A816` (gold) value is now consistent across both authoritative documents.

**Residual note:** The roadmap Slice 9 (line 600) still uses `#B96A16` for yellow in its inline `HISTORY_MAP` listing. This is a stale value from before the fix. See WARNING-1 below.

---

## 2. Previously Identified Warnings -- Status Update

### WARNING-1 (was): Sub-Call Count Discrepancy ("10 sub-calls")
**Status: STILL PRESENT (downgraded to NOTE)**

Architecture Section 5.1 Data Flow (line 670) still says "asyncio.gather(10 sub-calls concurrently)" but the actual gather call (lines 766-775) lists 9 sub-calls. This is a cosmetic typo in a narrative section; the code-level specification is correct. It will not cause implementation errors because the actual gather call is the canonical reference.

### WARNING-2 (was): Offerings Limit Mismatch (Backend 5 vs Frontend 3)
**Status: RESOLVED**

AC-06 (line 154) now includes a clarifying note: "the backend fetches up to 5 offerings (`limit=5`) so that filtering (e.g., ATM USED rows) does not reduce the visible count below 3; the frontend slices to a maximum of 3 for display." This makes the intentional design decision explicit and eliminates developer confusion.

### WARNING-3 (was): GapStats Color Hex in AC-05 vs UI Spec
**Status: RESOLVED**

AC-05 (line 146) now uses `#5ce08a` for green, matching the UI spec Section 4.8. The incorrect `#36d29a` (Risk Low color) has been replaced with the correct data-value green.

---

## 3. New Issues Found in This Review

### WARNING-1 (NEW): Roadmap Slice 9 HISTORY_MAP Uses Stale Yellow Color

**Document:** 04-ROADMAP.md, Slice 9 (line 600)

**Details:** The roadmap Slice 9 implementation notes include an inline `HISTORY_MAP` definition where yellow is listed as `bg: "#B96A16"`. This is the old (incorrect) value. The architecture Appendix B and UI Spec Section 4.9 + Appendix B all use the corrected `#B9A816`.

**Impact:** Low. A developer implementing Slice 9 should follow the architecture and UI spec (which are marked as authoritative for color values), not the roadmap's inline copy. However, the stale value could cause a brief confusion.

**Recommended fix:** Update roadmap Slice 9 line 600 to change `#B96A16` to `#B9A816` for the yellow entry.

---

### WARNING-2 (NEW, carried forward): Utility Files Not Assigned to Roadmap Slices

**Document:** 04-ROADMAP.md, File Ownership Summary (lines 743-767)

**Details:** Architecture Appendix A defines `frontend/src/lib/sectorAbbreviations.ts` and Appendix B defines `frontend/src/lib/historyMap.ts`. Neither file appears in the roadmap's File Ownership Summary or is explicitly assigned to any slice.

**Impact:** Low. The sector abbreviation map is clearly needed in Slice 8 (GainerRow uses it) and the history map is needed in Slice 9 (ChartAnalysisBadge uses it). Developers can infer this from context, but explicit assignment prevents oversights.

**Recommended fix:** Add `frontend/src/lib/sectorAbbreviations.ts` (Created, Slice 8) and `frontend/src/lib/historyMap.ts` (Created, Slice 9) to the File Ownership Summary.

---

### NOTE-1 (NEW): 4x Strike Filter Not in Roadmap Slice 4 Implementation Notes

**Document:** 04-ROADMAP.md, Slice 4 (lines 172-241)

**Details:** Requirements AC-10 (line 190) documents the 4x strike price filter. Architecture Section 4.2 `get_dilution_data_v2` (lines 497-500) specifies the filter. However, the roadmap's Slice 4 implementation notes (lines 213-221), which detail warrant and convertible extraction logic, do not mention the 4x filter.

**Impact:** Low. The architecture's `get_dilution_data_v2` docstring is the canonical implementation reference for Slice 4, and it clearly states the filter. The roadmap omission is unlikely to cause the filter to be missed, but adding it would improve completeness.

**Recommended fix:** Add a bullet to Slice 4 implementation notes (after line 219): "Apply 4x strike price filter: exclude warrants/convertibles where `strike_price > stockPrice * 4` (per AC-10 and architecture Section 4.2)."

---

### NOTE-2 (NEW): AC-10 Contains an In-Play Dilution Criterion

**Document:** 01-REQUIREMENTS.md, AC-10 (line 190)

**Details:** The 4x strike filter criterion was added to AC-10 (Offering Ability), but it logically pertains to In-Play Dilution (AC-09 territory). The filter affects warrants and convertibles, not the offering ability description parser.

**Impact:** Minimal. The criterion is clearly written and unambiguous regardless of its AC grouping. A developer will implement it in `get_dilution_data_v2` (backend) per the architecture spec, not in the OfferingAbility component. No functional risk.

**Recommended fix (optional):** Move the criterion from AC-10 to AC-09 for better organizational alignment.

---

## 4. Requirements Completeness (Re-Verified)

### Checklist

- [x] Summary is present and clear
- [x] User stories follow "As a... I want... so that..." format (19 stories)
- [x] Every user story has acceptance criteria (AC-01 through AC-19)
- [x] Edge cases table is populated (15 entries)
- [x] Out of scope section is not empty (10 exclusions + 2 deferrals)
- [x] Constraints are concrete (14 constraints)
- [x] API endpoint mapping table present
- [x] Component mapping table present
- [x] 4x strike filter now documented (AC-10, line 190)
- [x] Green hex corrected in AC-05 (`#5ce08a`)
- [x] Offerings limit clarified in AC-06 (backend 5, frontend 3, with rationale)

---

## 5. Requirements to Architecture Coverage (Re-Verified)

All 19 user stories map to architecture components. No changes from first review. Full coverage confirmed.

---

## 6. Requirements to UI Coverage (Re-Verified)

All user-facing stories have UI flows and layouts. No changes from first review. Full coverage confirmed.

---

## 7. Architecture to Roadmap Coverage (Re-Verified)

| Architecture Component | Roadmap Slice | Status |
|------------------------|---------------|--------|
| All backend components | Slices 1-5 | OK |
| All frontend components | Slices 6-9 | OK |
| `sectorAbbreviations.ts` utility | Not explicitly assigned | WARNING (see WARNING-2) |
| `historyMap.ts` utility | Not explicitly assigned | WARNING (see WARNING-2) |
| 4x strike filter logic | Slice 4 (architecture), not in roadmap notes | NOTE (see NOTE-1) |

**Result:** Near-complete coverage. Two utility files not assigned to slices (non-blocking). 4x filter in architecture but not roadmap notes (non-blocking).

---

## 8. Cross-Document Consistency (Re-Verified)

| Check | Documents | Status |
|-------|-----------|--------|
| Sector abbreviation map | Arch Appendix A, UI Spec Sec 4.1 + Appendix A, Roadmap Slice 8 | Consistent |
| HISTORY_MAP yellow color | Arch Appendix B, UI Spec Sec 4.9 + Appendix B | Consistent (`#B9A816`) |
| HISTORY_MAP yellow color | Roadmap Slice 9 | STALE (`#B96A16` -- see WARNING-1) |
| `fetchDilution` signature | Arch Sec 4.4, Arch Sec 5.2, Roadmap Slice 6 | Consistent (includes `signal?: AbortSignal`) |
| Sidebar error behavior | UI Spec Flow 4, Sec 7.3, Sec 10.2 | Consistent (retain stale rows on refresh error) |
| Risk badge colors | Req constraints, UI Spec Sec 5.1, Roadmap Slice 8 | Consistent |
| Green data color (`#5ce08a`) | Req AC-05, UI Spec Sec 4.8 | Consistent |
| Offerings limit | Req AC-06, AC-18, Arch Sec 4.2 | Consistent (backend 5, frontend 3, rationale documented) |
| Sub-call count | Arch Sec 5.1 narrative vs Arch Sec 7.1 code | Minor typo (10 vs 9 in narrative) |
| 4x strike filter | Req AC-10, Arch Sec 4.2 | Consistent |
| 4x strike filter | Roadmap Slice 4 notes | Not mentioned (NOTE-1) |

---

## 9. Identified Risks (Updated)

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| RISK-1 | `registrations` endpoint prefix is assumed to be `/enterprise/v1/` but is not in the intake's endpoint table. If wrong, Slice 1 introduces a regression. | Medium | High | Verify prefix against AskEdgar API docs before implementing Slice 1. If unconfirmed, keep `/v1/registrations` and add a TODO. |
| RISK-2 | `mgmt_commentary` field may not exist in the live `/enterprise/v1/dilution-rating` response. | Medium | Low | Architecture Appendix C documents graceful null fallback. No action needed beyond live API testing. |
| RISK-3 | TradingView scanner POST may change its response format without notice. | Low | High | The 200-empty-array fallback in `GainersService` handles this gracefully. Monitor for extended empty responses. |
| RISK-4 | The 50-ticker/day AskEdgar rate limit is not tracked or enforced. | Medium | Medium | Cache is the V2 mitigation. Acceptable for now. |
| RISK-5 | Slices 8 and 9 both modify `page.tsx` and are marked as parallelizable. | Medium | Low | Roadmap acknowledges this. Coordinate merge order. |

Note: RISK-3 from the first review (4x filter omission) has been eliminated -- the filter is now documented in requirements and architecture.

---

## 10. Assumptions (Unchanged)

| # | Assumption | Source | Impact if Wrong |
|---|-----------|--------|-----------------|
| A-1 | `mgmt_commentary` is a field in the existing `/enterprise/v1/dilution-rating` response | Architecture Appendix C, Requirements constraint | If absent, MgmtCommentary renders nothing. A new API call would be needed. |
| A-2 | The AskEdgar API returns `status: "success"` and `results: [...]` envelope for all endpoints | Reference implementation pattern | If new endpoints differ, all parsing fails. |
| A-3 | `high_time` in gap stats is an ISO timestamp in EST (not UTC) | Requirements AC-05, UI Spec Section 4.8 | If UTC, the 11am threshold is wrong by 4-5 hours. |
| A-4 | The `registrations` endpoint should use `/enterprise/v1/` prefix | Roadmap Slice 1 by analogy | If wrong, prefix change causes 404s. |
| A-5 | Node 18+ is available for the Next.js frontend | Requirements constraints | If Node 16, some features may break. |
| A-6 | TradingView scanner response field ordering is stable | Reference implementation line 232 | If column order changes, parsing breaks. |

---

## 11. Open Questions (Updated)

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| Q-1 | What is the correct API prefix for the `registrations` endpoint: `/v1/` or `/enterprise/v1/`? | Open | Needs AskEdgar API documentation or manual test. Non-blocking: Slice 1 uses `/enterprise/v1/` per analogy; if wrong, it is a single-line fix. |
| Q-2 | ~~Should the `4x stock price` filter be implemented?~~ | RESOLVED | Added to AC-10 and architecture Section 4.2. Will be implemented. |
| Q-3 | ~~Should the sidebar retain stale rows on refresh error?~~ | RESOLVED | UI Spec Section 10.2 updated: retain stale rows on refresh; full error only on initial load. |
| Q-4 | ~~HISTORY_MAP yellow color?~~ | RESOLVED | All docs use `#B9A816` (gold). Roadmap has stale value (non-blocking). |
| Q-5 | ~~Backend 3 vs 5 offerings?~~ | RESOLVED | AC-06 clarifies: backend fetches 5, frontend displays 3, rationale documented. |

**Remaining open questions: 1** (Q-1, non-blocking for implementation start)

---

## 12. Approval Checklist

### Requirements (01-REQUIREMENTS.md)
- [x] AC-05 green hex updated to `#5ce08a` -- matches UI spec
- [x] AC-06 offerings limit clarified (backend 5, frontend 3, with rationale)
- [x] 4x strike filter added to AC-10
- [x] Acceptance criteria are testable
- [x] Out of scope is acceptable
- [ ] Reviewed by human
- [ ] `registrations` endpoint prefix confirmed (Q-1, non-blocking)

### Architecture (02-ARCHITECTURE.md)
- [x] Sector abbreviation map (Appendix A) updated -- matches UI spec
- [x] `fetchDilution` signature includes `signal?: AbortSignal` -- matches roadmap
- [x] HISTORY_MAP "yellow" color is `#B9A816` -- matches UI spec
- [x] 4x strike filter documented in `get_dilution_data_v2`
- [x] Patterns are appropriate
- [x] Schemas are correct
- [ ] Reviewed by human
- [ ] "10 sub-calls" typo in Section 5.1 corrected to "9 sub-calls" (cosmetic)

### UI Spec (03-UI-SPEC.md)
- [x] Sidebar error behavior contradiction resolved (Section 10.2 updated)
- [x] HISTORY_MAP "yellow" color is `#B9A816` (Section 4.9 + Appendix B)
- [x] Flows are complete
- [x] Layouts are appropriate
- [ ] Reviewed by human

### Roadmap (04-ROADMAP.md)
- [x] Slice 9 Done criteria include `page.tsx` rendering all 10 panels
- [x] Sector abbreviation map matches canonical version
- [ ] Reviewed by human
- [ ] Utility files assigned to slices (WARNING-2, non-blocking)
- [ ] HISTORY_MAP yellow corrected from `#B96A16` to `#B9A816` in Slice 9 (WARNING-1, non-blocking)
- [ ] 4x filter mentioned in Slice 4 implementation notes (NOTE-1, non-blocking)

### Overall
- [x] All 4 blockers resolved
- [x] No new blockers identified
- [x] All risks have mitigations
- [x] 1 open question remaining (non-blocking)
- [x] Ready for implementation

---

## 13. Summary of Remaining Items (Non-Blocking)

| # | Item | Type | Document | Impact |
|---|------|------|----------|--------|
| WARNING-1 | Roadmap Slice 9 HISTORY_MAP yellow uses stale `#B96A16` instead of `#B9A816` | Cosmetic | 04-ROADMAP.md | Low -- architecture and UI spec are correct and authoritative |
| WARNING-2 | Utility files (`sectorAbbreviations.ts`, `historyMap.ts`) not in roadmap File Ownership Summary | Organizational | 04-ROADMAP.md | Low -- context makes assignment obvious |
| NOTE-1 | 4x strike filter not in roadmap Slice 4 implementation notes | Organizational | 04-ROADMAP.md | Low -- architecture docstring is the canonical reference |
| NOTE-2 | 4x filter criterion placed in AC-10 rather than AC-09 | Organizational | 01-REQUIREMENTS.md | Minimal -- criterion is clear regardless of grouping |
| NOTE-3 | Architecture Section 5.1 says "10 sub-calls" but actual gather has 9 | Typo | 02-ARCHITECTURE.md | None -- code-level spec is correct |
| Q-1 | `registrations` endpoint prefix unconfirmed | Open question | All docs | Non-blocking -- single-line fix if wrong |

All remaining items are cosmetic, organizational, or informational. None prevent implementation from proceeding.
