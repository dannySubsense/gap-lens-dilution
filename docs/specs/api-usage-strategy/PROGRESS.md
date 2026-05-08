# Progress: api-usage-strategy (INTAKE #4)

## Status: IN_PROGRESS

## Slices
- [x] Slice 0: Pre-sprint verification — COMPLETE (2026-05-08)
- [x] Slice 1: FMP float sub-fetcher + enrichment cache — COMPLETE (2026-05-08, commit c160038)
- [x] Slice 2: FMP profile sub-fetcher + rewrite `_enrich_gainer` — COMPLETE (2026-05-08, commit f86f19c)
- [x] Slice 3: Lever 1 live verification — COMPLETE (2026-05-08)
- [ ] Slice 4: TTL constants + DilutionService TTL dispatch — PENDING
- [ ] Slice 5: IntelService TTL dispatch + WatchlistService update — PENDING
- [ ] Slice 6: NewsService construction — PENDING
- [ ] Slice 7: NewsService integration + press-release mapping — PENDING
- [ ] Slice 8: Sprint closure gates (TSC + Playwright) — PENDING

## Slice 0 Results
- FMP `/api/v4/shares_float`: ✅ HTTP 200, `floatShares` populated
- EDGAR Atom URL: ✅ valid Atom XML with `User-Agent: GapLens danny@dannyclarke.art`
- Dilution-rating baseline (2026-05-08T12:23Z, pre-market):
  - INHD: overall_offering_risk=High, last_updated=2026-05-08T08:02:02
  - WALD: overall_offering_risk=Low, last_updated=2026-05-08T08:02:02
  - VERB: overall_offering_risk=Low, last_updated=2026-05-08T08:02:02
  - All three share identical `last_updated` — strong evidence of daily batch job at ~04:02 EDT
- Samples 2-4 (market open, midday, close) pending — collect at 09:35, 13:00, 16:00 EDT

## Current
Slice: 3 → Issue #1 fix → Slice 4
Step: Frank Item 1 fix (all-null dict guard)
Last updated: 2026-05-08T15:10:00Z

## Fix Attempts
| Test/File | Attempts | Last Error |
|-----------|----------|------------|
| test_gainers_slice2.py::test_enrich_gainer_fmp_profile_none_fields_are_none | 1 | `_setup_enrich_mocks` used None as sentinel for default — explicit `None` arg was replaced by default dict. Fixed: `_UNSET` sentinel. |

## Notes
- Slice 0 User-Agent requirement: `User-Agent: GapLens danny@dannyclarke.art` added to 02-ARCHITECTURE.md
- Dilution-rating intraday sampling running in parallel with forge (samples at 09:35, 13:00, 16:00 EDT)
- Lever 1 forge proceeds independently — no overlap with dilution-rating TTL (Lever 2)
