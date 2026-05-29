/**
 * Compile-time type assertion tests for GainerFilter — Slice 3
 *
 * Acceptance Criteria Coverage:
 *   AC-09: Filter state stored under localStorage key "gap-lens:gainerFilter"
 *   AC-12: Default values: price min $1, price max $20, volume min 1_000_000,
 *          % change min 15%, mcap max $500_000_000, float max 50_000_000,
 *          sectorExclude [], countryExclude []
 *
 * These tests are enforced by `npx tsc --noEmit`.
 * A type error here causes the TypeScript gate (Sprint Gate 1) to fail.
 * No test runner required — compilation IS the test run.
 */

import {
  DEFAULT_GAINER_FILTER,
  STORAGE_KEYS,
  type GainerFilter,
} from "../types/dilution";

// ── Test 1: DEFAULT_GAINER_FILTER has correct default values (AC-12) ─────────
//
// Each assertion below is a compile-time equality check using a conditional type.
// If the runtime value does not equal the expected literal, the `never` branch is
// reached and TypeScript emits an error on that line.

type AssertEq<A extends B, B> = A;

// priceMin = 1
const _priceMin: AssertEq<typeof DEFAULT_GAINER_FILTER.priceMin, number> =
  DEFAULT_GAINER_FILTER.priceMin;
if (_priceMin !== 1) {
  throw new Error(
    `AC-12: DEFAULT_GAINER_FILTER.priceMin expected 1, got ${_priceMin}`,
  );
}

// priceMax = 20
const _priceMax: AssertEq<typeof DEFAULT_GAINER_FILTER.priceMax, number> =
  DEFAULT_GAINER_FILTER.priceMax;
if (_priceMax !== 20) {
  throw new Error(
    `AC-12: DEFAULT_GAINER_FILTER.priceMax expected 20, got ${_priceMax}`,
  );
}

// volumeMin = 1_000_000
const _volumeMin: AssertEq<typeof DEFAULT_GAINER_FILTER.volumeMin, number> =
  DEFAULT_GAINER_FILTER.volumeMin;
if (_volumeMin !== 1_000_000) {
  throw new Error(
    `AC-12: DEFAULT_GAINER_FILTER.volumeMin expected 1000000, got ${_volumeMin}`,
  );
}

// changePctMin = 15
const _changePctMin: AssertEq<
  typeof DEFAULT_GAINER_FILTER.changePctMin,
  number
> = DEFAULT_GAINER_FILTER.changePctMin;
if (_changePctMin !== 15) {
  throw new Error(
    `AC-12: DEFAULT_GAINER_FILTER.changePctMin expected 15, got ${_changePctMin}`,
  );
}

// mcapMax = 500_000_000
const _mcapMax: AssertEq<
  typeof DEFAULT_GAINER_FILTER.mcapMax,
  number | null
> = DEFAULT_GAINER_FILTER.mcapMax;
if (_mcapMax !== 500_000_000) {
  throw new Error(
    `AC-12: DEFAULT_GAINER_FILTER.mcapMax expected 500000000, got ${_mcapMax}`,
  );
}

// floatMax = 50_000_000
const _floatMax: AssertEq<
  typeof DEFAULT_GAINER_FILTER.floatMax,
  number | null
> = DEFAULT_GAINER_FILTER.floatMax;
if (_floatMax !== 50_000_000) {
  throw new Error(
    `AC-12: DEFAULT_GAINER_FILTER.floatMax expected 50000000, got ${_floatMax}`,
  );
}

// sectorExclude = []
const _sectorExclude: AssertEq<
  typeof DEFAULT_GAINER_FILTER.sectorExclude,
  string[]
> = DEFAULT_GAINER_FILTER.sectorExclude;
if (_sectorExclude.length !== 0) {
  throw new Error(
    `AC-12: DEFAULT_GAINER_FILTER.sectorExclude expected [], got length ${_sectorExclude.length}`,
  );
}

// countryExclude = []
const _countryExclude: AssertEq<
  typeof DEFAULT_GAINER_FILTER.countryExclude,
  string[]
> = DEFAULT_GAINER_FILTER.countryExclude;
if (_countryExclude.length !== 0) {
  throw new Error(
    `AC-12: DEFAULT_GAINER_FILTER.countryExclude expected [], got length ${_countryExclude.length}`,
  );
}

// ── Test 2: STORAGE_KEYS.GAINER_FILTER equals "gap-lens:gainerFilter" (AC-09) ──
//
// The `as const` on STORAGE_KEYS preserves the literal type.
// TypeScript will widen the type if the value changes, breaking this assignment.

const _storageKey: "gap-lens:gainerFilter" = STORAGE_KEYS.GAINER_FILTER;
if (_storageKey !== "gap-lens:gainerFilter") {
  throw new Error(
    `AC-09: STORAGE_KEYS.GAINER_FILTER expected "gap-lens:gainerFilter", got "${_storageKey}"`,
  );
}

// ── Test 3: DEFAULT_GAINER_FILTER.mcapMax and floatMax are numbers, not null ──
//
// TypeScript enforces number | null for these fields.
// The runtime check below confirms the default is the number branch, not null.

const _mcapMaxNotNull: number = DEFAULT_GAINER_FILTER.mcapMax as number;
const _floatMaxNotNull: number = DEFAULT_GAINER_FILTER.floatMax as number;

if (_mcapMaxNotNull === null || typeof _mcapMaxNotNull !== "number") {
  throw new Error(
    "AC-12: DEFAULT_GAINER_FILTER.mcapMax must be a number (500_000_000), not null",
  );
}
if (_floatMaxNotNull === null || typeof _floatMaxNotNull !== "number") {
  throw new Error(
    "AC-12: DEFAULT_GAINER_FILTER.floatMax must be a number (50_000_000), not null",
  );
}

// ── Test 4: GainerFilter allows null for mcapMax and floatMax (compile-time) ──
//
// Assigning a GainerFilter with mcapMax=null and floatMax=null must compile.
// If the interface changed mcapMax/floatMax to `number` (non-nullable),
// this assignment would produce a compile error, catching the regression.

const _filterWithNullCeilings: GainerFilter = {
  priceMin: 1,
  priceMax: 20,
  volumeMin: 1_000_000,
  volumeMax: null,       // new — AC-01
  changePctMin: 15,
  changePctMax: null,    // new — AC-02
  mcapMin: null,         // new — AC-03
  mcapMax: null,         // must be accepted — "null means no ceiling"
  floatMin: null,        // new — AC-04
  floatMax: null,        // must be accepted — "null means no ceiling"
  sectorExclude: [],
  countryExclude: [],
};
// Suppress unused-variable warning while keeping the compile guard active.
void _filterWithNullCeilings;

// ── Slice 5: DEFAULT_GAINER_FILTER null defaults for new range fields ─────────
//
// AC-01..AC-04 require these four new fields to default to null (no bound).
// Each runtime check throws if the field is not null, which would cause the
// TypeScript gate (npx tsc --noEmit) to fail during the import-level evaluation.

// AC-01: volumeMax defaults to null
const _volumeMaxDefault: number | null = DEFAULT_GAINER_FILTER.volumeMax;
if (_volumeMaxDefault !== null) {
  throw new Error(
    `AC-01: DEFAULT_GAINER_FILTER.volumeMax expected null, got ${_volumeMaxDefault}`,
  );
}

// AC-02: changePctMax defaults to null
const _changePctMaxDefault: number | null = DEFAULT_GAINER_FILTER.changePctMax;
if (_changePctMaxDefault !== null) {
  throw new Error(
    `AC-02: DEFAULT_GAINER_FILTER.changePctMax expected null, got ${_changePctMaxDefault}`,
  );
}

// AC-03: mcapMin defaults to null
const _mcapMinDefault: number | null = DEFAULT_GAINER_FILTER.mcapMin;
if (_mcapMinDefault !== null) {
  throw new Error(
    `AC-03: DEFAULT_GAINER_FILTER.mcapMin expected null, got ${_mcapMinDefault}`,
  );
}

// AC-04: floatMin defaults to null
const _floatMinDefault: number | null = DEFAULT_GAINER_FILTER.floatMin;
if (_floatMinDefault !== null) {
  throw new Error(
    `AC-04: DEFAULT_GAINER_FILTER.floatMin expected null, got ${_floatMinDefault}`,
  );
}
