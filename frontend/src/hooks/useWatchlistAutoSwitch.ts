import { useEffect, useRef } from "react";
import type { ChartMode } from "@/types/dilution";

export interface UseWatchlistAutoSwitchOptions {
  watchlist: string[];
  chartMode: ChartMode;
  activeIntervals: string[];
  setChartAssignment: (interval: string, ticker: string | null) => void;
}

/**
 * Detects when a new ticker is appended to the watchlist and, in Independent
 * chart mode, switches all active chart intervals to that ticker.
 *
 * Implementation notes:
 * - Uses prevWatchlistRef to compare previous watchlist to current.
 * - Only fires when watchlist.length GREW (new ticker added).
 * - Finds the new ticker by iterating from end to find first entry not in the
 *   set of previous tickers.
 * - No-ops in Linked mode and when no new ticker is found.
 */
export function useWatchlistAutoSwitch({
  watchlist,
  chartMode,
  activeIntervals,
  setChartAssignment,
}: UseWatchlistAutoSwitchOptions): void {
  const prevWatchlistRef = useRef<string[]>([]);

  useEffect(() => {
    const prev = prevWatchlistRef.current;

    if (chartMode !== "independent") {
      prevWatchlistRef.current = [...watchlist];
      return;
    }

    if (watchlist.length <= prev.length) {
      prevWatchlistRef.current = [...watchlist];
      return;
    }

    // Find the newly-added ticker — iterate from end, first entry not in prev set
    const prevSet = new Set(prev);
    let newTicker: string | null = null;
    for (let i = watchlist.length - 1; i >= 0; i--) {
      if (!prevSet.has(watchlist[i])) {
        newTicker = watchlist[i];
        break;
      }
    }

    if (newTicker !== null) {
      for (const interval of activeIntervals) {
        setChartAssignment(interval, newTicker);
      }
    }

    prevWatchlistRef.current = [...watchlist];
  }, [watchlist, chartMode, activeIntervals, setChartAssignment]);
}
