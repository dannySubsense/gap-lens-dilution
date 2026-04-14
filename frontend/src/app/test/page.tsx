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
// New Phase 4 component imports
import MarketStrengthBar from "@/components/MarketStrengthBar";
import TabPanel from "@/components/TabPanel";
import KeyStatsGrid from "@/components/KeyStatsGrid";
import ComplianceWarning from "@/components/ComplianceWarning";
import PumpDumpBadge from "@/components/PumpDumpBadge";
import ReverseSplitFlag from "@/components/ReverseSplitFlag";
import ResearchReport from "@/components/ResearchReport";
import FilingTitlesList from "@/components/FilingTitlesList";
import NasdaqCompliance from "@/components/NasdaqCompliance";
import FloatHistoryChart from "@/components/FloatHistoryChart";
import ReverseSplitTable from "@/components/ReverseSplitTable";
import { parseResearchReport } from "@/utils/parseResearchReport";
import { AppSettingsProvider, useAppSettings } from "@/context/AppSettingsContext";
import {
  fetchDilution, fetchGainers, fetchMassiveGainers, fetchFmpGainers,
  fetchPumpAndDump, fetchNasdaqCompliance, fetchReverseSplits,
  fetchFilingTitles, fetchHistoricalFloat, fetchResearchReport,
  fetchBatchEnrichment,
} from "@/services/api";
import type {
  DilutionResponse,
  GainerEntry,
  GainerEnrichment,
  TabId,
  TabDefinition,
  KeyStatsData,
  PumpDumpData,
  ComplianceRecord,
  ReverseSplitRecord,
  FilingTitle,
  HistoricalFloatPoint,
  ResearchReportData,
  BatchEnrichmentResult,
} from "@/types/dilution";
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

// ── Tab definitions (outside component to avoid re-creation) ─────────────────

const TAB_DEFINITIONS: TabDefinition[] = [
  { id: "summary", label: "Summary" },
  { id: "dilution", label: "Dilution" },
  { id: "intel", label: "Intel" },
  { id: "history", label: "History" },
  { id: "market", label: "Market" },
];

// ── Inner test page component ────────────────────────────────────────────

function TestPageInner() {
  // ── Existing state (same as page.tsx) ──
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [sidebarSelectedTicker, setSidebarSelectedTicker] = useState<string | null>(null);
  const [dilutionData, setDilutionData] = useState<DilutionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<{ status: number; message: string } | null>(null);
  const [selectCount, setSelectCount] = useState(0);
  const abortRef = useRef<AbortController | null>(null);

  // Gainer data
  const [tvGainers, setTvGainers] = useState<GainerEntry[]>([]);
  const [massiveGainers, setMassiveGainers] = useState<GainerEntry[]>([]);
  const [fmpGainers, setFmpGainers] = useState<GainerEntry[]>([]);

  const gainerLookup = useMemo(() => {
    const map = new Map<string, GainerEntry>();
    for (const g of [...fmpGainers, ...massiveGainers, ...tvGainers]) {
      map.set(g.ticker, g);
    }
    return map;
  }, [tvGainers, massiveGainers, fmpGainers]);

  const { settings, watchlist, setChartAssignment } = useAppSettings();
  const chartCount = settings.chartCount ?? 4;
  const chartMode = settings.chartMode;
  const chartAssignments = settings.chartAssignments;
  const [newsCollapsed, setNewsCollapsed] = useState(false);

  // ── Phase 4 state ──
  const [activeTab, setActiveTab] = useState<TabId>("summary");
  const [pumpDumpData, setPumpDumpData] = useState<PumpDumpData | null>(null);
  const [complianceRecords, setComplianceRecords] = useState<ComplianceRecord[]>([]);
  const [reverseSplits, setReverseSplits] = useState<ReverseSplitRecord[]>([]);
  const [filingTitles, setFilingTitles] = useState<FilingTitle[]>([]);
  const [historicalFloat, setHistoricalFloat] = useState<HistoricalFloatPoint[]>([]);
  const [researchReport, setResearchReport] = useState<ResearchReportData | null>(null);
  const [intelLoading, setIntelLoading] = useState(false);
  const [enrichmentData, setEnrichmentData] = useState<BatchEnrichmentResult>({});
  const intelAbortRef = useRef<AbortController | null>(null);

  const enrichmentMap = useMemo(() => {
    const map = new Map<string, GainerEnrichment>();
    for (const [ticker, data] of Object.entries(enrichmentData)) {
      map.set(ticker, data);
    }
    return map;
  }, [enrichmentData]);

  // ── loadTicker with intel fetch group ──
  const loadTicker = useCallback(async (ticker: string, clearSidebar: boolean) => {
    // Abort previous requests
    abortRef.current?.abort();
    intelAbortRef.current?.abort();
    const controller = new AbortController();
    const intelController = new AbortController();
    abortRef.current = controller;
    intelAbortRef.current = intelController;

    // Reset state
    setIsLoading(true);
    setDilutionData(null);
    setError(null);
    setActiveTab("summary");

    // Clear intel state
    setPumpDumpData(null);
    setComplianceRecords([]);
    setReverseSplits([]);
    setFilingTitles([]);
    setHistoricalFloat([]);
    setResearchReport(null);
    setIntelLoading(true);

    if (clearSidebar) {
      setSidebarSelectedTicker(null);
    }

    // Launch dilution fetch
    const result = await fetchDilution(ticker, controller.signal);

    if (controller.signal.aborted) return;

    if (result.ok) {
      setDilutionData(result.data);
      setIsLoading(false);
    } else {
      if (result.message !== "Request aborted") {
        setError({ status: result.status, message: result.message });
        setIsLoading(false);
      }
    }

    // Launch intel fetches concurrently
    const intelResults = await Promise.allSettled([
      fetchPumpAndDump(ticker, intelController.signal),
      fetchNasdaqCompliance(ticker, intelController.signal),
      fetchReverseSplits(ticker, intelController.signal),
      fetchFilingTitles(ticker, intelController.signal),
      fetchHistoricalFloat(ticker, intelController.signal),
      fetchResearchReport(ticker, intelController.signal),
    ]);

    if (intelController.signal.aborted) return;

    // Distribute results
    const [pdResult, compResult, splitResult, filingResult, floatResult, reportResult] = intelResults;

    if (pdResult.status === "fulfilled" && pdResult.value.ok) {
      setPumpDumpData(pdResult.value.data);
    }
    if (compResult.status === "fulfilled" && compResult.value.ok) {
      setComplianceRecords(compResult.value.data);
    }
    if (splitResult.status === "fulfilled" && splitResult.value.ok) {
      setReverseSplits(splitResult.value.data);
    }
    if (filingResult.status === "fulfilled" && filingResult.value.ok) {
      setFilingTitles(filingResult.value.data);
    }
    if (floatResult.status === "fulfilled" && floatResult.value.ok) {
      setHistoricalFloat(floatResult.value.data);
    }
    if (reportResult.status === "fulfilled" && reportResult.value.ok) {
      const reportData = reportResult.value.data;
      if (reportData) {
        reportData.sections = parseResearchReport(reportData.reportText);
      }
      setResearchReport(reportData);
    }

    setIntelLoading(false);
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

  const handleSearchRef = useRef(handleSearch);
  const handleGainerSelectRef = useRef(handleGainerSelect);
  useEffect(() => { handleSearchRef.current = handleSearch; }, [handleSearch]);
  useEffect(() => { handleGainerSelectRef.current = handleGainerSelect; }, [handleGainerSelect]);

  // Auto-select on mount
  useEffect(() => {
    const lastTicker = localStorage.getItem("gap-lens:lastTicker");
    if (lastTicker) {
      handleSearchRef.current(lastTicker);
      return;
    }
    if (watchlist.length > 0) {
      handleGainerSelectRef.current(watchlist[0]);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fallback: when gainer data arrives and no ticker selected
  useEffect(() => {
    if (selectedTicker) return;
    if (fmpGainers.length > 0) {
      handleGainerSelectRef.current(fmpGainers[0].ticker);
    } else if (tvGainers.length > 0) {
      handleGainerSelectRef.current(tvGainers[0].ticker);
    }
  }, [fmpGainers, tvGainers, selectedTicker]);

  // Persist selected ticker
  useEffect(() => {
    if (selectedTicker) {
      localStorage.setItem("gap-lens:lastTicker", selectedTicker);
    }
  }, [selectedTicker]);

  // Batch enrichment — fires after gainer panels report data
  useEffect(() => {
    const tickers: string[] = [];
    if (settings.gainerColumns.tradingview) {
      tickers.push(...tvGainers.slice(0, 10).map(g => g.ticker));
    }
    if (settings.gainerColumns.massive) {
      tickers.push(...massiveGainers.slice(0, 10).map(g => g.ticker));
    }
    if (settings.gainerColumns.fmp) {
      tickers.push(...fmpGainers.slice(0, 10).map(g => g.ticker));
    }

    const unique = [...new Set(tickers)];
    if (unique.length === 0) return;

    fetchBatchEnrichment(unique).then(result => {
      if (result.ok) setEnrichmentData(result.data);
    });
  }, [tvGainers, massiveGainers, fmpGainers, settings.gainerColumns]);

  // ── Derived data ──

  const keyStatsData = useMemo((): KeyStatsData => {
    if (!dilutionData) {
      return {
        sector: null, industry: null, country: null, exchange: null,
        volAvg: null, institutionalOwnership: null, float: null, outstanding: null,
        cashPerShare: null, marketCap: null, enterpriseValue: null,
        shortInterest: null, borrowRate: null, daysToCover: null,
        offeringAbility: null, offeringFrequency: null, dilutionRisk: null,
        cashNeed: null, overallOfferingRisk: null, warrantExerciseRisk: null,
      };
    }

    const d = dilutionData;
    const floatVal = typeof d.float === "number" ? d.float : typeof d.float === "string" ? parseFloat(d.float) || null : null;
    const outstandingVal = typeof d.outstanding === "number" ? d.outstanding : typeof d.outstanding === "string" ? parseFloat(d.outstanding) || null : null;
    const cashPerShare = d.estimatedCash != null && outstandingVal ? d.estimatedCash / outstandingVal : null;
    const mcVal = typeof d.marketCap === "number" ? d.marketCap : typeof d.marketCap === "string" ? parseFloat(d.marketCap) || null : null;

    // Helper to map risk level strings
    const toRisk = (val: string | null | undefined): "Low" | "Medium" | "High" | "N/A" | null => {
      const allowed: Array<"Low" | "Medium" | "High" | "N/A"> = ["Low", "Medium", "High", "N/A"];
      if (val && (allowed as string[]).includes(val)) return val as "Low" | "Medium" | "High" | "N/A";
      return null;
    };

    return {
      sector: d.sector ?? null,
      industry: d.industry ?? null,
      country: d.country ?? null,
      exchange: d.exchange ?? null,
      volAvg: d.volAvg ?? null,
      institutionalOwnership: d.institutionalOwnership ?? null,
      float: floatVal,
      outstanding: outstandingVal,
      cashPerShare,
      marketCap: mcVal,
      enterpriseValue: null,
      shortInterest: d.shortFloat ?? null,
      borrowRate: d.feeRate ?? null,
      daysToCover: d.daysToCover ?? null,
      offeringAbility: toRisk(d.offeringAbility),
      offeringFrequency: toRisk(d.offeringFrequency),
      dilutionRisk: toRisk(d.dilutionRisk),
      cashNeed: toRisk(d.cashNeed),
      overallOfferingRisk: toRisk(d.offeringRisk),
      warrantExerciseRisk: toRisk(d.warrantExercise),
    };
  }, [dilutionData]);

  const hasComplianceDeficiency = complianceRecords.length > 0;
  const hasReverseSplits = reverseSplits.length > 0;

  // ── Tab panels ──

  const tabPanels: Record<TabId, React.ReactNode> = {
    summary: (
      <div className="p-3 flex flex-col gap-3 overflow-y-auto">
        <KeyStatsGrid data={keyStatsData} isLoading={isLoading || intelLoading} />
        {(hasComplianceDeficiency || pumpDumpData || hasReverseSplits) && (
          <div className="flex flex-wrap gap-2">
            <ComplianceWarning hasDeficiency={hasComplianceDeficiency} />
            <PumpDumpBadge data={pumpDumpData} />
            <ReverseSplitFlag hasSplits={hasReverseSplits} />
          </div>
        )}
        <ResearchReport
          sections={researchReport?.sections ?? []}
          gainPercentage={researchReport?.gainPercentage ?? null}
          createdAt={researchReport?.createdAt ?? null}
        />
        <FilingTitlesList items={filingTitles} maxItems={1} isLoading={intelLoading} />
      </div>
    ),
    dilution: (
      <div className="p-2 space-y-4 overflow-y-auto">
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
      </div>
    ),
    intel: (
      <div className="p-2 space-y-4 overflow-y-auto">
        <FilingTitlesList items={filingTitles} isLoading={intelLoading} />
        <Headlines
          data={
            dilutionData
              ? mapNewsToHeadlines(dilutionData.news as unknown as RawNewsItem[])
              : null
          }
          isCollapsed={newsCollapsed}
          onToggleCollapse={() => setNewsCollapsed(c => !c)}
        />
        <NasdaqCompliance records={complianceRecords} isLoading={intelLoading} />
      </div>
    ),
    history: (
      <div className="p-2 space-y-4 overflow-y-auto">
        <FloatHistoryChart data={historicalFloat} isLoading={intelLoading} />
        <ReverseSplitTable records={reverseSplits} isLoading={intelLoading} />
        {dilutionData && dilutionData.gapStats.length > 0 && (
          <GapStats rawEntries={dilutionData.gapStats} />
        )}
      </div>
    ),
    market: (
      <MarketStrengthBar />
    ),
  };

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
              enrichmentMap={enrichmentMap}
            />
          </div>
          <div className={`w-[260px] flex flex-col h-full overflow-hidden${!settings.gainerColumns.massive ? " hidden" : ""}`}>
            <GainerPanel
              title="Massive"
              fetchFn={fetchMassiveGainers}
              selectedTicker={sidebarSelectedTicker}
              onGainerSelect={handleGainerSelect}
              onDataChange={setMassiveGainers}
              enrichmentMap={enrichmentMap}
            />
          </div>
          <div className={`w-[260px] flex flex-col h-full overflow-hidden${!settings.gainerColumns.fmp ? " hidden" : ""}`}>
            <GainerPanel
              title="FMP"
              fetchFn={fetchFmpGainers}
              selectedTicker={sidebarSelectedTicker}
              onGainerSelect={handleGainerSelect}
              onDataChange={setFmpGainers}
              enrichmentMap={enrichmentMap}
            />
          </div>
        </div>

        {/* Middle column — stacked TradingView charts */}
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

        {/* Right column — dilution data with TabPanel */}
        <div className="flex-1 flex flex-col overflow-hidden p-4">
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

          {/* TabPanel — visible when ticker is selected or loading */}
          {(isLoading || dilutionData) && (
            <TabPanel
              tabs={TAB_DEFINITIONS}
              activeTab={activeTab}
              onTabChange={setActiveTab}
              panels={tabPanels}
            />
          )}
        </div>

        {/* Watchlist column */}
        <WatchlistColumn
          selectedTicker={selectedTicker}
          onTickerActivate={handleGainerSelect}
          gainerLookup={gainerLookup}
          enrichmentMap={enrichmentMap}
        />
      </div>
    </div>
  );
}

// ── Page component ──────────────────────────────────────────────────────

export default function TestPage() {
  return (
    <AppSettingsProvider>
      <TestPageInner />
    </AppSettingsProvider>
  );
}
