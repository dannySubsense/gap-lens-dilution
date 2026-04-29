"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import type { GainerEntry, ApiResult, GainerEnrichment } from "@/types/dilution";
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
    isMountedRef.current = true;
    fetchAndUpdate(true).then(() => {
      if (isMountedRef.current) startInterval();
    });
    return () => {
      isMountedRef.current = false;
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
        <span className="text-accent-purple text-section font-bold">{title}</span>
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
          <p className="text-text-muted text-meta text-center py-6">No gainers found</p>
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
