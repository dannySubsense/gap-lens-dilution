"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { fetchWatchlistQuote, type WatchlistQuoteBatch } from "@/services/api";
import type { WatchlistQuoteEntry } from "@/types/dilution";

export interface UseWatchlistQuoteResult {
  watchlistLookup: Map<string, WatchlistQuoteEntry>;
  isLoading: boolean;
}

/**
 * useWatchlistQuote — fetch watchlist quote enrichment for non-gainer tickers.
 *
 * Triggers a single batch fetch on mount and whenever the watchlist set
 * changes (add/remove). Reorders do not trigger a new fetch — the dependency
 * key is `JSON.stringify([...watchlist].sort())` (spread before sort to avoid
 * mutating the original array held by AppSettingsContext).
 *
 * On error the previous lookup state is preserved (existing data stays
 * visible) — no error banner is wired in this sprint.
 */
export function useWatchlistQuote(
  watchlist: string[],
): UseWatchlistQuoteResult {
  const [watchlistLookup, setWatchlistLookup] = useState<
    Map<string, WatchlistQuoteEntry>
  >(() => new Map());
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Stable dep key — sorted copy so reorders don't refetch and the original
  // array (held by AppSettingsContext) is never mutated.
  const watchlistKey = useMemo(
    () => JSON.stringify([...watchlist].sort()),
    [watchlist],
  );

  useEffect(() => {
    // Empty watchlist: skip fetch, ensure isLoading is false.
    if (watchlist.length === 0) {
      // Abort any in-flight request from a previous non-empty state
      abortControllerRef.current?.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
      return;
    }

    // Abort any prior in-flight request
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    let cancelled = false;
    setIsLoading(true);

    fetchWatchlistQuote(watchlist, controller.signal).then((result) => {
      if (cancelled || controller.signal.aborted) return;
      if (result.ok) {
        const next = new Map<string, WatchlistQuoteEntry>();
        for (const [ticker, entry] of Object.entries(result.data)) {
          next.set(ticker, entry);
        }
        setWatchlistLookup(next);
      }
      // On error: leave watchlistLookup unchanged.
      setIsLoading(false);
    });

    return () => {
      cancelled = true;
      controller.abort();
    };
    // watchlistKey captures the sorted contents of `watchlist`; we want the
    // effect to re-run only when that changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchlistKey]);

  return { watchlistLookup, isLoading };
}
