# INVARIANTS.md — gap-lens-dilution

Project-wide rules that apply to every forge sprint. Non-negotiable.
The forge-start workflow reads this file at session start.

---

## 1. Sprint Closure Gates

A sprint is not COMPLETE until all three pass with exit code 0:

- `cd frontend && npx tsc --noEmit` — zero TypeScript errors
- `bash scripts/run_playwright_qc.sh` — all browser tests pass
- `bash scripts/check-no-raw-hex.sh` — zero design token violations

Sprint status must not be set to COMPLETE in PROGRESS.md until all three gates pass.

---

## 2. Design Token Rules

Applies to all files in `frontend/src/components/` and `frontend/src/app/page.tsx` / `frontend/src/app/test/page.tsx`.

**Forbidden:**
- Raw hex literals (`#xxxxxx`, `#xxx`) anywhere in `.tsx` source
- Arbitrary Tailwind size classes: `text-[Xpx]`, `text-[Xrem]`
- Stock Tailwind size classes: `text-xs`, `text-sm`, `text-base`, `text-lg`, `text-xl`, `text-2xl`, `text-3xl`, `text-4xl`, `text-5xl`, `text-6xl`
- Inline `style={{ fontSize: "Xpx" }}` or `style={{ fontSize: "Xrem" }}` — use `style={{ fontSize: 'var(--font-size-...)' }}` instead
- Reserved typography tokens in production component code: `text-heading`, `text-body`, `text-display`

**Required typography tokens (role-to-token mapping):**

| Role | Token | px |
|---|---|---|
| Sub-label (uppercase tracked descriptors, column headers) | `text-label` | 10 |
| Body / value content (default text, values, list items) | `text-meta` | 12 |
| Card-level heading, zone/panel heading, header ticker | `text-section` | 13 |

**Exemptions:**
- `frontend/src/app/globals.css` — token source of truth, not scanned
- `tailwind.config.*` — config files, not scanned
- `*.test.tsx`, `*.spec.tsx`, `tests/`, `__tests__/` — test files excluded
- Lines marked `// tv-exempt` — TradingView widget constructor config
- Lines marked `// token-reserved-ok` — escape hatch requiring human orchestrator approval
- SVG `fontSize` attributes in SVG elements (e.g., `FloatHistoryChart.tsx`) — Tailwind classes cannot be applied to SVG text elements

---

## 3. Backend Patterns

Applies to all changes under `app/`.

- FMP 429 responses: silent fallback only — no retry, no `HTTPException(500)` raised
- Cache no-None contract: never store `None` in `_cache` or `_fmp_enrich_cache`
- Single uvicorn worker — in-memory cache is shared across requests; no per-request state
- No new infrastructure: no Redis, no new external services, no new databases

---

## 4. Frank QC Gate

- Frank (`@senior-qc`) is the final reviewer on both spec and code
- Verdicts are binary: **SHIP** or **HALT+FIX** — no conditional passes
- Every Frank verdict must be captured to LORE tagged `frank-verdict`

---

## 5. Scope Rules

- `get_dilution_data_v2` ticker-detail path: out of scope for Lever 1 FMP substitution
- `GainerEntry` and `WatchlistQuoteEntry` TypeScript interfaces: must not be modified
- No new npm packages without explicit human approval
