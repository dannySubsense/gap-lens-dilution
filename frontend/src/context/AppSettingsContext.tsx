"use client";

import React, {
  createContext,
  useContext,
  useReducer,
  useState,
  useEffect,
} from "react";

import {
  AppSettings,
  DEFAULT_SETTINGS,
  STORAGE_KEYS,
  WatchlistAddResult,
  GainerColumnVisibility,
  ChartMode,
} from "@/types/dilution";

// ── Context Value Interface ───────────────────────────────────────────────────

interface AppSettingsContextValue {
  // Settings
  settings: AppSettings;
  updateGainerColumns: (columns: Partial<GainerColumnVisibility>) => void;
  setChartMode: (mode: ChartMode) => void;
  setChartAssignment: (interval: string, ticker: string | null) => void;
  setChartCount: (count: 2 | 3 | 4) => void;

  // Settings modal open/close
  isSettingsOpen: boolean;
  openSettings: () => void;
  closeSettings: () => void;

  // Watchlist
  watchlist: string[];
  addToWatchlist: (ticker: string) => WatchlistAddResult;
  removeFromWatchlist: (tickers: string[]) => void;

  // Flash feedback (UI-only, not persisted)
  flashingTickers: Set<string>;
  columnFlashing: boolean;
}

// ── Reducer Types ─────────────────────────────────────────────────────────────

interface PersistedState {
  settings: AppSettings;
  watchlist: string[];
}

type ReducerAction =
  | { type: "INIT"; state: PersistedState }
  | { type: "UPDATE_GAINER_COLUMNS"; columns: Partial<GainerColumnVisibility> }
  | { type: "SET_CHART_MODE"; mode: ChartMode }
  | { type: "SET_CHART_ASSIGNMENT"; interval: string; ticker: string | null }
  | { type: "SET_CHART_COUNT"; count: 2 | 3 | 4 }
  | { type: "ADD_TO_WATCHLIST"; ticker: string }
  | { type: "REMOVE_FROM_WATCHLIST"; tickers: string[] };

// ── Reducer ───────────────────────────────────────────────────────────────────

function reducer(state: PersistedState, action: ReducerAction): PersistedState {
  switch (action.type) {
    case "INIT":
      return action.state;

    case "UPDATE_GAINER_COLUMNS":
      return {
        ...state,
        settings: {
          ...state.settings,
          gainerColumns: {
            ...state.settings.gainerColumns,
            ...action.columns,
          },
        },
      };

    case "SET_CHART_MODE":
      return {
        ...state,
        settings: {
          ...state.settings,
          chartMode: action.mode,
        },
      };

    case "SET_CHART_ASSIGNMENT":
      return {
        ...state,
        settings: {
          ...state.settings,
          chartAssignments: {
            ...state.settings.chartAssignments,
            [action.interval]: action.ticker,
          },
        },
      };

    case "SET_CHART_COUNT":
      return {
        ...state,
        settings: {
          ...state.settings,
          chartCount: action.count,
        },
      };

    case "ADD_TO_WATCHLIST":
      return {
        ...state,
        watchlist: [...state.watchlist, action.ticker],
      };

    case "REMOVE_FROM_WATCHLIST": {
      const tickersToRemove = new Set(action.tickers);
      const newWatchlist = state.watchlist.filter(
        (t) => !tickersToRemove.has(t)
      );
      // Also null out any chartAssignments that match removed tickers
      const updatedAssignments: Record<string, string | null> = {};
      for (const [interval, assigned] of Object.entries(
        state.settings.chartAssignments
      )) {
        updatedAssignments[interval] =
          assigned !== null && tickersToRemove.has(assigned) ? null : assigned;
      }
      return {
        ...state,
        watchlist: newWatchlist,
        settings: {
          ...state.settings,
          chartAssignments: updatedAssignments,
        },
      };
    }

    default:
      return state;
  }
}

// ── SSR-safe initial state (no localStorage access) ──────────────────────────

const INITIAL_STATE: PersistedState = {
  settings: DEFAULT_SETTINGS,
  watchlist: [],
};

// ── Context ───────────────────────────────────────────────────────────────────

const AppSettingsContext = createContext<AppSettingsContextValue | null>(null);

// ── Provider ──────────────────────────────────────────────────────────────────

export function AppSettingsProvider({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  // Initialize with static defaults so SSR and first client render match.
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);

  // hydrated becomes true after the client-side localStorage read completes.
  const [hydrated, setHydrated] = useState(false);

  // UI-only state (not persisted)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [flashingTickers, setFlashingTickers] = useState<Set<string>>(
    new Set()
  );
  const [columnFlashing, setColumnFlashing] = useState(false);

  // Read localStorage on mount and replace state with persisted values.
  useEffect(() => {
    let settings: AppSettings = DEFAULT_SETTINGS;
    let watchlist: string[] = [];

    try {
      const rawSettings = localStorage.getItem(STORAGE_KEYS.SETTINGS);
      const parsed = JSON.parse(rawSettings ?? "null");
      if (parsed !== null && typeof parsed === "object") {
        settings = parsed as AppSettings;
      }
    } catch {
      // Parse failure: fall back to DEFAULT_SETTINGS
    }

    try {
      const rawWatchlist = localStorage.getItem(STORAGE_KEYS.WATCHLIST);
      const parsed = JSON.parse(rawWatchlist ?? "null");
      if (Array.isArray(parsed)) {
        watchlist = parsed as string[];
      }
    } catch {
      // Parse failure: fall back to empty array
    }

    dispatch({ type: "INIT", state: { settings, watchlist } });
    setHydrated(true);
  }, []);

  // Write to localStorage on every state change — only after hydration so we
  // never overwrite persisted values with DEFAULT_SETTINGS on the initial mount.
  useEffect(() => {
    if (!hydrated) return;

    try {
      localStorage.setItem(
        STORAGE_KEYS.SETTINGS,
        JSON.stringify(state.settings)
      );
    } catch {
      // Silently discard quota or write errors
    }

    try {
      localStorage.setItem(
        STORAGE_KEYS.WATCHLIST,
        JSON.stringify(state.watchlist)
      );
    } catch {
      // Silently discard quota or write errors
    }
  }, [state, hydrated]);

  // ── Action Handlers ─────────────────────────────────────────────────────────

  function updateGainerColumns(columns: Partial<GainerColumnVisibility>): void {
    dispatch({ type: "UPDATE_GAINER_COLUMNS", columns });
  }

  function setChartMode(mode: ChartMode): void {
    dispatch({ type: "SET_CHART_MODE", mode });
  }

  function setChartAssignment(
    interval: string,
    ticker: string | null
  ): void {
    dispatch({ type: "SET_CHART_ASSIGNMENT", interval, ticker });
  }

  function setChartCount(count: 2 | 3 | 4): void {
    dispatch({ type: "SET_CHART_COUNT", count });
  }

  function openSettings(): void {
    setIsSettingsOpen(true);
  }

  function closeSettings(): void {
    setIsSettingsOpen(false);
  }

  function addToWatchlist(ticker: string): WatchlistAddResult {
    const upper = ticker.toUpperCase();

    if (state.watchlist.length >= 20) {
      return { outcome: "full" };
    }

    if (state.watchlist.includes(upper)) {
      // Flash the duplicate ticker for 600ms
      setFlashingTickers((prev) => new Set([...prev, upper]));
      setTimeout(() => {
        setFlashingTickers((prev) => {
          const next = new Set(prev);
          next.delete(upper);
          return next;
        });
      }, 600);
      return { outcome: "duplicate", ticker: upper };
    }

    dispatch({ type: "ADD_TO_WATCHLIST", ticker: upper });
    // Flash the column for 600ms on successful add
    setColumnFlashing(true);
    setTimeout(() => {
      setColumnFlashing(false);
    }, 600);
    return { outcome: "added" };
  }

  function removeFromWatchlist(tickers: string[]): void {
    dispatch({ type: "REMOVE_FROM_WATCHLIST", tickers });
  }

  const value: AppSettingsContextValue = {
    settings: state.settings,
    updateGainerColumns,
    setChartMode,
    setChartAssignment,
    setChartCount,
    isSettingsOpen,
    openSettings,
    closeSettings,
    watchlist: state.watchlist,
    addToWatchlist,
    removeFromWatchlist,
    flashingTickers,
    columnFlashing,
  };

  return (
    <AppSettingsContext.Provider value={value}>
      {children}
    </AppSettingsContext.Provider>
  );
}

// ── Consumer Hook ─────────────────────────────────────────────────────────────

export function useAppSettings(): AppSettingsContextValue {
  const ctx = useContext(AppSettingsContext);
  if (!ctx) {
    throw new Error("useAppSettings must be used inside AppSettingsProvider");
  }
  return ctx;
}
