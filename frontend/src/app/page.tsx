"use client";

import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import Header from "@/components/Header";
import Headlines from "@/components/Headlines";
import RiskBadges from "@/components/RiskBadges";
import OfferingAbility from "@/components/OfferingAbility";
import InPlayDilution from "@/components/InPlayDilution";
import Offerings from "@/components/Offerings";
import GapStats from "@/components/GapStats";
import JMT415Notes from "@/components/JMT415Notes";
import MgmtCommentary from "@/components/MgmtCommentary";
import Ownership from "@/components/Ownership";
import TickerSearch from "@/components/TickerSearch";
import GainerPanel from "@/components/GainerPanel";
import TradingViewChart from "@/components/TradingViewChart";
import Toolbar from "@/components/Toolbar";
import WatchlistColumn from "@/components/WatchlistColumn";
import SettingsModal from "@/components/SettingsModal";
import { AppSettingsProvider, useAppSettings } from "@/context/AppSettingsContext";
import { fetchDilution, fetchGainers, fetchMassiveGainers, fetchFmpGainers } from "@/services/api";
import type { DilutionResponse, GainerEntry } from "@/types/dilution";
import {
  buildHeaderData,
  buildRiskData,
  buildInPlayData,
  mapNewsToHeadlines,
  mapOfferings,
  mapOwnership,
  extractJMT415,
  type RawNewsItem,
} from "@/utils/dilutionMappers";

// ── Inner page component (must be inside AppSettingsProvider) ────────────

function HomeInner() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [sidebarSelectedTicker, setSidebarSelectedTicker] = useState<string | null>(null);
  const [dilutionData, setDilutionData] = useState<DilutionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<{ status: number; message: string } | null>(null);
  const [selectCount, setSelectCount] = useState(0);
  const abortRef = useRef<AbortController | null>(null);

  // Gainer data lifted for watchlist enrichment
  const [tvGainers, setTvGainers] = useState<GainerEntry[]>([]);
  const [massiveGainers, setMassiveGainers] = useState<GainerEntry[]>([]);
  const [fmpGainers, setFmpGainers] = useState<GainerEntry[]>([]);

  // gainerLookup: priority fmp → massive → tv (last-write-wins = tv)
  const gainerLookup = useMemo(() => {
    const map = new Map<string, GainerEntry>();
    for (const g of [...fmpGainers, ...massiveGainers, ...tvGainers]) {
      map.set(g.ticker, g);
    }
    return map;
  }, [tvGainers, massiveGainers, fmpGainers]);

  // Slice 5: initial context call; Slice 6: destructure settings for column visibility; Slice 8: watchlist + setChartAssignment
  const { settings, watchlist, setChartAssignment } = useAppSettings();
  const chartCount = settings.chartCount ?? 4;

  // Slice 8: derive chart mode and per-interval assignments
  const chartMode = settings.chartMode;
  const chartAssignments = settings.chartAssignments;

  // Slice 7: Headlines collapse state (not persisted)
  const [newsCollapsed, setNewsCollapsed] = useState(false);

  const loadTicker = useCallback(async (ticker: string, clearSidebar: boolean) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsLoading(true);
    setDilutionData(null);
    setError(null);

    if (clearSidebar) {
      setSidebarSelectedTicker(null);
    }

    const result = await fetchDilution(ticker, controller.signal);

    if (controller.signal.aborted) {
      return;
    }

    if (result.ok) {
      setDilutionData(result.data);
      setIsLoading(false);
    } else {
      if (result.message !== "Request aborted") {
        setError({ status: result.status, message: result.message });
        setIsLoading(false);
      }
    }
  }, []);

  const handleSearch = useCallback((ticker: string) => {
    setSelectCount(c => c + 1);
    if (!ticker.trim()) return;
    const upper = ticker.trim().toUpperCase();
    setSelectedTicker(upper);
    loadTicker(upper, true);
  }, [loadTicker]);

  const handleGainerSelect = useCallback((ticker: string) => {
    setSelectCount(c => c + 1);
    setSidebarSelectedTicker(ticker);
    setSelectedTicker(ticker);
    loadTicker(ticker, false);
  }, [loadTicker]);

  // Stable refs so mount-once effect always calls the current callback
  const handleSearchRef = useRef(handleSearch);
  const handleGainerSelectRef = useRef(handleGainerSelect);
  useEffect(() => { handleSearchRef.current = handleSearch; }, [handleSearch]);
  useEffect(() => { handleGainerSelectRef.current = handleGainerSelect; }, [handleGainerSelect]);

  // Auto-select on mount: last ticker → first watchlist entry → wait for gainer data
  useEffect(() => {
    const lastTicker = localStorage.getItem("gap-lens:lastTicker");
    if (lastTicker) {
      handleSearchRef.current(lastTicker);
      return;
    }
    if (watchlist.length > 0) {
      handleGainerSelectRef.current(watchlist[0]);
    }
    // Otherwise the gainer-data fallback effect below will handle it
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fallback: when gainer data arrives and no ticker has been selected yet, take the first one
  useEffect(() => {
    if (selectedTicker) return;
    if (fmpGainers.length > 0) {
      handleGainerSelectRef.current(fmpGainers[0].ticker);
    } else if (tvGainers.length > 0) {
      handleGainerSelectRef.current(tvGainers[0].ticker);
    }
  }, [fmpGainers, tvGainers, selectedTicker]);

  // Persist selected ticker to localStorage whenever it changes
  useEffect(() => {
    if (selectedTicker) {
      localStorage.setItem("gap-lens:lastTicker", selectedTicker);
    }
  }, [selectedTicker]);

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#0e111a]">
      <Toolbar activeTicker={selectedTicker} />
      <SettingsModal />

      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar — triple gainers columns */}
        <div className="shrink-0 flex h-full overflow-hidden bg-[#0e111a]">
          <div className={`w-[260px] flex flex-col h-full overflow-hidden${!settings.gainerColumns.tradingview ? " hidden" : ""}`}>
            <GainerPanel
              title="TradingView"
              fetchFn={fetchGainers}
              selectedTicker={sidebarSelectedTicker}
              onGainerSelect={handleGainerSelect}
              onDataChange={setTvGainers}
            />
          </div>
          <div className={`w-[260px] flex flex-col h-full overflow-hidden${!settings.gainerColumns.massive ? " hidden" : ""}`}>
            <GainerPanel
              title="Massive"
              fetchFn={fetchMassiveGainers}
              selectedTicker={sidebarSelectedTicker}
              onGainerSelect={handleGainerSelect}
              onDataChange={setMassiveGainers}
            />
          </div>
          <div className={`w-[260px] flex flex-col h-full overflow-hidden${!settings.gainerColumns.fmp ? " hidden" : ""}`}>
            <GainerPanel
              title="FMP"
              fetchFn={fetchFmpGainers}
              selectedTicker={sidebarSelectedTicker}
              onGainerSelect={handleGainerSelect}
              onDataChange={setFmpGainers}
            />
          </div>
        </div>

        {/* Middle column — stacked TradingView charts, no scroll */}
        <div className="flex-1 flex flex-col h-full p-2 gap-1 overflow-hidden">
          {[
            { interval: "5", label: "5 Min" },
            { interval: "15", label: "15 Min" },
            { interval: "D", label: "Daily" },
            { interval: "M", label: "Monthly" },
          ].slice(0, chartCount).map((chart) => (
            <TradingViewChart
              key={chart.interval}
              ticker={selectedTicker}
              selectCount={selectCount}
              interval={chart.interval}
              label={chart.label}
              overrideTicker={chartMode === "independent" ? (chartAssignments[chart.interval] ?? null) : null}
              showDropdown={chartMode === "independent"}
              watchlistTickers={watchlist}
              onTickerOverride={(iv, t) => setChartAssignment(iv, t)}
            />
          ))}
        </div>

        {/* Right column — dilution data */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <TickerSearch onSearch={handleSearch} />

          {/* Idle state */}
          {!selectedTicker && !isLoading && !error && (
            <p className="text-[#9aa7c7] text-sm text-center mt-16">
              Search a ticker or click a gainer to begin.
            </p>
          )}

          {/* Error state */}
          {error && (
            <div className="bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5">
              <p className="text-[#ff6b6b] text-sm">{error.message}</p>
              <button
                onClick={() => selectedTicker && loadTicker(selectedTicker, false)}
                className="mt-3 text-xs text-[#ff4fa6] hover:underline"
              >
                Retry
              </button>
            </div>
          )}

          {/* Loaded/loading states — dilution components */}
          {(isLoading || dilutionData) && (
            <>
              <Header data={dilutionData ? buildHeaderData(dilutionData) : null} />
              <Headlines
                data={
                  dilutionData
                    ? mapNewsToHeadlines(dilutionData.news as unknown as RawNewsItem[])
                    : null
                }
                isCollapsed={newsCollapsed}
                onToggleCollapse={() => setNewsCollapsed(c => !c)}
              />
              <RiskBadges data={dilutionData ? buildRiskData(dilutionData) : null} />
              <OfferingAbility
                offeringAbilityDesc={dilutionData?.offeringAbilityDesc ?? null}
              />
              <InPlayDilution data={dilutionData ? buildInPlayData(dilutionData) : null} />
              {dilutionData && dilutionData.offerings.length > 0 && (
                <Offerings
                  entries={mapOfferings(dilutionData.offerings, dilutionData.stockPrice ?? null)}
                  stockPrice={dilutionData.stockPrice ?? null}
                />
              )}
              {dilutionData && dilutionData.gapStats.length > 0 && (
                <GapStats rawEntries={dilutionData.gapStats} />
              )}
              <JMT415Notes
                data={
                  dilutionData
                    ? extractJMT415(dilutionData.news as unknown as RawNewsItem[])
                    : null
                }
              />
              {dilutionData && dilutionData.mgmtCommentary && (
                <MgmtCommentary text={dilutionData.mgmtCommentary} />
              )}
              {dilutionData && dilutionData.ownership && (
                <Ownership data={mapOwnership(dilutionData.ownership)} />
              )}
            </>
          )}
        </div>

        {/* Watchlist column — 4th column, far right */}
        <WatchlistColumn
          selectedTicker={selectedTicker}
          onTickerActivate={handleGainerSelect}
          gainerLookup={gainerLookup}
        />
      </div>
    </div>
  );
}

// ── Page component ────────────────────────────────────────────────────────

export default function Home() {
  return (
    <AppSettingsProvider>
      <HomeInner />
    </AppSettingsProvider>
  );
}
