"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import type { GainerEntry, ApiResult, GainerEnrichment } from "@/types/dilution";
import { DEFAULT_GAINER_FILTER } from "@/types/dilution";
import { useAppSettings } from "@/context/AppSettingsContext";
import GainerRow from "./GainerRow";

interface GainerPanelProps {
  title: string;
  fetchFn: (signal?: AbortSignal) => Promise<ApiResult<GainerEntry[]>>;
  selectedTicker: string | null;
  onGainerSelect: (ticker: string) => void;
  onDataChange?: (data: GainerEntry[]) => void;
  enrichmentMap?: Map<string, GainerEnrichment>;
}

function SkeletonRow() {
  return <div className="h-14 bg-bg-card rounded-[5px] mx-2 my-1 animate-pulse" />;
}

export default function GainerPanel({
  title,
  fetchFn,
  selectedTicker,
  onGainerSelect,
  onDataChange,
  enrichmentMap,
}: GainerPanelProps) {
  const { gainerFilter } = useAppSettings();
  const isFilterActive =
    gainerFilter.priceMin !== DEFAULT_GAINER_FILTER.priceMin ||
    gainerFilter.priceMax !== DEFAULT_GAINER_FILTER.priceMax ||
    gainerFilter.volumeMin !== DEFAULT_GAINER_FILTER.volumeMin ||
    gainerFilter.volumeMax !== DEFAULT_GAINER_FILTER.volumeMax ||
    gainerFilter.changePctMin !== DEFAULT_GAINER_FILTER.changePctMin ||
    gainerFilter.changePctMax !== DEFAULT_GAINER_FILTER.changePctMax ||
    gainerFilter.mcapMin !== DEFAULT_GAINER_FILTER.mcapMin ||
    gainerFilter.mcapMax !== DEFAULT_GAINER_FILTER.mcapMax ||
    gainerFilter.floatMin !== DEFAULT_GAINER_FILTER.floatMin ||
    gainerFilter.floatMax !== DEFAULT_GAINER_FILTER.floatMax ||
    gainerFilter.sectorExclude.length > 0 ||
    gainerFilter.countryExclude.length > 0;

  const [gainers, setGainers] = useState<GainerEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshError, setLastRefreshError] = useState<string | null>(null);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isMountedRef = useRef(true);

  const fetchAndUpdate = useCallback(async (isInitial: boolean) => {
    if (isInitial) {
      setIsLoading(true);
      setError(null);
      setLastRefreshError(null);
    }

    const result = await fetchFn();

    if (!isMountedRef.current) return;

    if (result.ok) {
      setGainers(result.data);
      onDataChange?.(result.data);
      setLastRefreshError(null);
      if (isInitial) {
        setIsLoading(false);
        setError(null);
      }
    } else {
      if (isInitial) {
        setIsLoading(false);
        setError(result.message);
      } else {
        setLastRefreshError("Refresh failed");
      }
    }
  }, [fetchFn]);

  const startInterval = useCallback(() => {
    if (intervalRef.current !== null) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(() => fetchAndUpdate(false), 60_000);
  }, [fetchAndUpdate]);

  useEffect(() => {
    if (typeof window === 'undefined') return; // useEffect is client-only in Next.js; guard is belt-and-suspenders for static export edge cases
    isMountedRef.current = true;

    function handleVisibilityChange() {
      if (document.visibilityState === 'hidden') {
        if (intervalRef.current !== null) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } else {
        fetchAndUpdate(false);
        startInterval();
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange);

    if (document.visibilityState === 'hidden') {
      // Background-tab mount: defer first fetch until visible
    } else {
      fetchAndUpdate(true).then(() => {
        if (isMountedRef.current) startInterval();
      });
    }

    return () => {
      isMountedRef.current = false;
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchFn]);

  const handleManualRefresh = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    fetchAndUpdate(false).then(() => {
      if (isMountedRef.current) startInterval();
    });
  }, [fetchAndUpdate, startInterval]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 shrink-0">
        <span className="flex items-center">
          <span className="text-accent-purple text-section font-bold">{title}</span>
          {isFilterActive && (
            <span
              aria-label="Filter active"
              className="text-label text-accent-purple border border-accent-purple rounded-full px-1.5 py-0.5 ml-2"
            >
              Filtered
            </span>
          )}
        </span>
        <div className="flex items-center gap-2">
          {isLoading ? (
            <span className="text-text-muted text-meta animate-pulse">Loading...</span>
          ) : (
            <span className="text-text-muted text-meta">{gainers.length}</span>
          )}
          <button
            type="button"
            className="text-accent-magenta hover:text-accent-magenta-hover text-meta p-1 rounded"
            onClick={handleManualRefresh}
            aria-label={`Refresh ${title}`}
          >
            &#8635;
          </button>
        </div>
      </div>

      {lastRefreshError && (
        <div className="px-3 py-1 text-negative text-meta shrink-0">{lastRefreshError}</div>
      )}

      <div className="flex-1 overflow-y-auto pr-4">
        {isLoading && (<>{[1,2,3,4,5].map(i => <SkeletonRow key={i} />)}</>)}

        {!isLoading && error !== null && (
          <div className="px-3 py-4 flex flex-col items-center gap-2">
            <p className="text-negative text-meta text-center">{error}</p>
            <button type="button" className="text-accent-magenta text-meta hover:underline" onClick={handleManualRefresh}>Retry</button>
          </div>
        )}

        {!isLoading && error === null && gainers.length === 0 && (
          <div className="flex flex-col items-center gap-1 py-6">
            <p className="text-meta text-text-muted text-center">No matching gainers</p>
            <p className="text-meta text-text-muted text-center">Adjust your Gainer Filter in Settings</p>
          </div>
        )}

        {!isLoading && error === null && gainers.length > 0 &&
          gainers.map((gainer) => (
            <GainerRow
              key={gainer.ticker}
              gainer={gainer}
              isSelected={selectedTicker === gainer.ticker}
              onClick={onGainerSelect}
              enrichmentData={enrichmentMap?.get(gainer.ticker) ?? null}
            />
          ))
        }
      </div>
    </div>
  );
}
