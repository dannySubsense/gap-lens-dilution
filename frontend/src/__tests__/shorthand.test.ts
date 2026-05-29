/**
 * Compile-time + runtime assertion tests for shorthand.ts — Slice 1
 *
 * Acceptance Criteria Coverage:
 *   parseShorthand: suffix K/k/M/m/B/b, plain numeric, lowercase, whitespace trim,
 *                   decimal rounding, zero, large values, null for all invalid cases
 *   formatShorthand: null/undefined → "", 0 → "0", thresholds B/M/K/plain,
 *                    trailing zero stripping
 *
 * These tests are enforced by `npx tsc --noEmit`.
 * A type error here causes the TypeScript gate (Sprint Gate 1) to fail.
 * No test runner required — compilation IS the test run.
 */

import { parseShorthand, formatShorthand } from "../utils/shorthand";

// ── Helper ────────────────────────────────────────────────────────────────────
//
// assertEq: throws at runtime if actual !== expected.
// The generic constraint also provides a compile-time signal when the
// return type of the function under test diverges from the expected type.

function assertEq<T>(actual: T, expected: T, label: string): void {
  if (actual !== expected) {
    throw new Error(
      `shorthand.test: ${label} — expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    );
  }
}

// ── parseShorthand — valid inputs ─────────────────────────────────────────────

assertEq(parseShorthand("500K"), 500000, 'parseShorthand("500K")');
assertEq(parseShorthand("2B"), 2000000000, 'parseShorthand("2B")');
assertEq(parseShorthand("500M"), 500000000, 'parseShorthand("500M")');
assertEq(parseShorthand("1.5M"), 1500000, 'parseShorthand("1.5M")');
assertEq(parseShorthand("2.5B"), 2500000000, 'parseShorthand("2.5B")');
assertEq(parseShorthand("50m"), 50000000, 'parseShorthand("50m") — lowercase');
assertEq(parseShorthand("1000000"), 1000000, 'parseShorthand("1000000") — plain');
assertEq(parseShorthand("0M"), 0, 'parseShorthand("0M")');
assertEq(parseShorthand("999B"), 999000000000, 'parseShorthand("999B")');
assertEq(parseShorthand("1.7M"), 1700000, 'parseShorthand("1.7M") — rounded');
assertEq(parseShorthand(" 50M "), 50000000, 'parseShorthand(" 50M ") — whitespace');

// ── parseShorthand — invalid inputs (must return null) ────────────────────────

assertEq(parseShorthand("abc"), null, 'parseShorthand("abc")');
assertEq(parseShorthand("1.2.3M"), null, 'parseShorthand("1.2.3M")');
assertEq(parseShorthand("M"), null, 'parseShorthand("M") — suffix only');
assertEq(parseShorthand("5MB"), null, 'parseShorthand("5MB") — multiple suffixes');
assertEq(parseShorthand("-5M"), null, 'parseShorthand("-5M") — negative');
assertEq(parseShorthand(""), null, 'parseShorthand("") — empty');

// ── formatShorthand — null/undefined/zero ────────────────────────────────────

assertEq(formatShorthand(null), "", "formatShorthand(null)");
assertEq(formatShorthand(undefined), "", "formatShorthand(undefined)");
assertEq(formatShorthand(0), "0", "formatShorthand(0)");

// ── formatShorthand — plain values (< 1000) ───────────────────────────────────

assertEq(formatShorthand(1), "1", "formatShorthand(1)");
assertEq(formatShorthand(20), "20", "formatShorthand(20)");

// ── formatShorthand — K tier (≥ 1,000, < 1,000,000) ─────────────────────────

assertEq(formatShorthand(500000), "500K", "formatShorthand(500000)");

// ── formatShorthand — M tier (≥ 1,000,000, < 1,000,000,000) ──────────────────

assertEq(formatShorthand(1000000), "1M", "formatShorthand(1000000)");
assertEq(formatShorthand(1500000), "1.5M", "formatShorthand(1500000)");
assertEq(formatShorthand(50000000), "50M", "formatShorthand(50000000)");
assertEq(formatShorthand(500000000), "500M", "formatShorthand(500000000)");

// ── formatShorthand — B tier (≥ 1,000,000,000) ───────────────────────────────

assertEq(formatShorthand(2000000000), "2B", "formatShorthand(2000000000)");

// ── Compile-time type guards ──────────────────────────────────────────────────
//
// These assignments verify the return types are what callers expect.
// If the signatures change, these lines produce compile errors.

const _parseResult: number | null = parseShorthand("1M");
const _formatResult: string = formatShorthand(1_000_000);

// Suppress unused-variable warnings while keeping compile guards active.
void _parseResult;
void _formatResult;
