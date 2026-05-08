# Slice 0 — Dilution-Rating Intraday Sampling Log

**Purpose:** Empirically verify that AskEdgar dilution-rating values are stable across a
full trading day before committing to 24h TTL in Lever 2.

**Tickers:** INHD, WALD, VERB (MULN dropped — no AskEdgar data, delisted/not covered)

---

## Sample 1 — Pre-market baseline
**Time:** 2026-05-08T12:23:34Z (08:23 EDT, pre-market)

| Ticker | overall_offering_risk | dilution | offering_ability | offering_frequency | cash_need | warrant_exercise | last_updated |
|---|---|---|---|---|---|---|---|
| INHD | High | High | High | High | Low | Low | 2026-05-08T08:02:02.814825 |
| WALD | Low | Low | Low | Low | Low | Low | 2026-05-08T08:02:02.814825 |
| VERB | Low | Low | Low | Low | Low | Low | 2026-05-08T08:02:02.814825 |

**Observation:** All three tickers share identical `last_updated` timestamp (2026-05-08T08:02:02 UTC = 04:02 EDT).
Strong evidence of a nightly batch computation job. Consistent with Danny's domain knowledge (once-a-day rating).

**Cost:** ~$0.012 (INHD was cache hit)
**Credits remaining:** ~$18.48

---

## Sample 2 — Market open
**Target time:** ~09:35 EDT | **Actual time:** 2026-05-08T15:04Z (~11:04 EDT, ~90 min into trading session)

| Ticker | overall_offering_risk | dilution | offering_ability | offering_frequency | cash_need | warrant_exercise | last_updated |
|---|---|---|---|---|---|---|---|
| INHD | High | High | High | High | Low | Low | 2026-05-08T08:02:02.814825 |
| WALD | Low | Low | Low | Low | Low | Low | 2026-05-08T08:02:02.814825 |
| VERB | Low | Low | Low | Low | Low | Low | 2026-05-08T08:02:02.814825 |

**Observation:** All `last_updated` timestamps are **identical to Sample 1** (04:02 EDT batch). Zero field changes across all three tickers after 90 minutes of active trading. Daily batch hypothesis holds.

**Cost:** ~$0.020 (INHD: $0.008, WALD: $0.007, VERB: $0.004)
**Credits remaining:** ~$17.85

---

## Sample 3 — Midday
**Target time:** ~13:00 EDT (17:00 UTC)

| Ticker | overall_offering_risk | dilution | offering_ability | offering_frequency | cash_need | warrant_exercise | last_updated |
|---|---|---|---|---|---|---|---|
| INHD | _pending_ | | | | | | |
| WALD | _pending_ | | | | | | |
| VERB | _pending_ | | | | | | |

---

## Sample 4 — Market close
**Target time:** ~16:00 EDT (20:00 UTC)

| Ticker | overall_offering_risk | dilution | offering_ability | offering_frequency | cash_need | warrant_exercise | last_updated |
|---|---|---|---|---|---|---|---|
| INHD | _pending_ | | | | | | |
| WALD | _pending_ | | | | | | |
| VERB | _pending_ | | | | | | |

---

## Verdict
_Pending completion of samples 2-4._

HALT A fires if: any field in any ticker changes value between samples.
Fallback: downgrade dilution-rating TTL from 24h → 4h in CACHE_TTL_MAP.
