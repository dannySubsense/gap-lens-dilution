/**
 * Parses a shorthand number string (e.g. "2B", "50M", "500K") to a number.
 * Returns null for empty, negative, or malformed input.
 */
export function parseShorthand(input: string): number | null {
  const trimmed = input.trim();
  if (!trimmed) return null;

  const SUFFIXES: Record<string, number> = {
    k: 1_000, K: 1_000,
    m: 1_000_000, M: 1_000_000,
    b: 1_000_000_000, B: 1_000_000_000,
  };

  const lastChar = trimmed[trimmed.length - 1];
  const multiplier = SUFFIXES[lastChar];

  let numStr: string;
  if (multiplier !== undefined) {
    numStr = trimmed.slice(0, -1);
  } else {
    numStr = trimmed;
  }

  if (!numStr) return null;

  const parsed = Number(numStr);
  if (!isFinite(parsed) || isNaN(parsed)) return null;
  if (parsed < 0) return null;

  return Math.round(parsed * (multiplier ?? 1));
}

/**
 * Formats a number to its shorthand display string (e.g. 50000000 → "50M").
 * Returns "" for null/undefined, "0" for zero, plain string for values < 1000.
 */
export function formatShorthand(value: number | null | undefined): string {
  if (value === null || value === undefined) return "";
  if (value === 0) return "0";

  if (value >= 1_000_000_000) {
    return stripTrailingZeros((value / 1_000_000_000).toFixed(2)) + "B";
  }
  if (value >= 1_000_000) {
    return stripTrailingZeros((value / 1_000_000).toFixed(2)) + "M";
  }
  if (value >= 1_000) {
    return stripTrailingZeros((value / 1_000).toFixed(2)) + "K";
  }
  return String(value);
}

function stripTrailingZeros(s: string): string {
  return s.replace(/\.?0+$/, "");
}
