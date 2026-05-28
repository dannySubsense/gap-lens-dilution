/**
 * Runtime assertion tests for gainerFilterToParams — Slice 5
 *
 * Acceptance Criteria Coverage:
 *   AC-08: Filter query parameters sent to all three gainer endpoints with identical
 *          values; gainerFilterToParams serializes GainerFilter to URLSearchParams.
 *   AC-11: When watchlist contains tickers, `watchlist` query param is present
 *          (comma-separated). When watchlist is absent or empty, param is omitted.
 *
 * These tests are enforced by `npx tsc --noEmit` for type correctness.
 * Runtime assertions throw on value mismatches, catching serialization regressions.
 *
 * No test runner required — compilation + module execution verify correctness.
 */

import { DEFAULT_GAINER_FILTER } from "../types/dilution";
import { gainerFilterToParams } from "../services/api";

// ── Test 1: DEFAULT_GAINER_FILTER serializes all scalar fields (AC-08) ──────

{
  const params = gainerFilterToParams(DEFAULT_GAINER_FILTER);

  if (params.get("price_min") !== "1") {
    throw new Error(
      `AC-08: price_min expected "1", got "${params.get("price_min")}"`,
    );
  }
  if (params.get("price_max") !== "20") {
    throw new Error(
      `AC-08: price_max expected "20", got "${params.get("price_max")}"`,
    );
  }
  if (params.get("volume_min") !== "1000000") {
    throw new Error(
      `AC-08: volume_min expected "1000000", got "${params.get("volume_min")}"`,
    );
  }
  if (params.get("change_pct_min") !== "15") {
    throw new Error(
      `AC-08: change_pct_min expected "15", got "${params.get("change_pct_min")}"`,
    );
  }
}

// ── Test 2: DEFAULT_GAINER_FILTER serializes non-null mcapMax and floatMax ───

{
  const params = gainerFilterToParams(DEFAULT_GAINER_FILTER);

  if (params.get("mcap_max") !== "500000000") {
    throw new Error(
      `AC-08: mcap_max expected "500000000", got "${params.get("mcap_max")}"`,
    );
  }
  if (params.get("float_max") !== "50000000") {
    throw new Error(
      `AC-08: float_max expected "50000000", got "${params.get("float_max")}"`,
    );
  }
}

// ── Test 3: DEFAULT_GAINER_FILTER omits sector_exclude and country_exclude ───

{
  const params = gainerFilterToParams(DEFAULT_GAINER_FILTER);

  const sectors = params.getAll("sector_exclude");
  if (sectors.length !== 0) {
    throw new Error(
      `AC-08: sector_exclude expected empty, got [${sectors.join(", ")}]`,
    );
  }

  const countries = params.getAll("country_exclude");
  if (countries.length !== 0) {
    throw new Error(
      `AC-08: country_exclude expected empty, got [${countries.join(", ")}]`,
    );
  }
}

// ── Test 4: null mcapMax omits mcap_max param entirely ────────────────────────

{
  const filter = { ...DEFAULT_GAINER_FILTER, mcapMax: null };
  const params = gainerFilterToParams(filter);

  if (params.has("mcap_max")) {
    throw new Error(
      `AC-08: mcap_max should be absent when mcapMax is null, got "${params.get("mcap_max")}"`,
    );
  }
}

// ── Test 5: null floatMax omits float_max param entirely ──────────────────────

{
  const filter = { ...DEFAULT_GAINER_FILTER, floatMax: null };
  const params = gainerFilterToParams(filter);

  if (params.has("float_max")) {
    throw new Error(
      `AC-08: float_max should be absent when floatMax is null, got "${params.get("float_max")}"`,
    );
  }
}

// ── Test 6: non-empty sectorExclude serializes as repeated params ─────────────

{
  const filter = {
    ...DEFAULT_GAINER_FILTER,
    sectorExclude: ["Technology", "Healthcare"],
  };
  const params = gainerFilterToParams(filter);
  const sectors = params.getAll("sector_exclude");

  if (sectors.length !== 2) {
    throw new Error(
      `AC-08: sector_exclude expected 2 entries, got ${sectors.length}`,
    );
  }
  if (!sectors.includes("Technology")) {
    throw new Error(
      `AC-08: sector_exclude missing "Technology", got [${sectors.join(", ")}]`,
    );
  }
  if (!sectors.includes("Healthcare")) {
    throw new Error(
      `AC-08: sector_exclude missing "Healthcare", got [${sectors.join(", ")}]`,
    );
  }
}

// ── Test 7: non-empty countryExclude serializes as repeated params ────────────

{
  const filter = {
    ...DEFAULT_GAINER_FILTER,
    countryExclude: ["CN", "IL"],
  };
  const params = gainerFilterToParams(filter);
  const countries = params.getAll("country_exclude");

  if (countries.length !== 2) {
    throw new Error(
      `AC-08: country_exclude expected 2 entries, got ${countries.length}`,
    );
  }
  if (!countries.includes("CN")) {
    throw new Error(
      `AC-08: country_exclude missing "CN", got [${countries.join(", ")}]`,
    );
  }
  if (!countries.includes("IL")) {
    throw new Error(
      `AC-08: country_exclude missing "IL", got [${countries.join(", ")}]`,
    );
  }
}

// ── Test 8: watchlist param is comma-joined when non-empty (AC-11) ────────────

{
  const params = gainerFilterToParams(DEFAULT_GAINER_FILTER, ["AAPL", "TSLA"]);

  if (!params.has("watchlist")) {
    throw new Error(`AC-11: watchlist param should be present for ["AAPL", "TSLA"]`);
  }
  if (params.get("watchlist") !== "AAPL,TSLA") {
    throw new Error(
      `AC-11: watchlist expected "AAPL,TSLA", got "${params.get("watchlist")}"`,
    );
  }
}

// ── Test 9: watchlist param is absent when watchlist is undefined (AC-11) ─────

{
  const params = gainerFilterToParams(DEFAULT_GAINER_FILTER, undefined);

  if (params.has("watchlist")) {
    throw new Error(
      `AC-11: watchlist param should be absent when watchlist is undefined, got "${params.get("watchlist")}"`,
    );
  }
}

// ── Test 10: watchlist param is absent when watchlist is empty array (AC-11) ──

{
  const params = gainerFilterToParams(DEFAULT_GAINER_FILTER, []);

  if (params.has("watchlist")) {
    throw new Error(
      `AC-11: watchlist param should be absent when watchlist is [], got "${params.get("watchlist")}"`,
    );
  }
}
