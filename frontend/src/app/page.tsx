"use client";

import { useState, useRef, useCallback, useMemo } from "react";
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
import type {
  DilutionResponse,
  HeaderData,
  Headline,
  RiskAssessment,
  RiskLevel,
  InPlayDilutionData,
  WarrantItem,
  ConvertibleItem,
  JMT415Note,
  FilingType,
  OfferingEntry,
  OwnershipData,
  OwnerEntry,
  ChartAnalysis,
  GainerEntry,
} from "@/types/dilution";

// ── Number formatting helpers ─────────────────────────────────────────────

function formatNum(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2).replace(/\.?0+$/, "")}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2).replace(/\.?0+$/, "")}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

function parseNumericString(s: string | null): number | null {
  if (!s) return null;
  // Strip leading $ and trailing multiplier letters, then parse
  const cleaned = s.replace(/[$,]/g, "").trim();
  const match = cleaned.match(/^([\d.]+)([KkMmBb]?)$/);
  if (!match) return null;
  const base = parseFloat(match[1]);
  const suffix = match[2].toUpperCase();
  if (suffix === "K") return base * 1_000;
  if (suffix === "M") return base * 1_000_000;
  if (suffix === "B") return base * 1_000_000_000;
  return base;
}

function safeRiskLevel(value: string | null): RiskLevel {
  const allowed: RiskLevel[] = ["Low", "Medium", "High", "N/A"];
  if (value && (allowed as string[]).includes(value)) return value as RiskLevel;
  return "N/A";
}

// ── Helper: map raw API news item to Headline ─────────────────────────────

// The backend may return news with snake_case fields; map them to Headline shape.
interface RawNewsItem {
  form_type?: string;
  filed_at?: string;
  created_at?: string;
  title?: string;
  summary?: string;
  // Already-mapped fields (if backend already conforms)
  filingType?: string;
  filedAt?: string;
  headline?: string;
}

const VALID_FILING_TYPES: FilingType[] = [
  "6-K", "8-K", "S-1", "10-K", "10-Q", "SC 13D", "SC 13G", "GROK", "news", "jmt415",
];

function toFilingType(raw: string | undefined): FilingType {
  if (!raw) return "news";
  if ((VALID_FILING_TYPES as string[]).includes(raw)) return raw as FilingType;
  return "news";
}

function mapNewsItem(item: RawNewsItem): Headline {
  const filingType = toFilingType(item.filingType ?? item.form_type);
  const filedAt = item.filedAt ?? item.filed_at ?? item.created_at ?? new Date().toISOString();
  const headline = item.headline ?? item.title ?? item.summary ?? "";
  return { filingType, filedAt, headline };
}

// ── buildHeaderData ───────────────────────────────────────────────────────

function toDisplayNum(val: any): string {
  if (val === null || val === undefined) return "—";
  if (typeof val === "number") return formatNum(val);
  if (typeof val === "string") {
    const parsed = parseNumericString(val);
    return parsed !== null ? formatNum(parsed) : val;
  }
  return "—";
}

function buildHeaderData(d: DilutionResponse): HeaderData {
  return {
    ticker: d.ticker,
    float: toDisplayNum(d.float),
    outstandingShares: toDisplayNum(d.outstanding),
    marketCap: toDisplayNum(d.marketCap),
    sector: d.sector ?? d.industry ?? "—",
    country: d.country ?? "—",
    overallRisk: safeRiskLevel(d.offeringRisk),
    stockPrice: d.stockPrice ?? null,
    chartAnalysis: mapChartAnalysis(d.chartAnalysis),
  };
}

// ── buildRiskData ─────────────────────────────────────────────────────────

function buildRiskData(d: DilutionResponse): RiskAssessment {
  return {
    overallRisk: safeRiskLevel(d.offeringRisk),
    offering: safeRiskLevel(d.offeringAbility),
    dilution: safeRiskLevel(d.dilutionRisk),
    frequency: safeRiskLevel(d.offeringFrequency),
    cashNeed: safeRiskLevel(d.cashNeed),
    warrants: safeRiskLevel(d.warrantExercise),
  };
}

// ── buildInPlayData ───────────────────────────────────────────────────────

function buildInPlayData(d: DilutionResponse): InPlayDilutionData {
  const stockPrice = d.stockPrice ?? null;

  const warrants: WarrantItem[] = (d.warrants ?? []).map((w) => {
    const strike = w.warrants_exercise_price ?? 0;
    return {
      details: w.details ?? "",
      issueDate: w.filed_at ? w.filed_at.slice(0, 7) : "—",
      remaining: w.warrants_remaining ?? 0,
      strikePrice: strike,
      filedDate: w.filed_at ? w.filed_at.slice(0, 10) : "—",
      registered: w.registered ?? "—",
      inTheMoney: stockPrice !== null && strike > 0 ? strike <= stockPrice : false,
    };
  });

  const convertibles: ConvertibleItem[] = (d.convertibles ?? []).map((c) => {
    const convPrice = c.conversion_price ?? 0;
    return {
      details: c.details ?? "",
      sharesRemaining: c.underlying_shares_remaining ?? 0,
      conversionPrice: convPrice,
      filedDate: c.filed_at ? c.filed_at.slice(0, 10) : "—",
      registered: c.registered ?? "—",
      inTheMoney: stockPrice !== null && convPrice > 0 ? convPrice <= stockPrice : false,
    };
  });

  return { warrants, convertibles, stockPrice };
}

// ── extractJMT415 ─────────────────────────────────────────────────────────

function extractJMT415(news: Headline[] | RawNewsItem[]): JMT415Note[] {
  const rawItems = news as RawNewsItem[];
  const jmtItems = rawItems.filter(
    (item) => (item.form_type ?? item.filingType) === "jmt415"
  );

  return jmtItems.map((item) => {
    const date = (item.filed_at ?? item.filedAt ?? "").slice(0, 10);
    const rawText = item.title ?? item.headline ?? item.summary ?? "";
    const content = rawText ? rawText.split("\n").filter(Boolean) : [];
    return {
      date,
      ticker: "",
      content,
    };
  });
}

// ── mapNewsToHeadlines ────────────────────────────────────────────────────

function mapNewsToHeadlines(news: Headline[] | RawNewsItem[]): Headline[] {
  return (news as RawNewsItem[]).map(mapNewsItem);
}

// ── mapOfferings ─────────────────────────────────────────────────────────
// API returns snake_case; component expects camelCase + computed fields

function mapOfferings(raw: any[], stockPrice: number | null): OfferingEntry[] {
  return raw.map((o) => {
    const sp = o.share_price ?? o.sharePrice ?? null;
    const headline = o.headline ?? "—";
    return {
      headline,
      offeringAmount: o.offering_amount ?? o.offeringAmount ?? null,
      sharePrice: sp,
      sharesAmount: o.shares_amount ?? o.sharesAmount ?? null,
      warrantsAmount: o.warrants_amount ?? o.warrantsAmount ?? null,
      filedAt: o.filed_at ?? o.filedAt ?? null,
      isAtmUsed: headline.toUpperCase().includes("ATM USED"),
      inTheMoney: sp !== null && stockPrice !== null && sp > 0 && stockPrice > 0 && sp <= stockPrice,
    };
  });
}

// ── mapOwnership ─────────────────────────────────────────────────────────

function mapOwnership(raw: any | null): OwnershipData | null {
  if (!raw) return null;
  const owners: OwnerEntry[] = (raw.owners ?? []).map((o: any) => ({
    ownerName: o.owner_name ?? o.ownerName ?? "—",
    title: o.title ?? o.owner_type ?? "—",
    commonSharesAmount: o.common_shares_amount ?? o.commonSharesAmount ?? null,
    documentUrl: o.document_url ?? o.documentUrl ?? null,
  }));
  if (owners.length === 0) return null;
  return {
    reportedDate: raw.reported_date ?? raw.reportedDate ?? "—",
    owners,
  };
}

// ── mapChartAnalysis ─────────────────────────────────────────────────────

const HISTORY_MAP: Record<string, { label: string; badgeColor: string }> = {
  green: { label: "Strong", badgeColor: "#2F7D57" },
  yellow: { label: "Semi-Strong", badgeColor: "#B9A816" },
  orange: { label: "Mixed", badgeColor: "#B96A16" },
  red: { label: "Fader", badgeColor: "#A93232" },
};

function mapChartAnalysis(raw: any | null): ChartAnalysis | null {
  if (!raw) return null;
  const rating = raw.rating;
  if (!rating || !HISTORY_MAP[rating]) return null;
  const { label, badgeColor } = HISTORY_MAP[rating];
  return { rating, label, badgeColor };
}

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

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#0e111a]">
      <Toolbar activeTicker={selectedTicker} />
      <SettingsModal />

      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar — triple gainers columns */}
        <div className="shrink-0 border-r border-[#2a3447] flex h-full overflow-hidden bg-[#0e111a]">
          <div className={`w-[260px] border-r border-[#2a3447] flex flex-col h-full overflow-hidden${!settings.gainerColumns.tradingview ? " hidden" : ""}`}>
            <GainerPanel
              title="TradingView"
              fetchFn={fetchGainers}
              selectedTicker={sidebarSelectedTicker}
              onGainerSelect={handleGainerSelect}
              onDataChange={setTvGainers}
            />
          </div>
          <div className={`w-[260px] border-r border-[#2a3447] flex flex-col h-full overflow-hidden${!settings.gainerColumns.massive ? " hidden" : ""}`}>
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

        {/* Middle column — 4 stacked TradingView charts, no scroll */}
        <div className="flex-1 flex flex-col h-full p-2 gap-1 overflow-hidden border-r border-[#2a3447]">
          {[
            { interval: "5", label: "5 Min" },
            { interval: "15", label: "15 Min" },
            { interval: "D", label: "Daily" },
            { interval: "M", label: "Monthly" },
          ].map((chart) => (
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
