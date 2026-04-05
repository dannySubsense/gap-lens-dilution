"use client";

import { useState, useCallback, useRef, KeyboardEvent } from "react";
import type { GainerEntry } from "@/types/dilution";
import { useAppSettings } from "@/context/AppSettingsContext";
import WatchlistCard from "./WatchlistCard";

// ── Selection state ───────────────────────────────────────────────────────

interface WatchlistSelectionState {
  selectedTickers: Set<string>;
  lastClickedIndex: number | null;
}

// ── Props ─────────────────────────────────────────────────────────────────

interface WatchlistColumnProps {
  selectedTicker: string | null;
  onTickerActivate: (ticker: string) => void;
  gainerLookup: Map<string, GainerEntry>;
}

// ── Component ─────────────────────────────────────────────────────────────

export default function WatchlistColumn({
  selectedTicker,
  onTickerActivate,
  gainerLookup,
}: WatchlistColumnProps) {
  const { watchlist, removeFromWatchlist, flashingTickers, columnFlashing } =
    useAppSettings();

  const [selectionState, setSelectionState] = useState<WatchlistSelectionState>({
    selectedTickers: new Set(),
    lastClickedIndex: null,
  });

  // Ref mirror so callbacks always read the latest selection state without
  // stale-closure bugs and without needing selectionState in their dep arrays.
  const selectionRef = useRef(selectionState);
  selectionRef.current = selectionState;

  // ── Multi-select handler ─────────────────────────────────────────────────

  const onMultiSelect = useCallback(
    (ticker: string, event: React.MouseEvent) => {
      const tickerIndex = watchlist.indexOf(ticker);
      const current = selectionRef.current;

      if (event.ctrlKey || event.metaKey) {
        // Ctrl/Cmd+click: toggle this ticker in selection
        setSelectionState((prev) => {
          const next = new Set(prev.selectedTickers);
          if (next.has(ticker)) {
            next.delete(ticker);
          } else {
            next.add(ticker);
          }
          return { selectedTickers: next, lastClickedIndex: tickerIndex };
        });
      } else if (event.shiftKey && current.lastClickedIndex !== null) {
        // Shift+click with a prior anchor: range select
        const start = Math.min(current.lastClickedIndex, tickerIndex);
        const end = Math.max(current.lastClickedIndex, tickerIndex);
        setSelectionState((prev) => {
          const next = new Set(prev.selectedTickers);
          for (let i = start; i <= end; i++) {
            if (watchlist[i]) next.add(watchlist[i]);
          }
          // Do NOT update lastClickedIndex on shift+click
          return { selectedTickers: next, lastClickedIndex: prev.lastClickedIndex };
        });
      } else if (event.shiftKey && current.lastClickedIndex === null) {
        // Shift+click with no prior anchor: treat like Ctrl+click (select just this card)
        setSelectionState({
          selectedTickers: new Set([ticker]),
          lastClickedIndex: tickerIndex,
        });
      } else {
        // Plain click
        if (current.selectedTickers.size > 0) {
          // Clear selection without activating
          setSelectionState({ selectedTickers: new Set(), lastClickedIndex: null });
        } else {
          // Activate ticker and record anchor so Shift+click works from here
          onTickerActivate(ticker);
          setSelectionState({ selectedTickers: new Set(), lastClickedIndex: tickerIndex });
        }
      }
    },
    [watchlist, onTickerActivate]
  );

  // ── Delete handler ────────────────────────────────────────────────────────

  const onDelete = useCallback(
    (ticker: string) => {
      const current = selectionRef.current;
      if (current.selectedTickers.has(ticker)) {
        // Remove all selected tickers
        removeFromWatchlist([...current.selectedTickers]);
      } else {
        // Remove only this ticker
        removeFromWatchlist([ticker]);
      }
      // Always reset lastClickedIndex after delete (indices shift)
      setSelectionState({ selectedTickers: new Set(), lastClickedIndex: null });
    },
    [removeFromWatchlist]
  );

  // ── Bulk delete (header trash icon or Delete key) ─────────────────────────

  const handleBulkDelete = useCallback(() => {
    removeFromWatchlist([...selectionRef.current.selectedTickers]);
    setSelectionState({ selectedTickers: new Set(), lastClickedIndex: null });
  }, [removeFromWatchlist]);

  // ── Delete key handler ────────────────────────────────────────────────────

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Delete" && selectionRef.current.selectedTickers.size > 0) {
        e.preventDefault();
        handleBulkDelete();
      }
    },
    [handleBulkDelete]
  );

  // ── Render ────────────────────────────────────────────────────────────────

  const columnClass = [
    "w-[260px] shrink-0 h-full flex flex-col bg-[#0e111a] border-l border-[#2a3447]",
    columnFlashing ? "flash-column" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={columnClass}
      tabIndex={0}
      onKeyDown={handleKeyDown}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-[#2a3447] shrink-0">
        <span className="text-[#a78bfa] text-sm font-bold">WATCHLIST</span>
        {selectionState.selectedTickers.size > 0 && (
          <button
            type="button"
            className="text-[#ff4fa6] hover:text-[#ff6fbf] text-xs p-1 rounded"
            onClick={handleBulkDelete}
            aria-label="Remove selected tickers"
            title="Remove selected"
          >
            &#128465;
          </button>
        )}
      </div>

      {/* Card list */}
      <div className="flex-1 overflow-y-auto pr-2">
        {watchlist.length === 0 ? (
          <p className="text-[#9aa7c7] text-xs text-center py-6 px-3 leading-relaxed">
            No tickers in watchlist{"\n"}
            <br />
            Click + in the toolbar
            <br />
            to add a ticker
          </p>
        ) : (
          watchlist.map((ticker) => (
            <WatchlistCard
              key={ticker}
              ticker={ticker}
              gainerData={gainerLookup.get(ticker) ?? null}
              isSelected={selectionState.selectedTickers.has(ticker)}
              isFlashing={flashingTickers.has(ticker)}
              isActive={selectedTicker === ticker}
              onActivate={onTickerActivate}
              onDelete={onDelete}
              onMultiSelect={onMultiSelect}
            />
          ))
        )}
      </div>
    </div>
  );
}
