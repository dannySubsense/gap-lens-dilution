import type { GainerEntry, RiskLevel, GainerEnrichment } from "@/types/dilution";
import PumpDumpBadge from "./PumpDumpBadge";
import ComplianceWarning from "./ComplianceWarning";
import ReverseSplitFlag from "./ReverseSplitFlag";

// ── Helpers ───────────────────────────────────────────────────────────────

export function formatMillions(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${Math.round(n / 1_000)}K`;
  return String(n);
}

function formatPrice(price: number): string {
  if (price >= 1) return price.toFixed(2);
  return price.toFixed(4);
}

const SECTOR_ABBR: Record<string, string> = {
  Healthcare: "Health",
  Technology: "Tech",
  Industrials: "Indust",
  "Consumer Cyclical": "Cons Cyc",
  "Consumer Defensive": "Cons Def",
  "Communication Services": "Comms",
  "Financial Services": "Financ",
  "Basic Materials": "Materials",
  "Real Estate": "RE",
};

function abbreviateSector(sector: string | null): string | null {
  if (!sector) return null;
  return SECTOR_ABBR[sector] ?? sector;
}

const RISK_BADGE_BG: Record<RiskLevel, string> = {
  High: "#A93232",
  Medium: "#B96A16",
  Low: "#2F7D57",
  "N/A": "#4A525C",
};

// ── Props ─────────────────────────────────────────────────────────────────

interface GainerRowProps {
  gainer: GainerEntry;
  isSelected: boolean;
  onClick: (ticker: string) => void;
  enrichmentData?: GainerEnrichment | null;
}

// ── Component ─────────────────────────────────────────────────────────────

export default function GainerRow({ gainer, isSelected, onClick, enrichmentData }: GainerRowProps) {
  const {
    ticker,
    todaysChangePerc,
    price,
    volume,
    float,
    marketCap,
    sector,
    country,
    risk,
    newsToday,
  } = gainer;

  const changePositive = todaysChangePerc >= 0;
  const changeColor = changePositive ? "text-[#5ce08a]" : "text-[#ff6b6b]";
  const changeLabel = `${changePositive ? "+" : ""}${todaysChangePerc.toFixed(2)}%`;

  const sectorAbbr = abbreviateSector(sector);

  const bottomParts: string[] = [];
  if (float !== null) bottomParts.push(formatMillions(float));
  if (marketCap !== null) bottomParts.push(formatMillions(marketCap));
  if (sectorAbbr !== null) bottomParts.push(sectorAbbr);
  if (country !== null) bottomParts.push(country);
  const hasBottomLine = bottomParts.length > 0;

  const wrapperBase =
    "cursor-pointer w-full mx-2 my-1 px-2.5 py-1.5 border rounded-[5px] transition-colors";
  const wrapperState = isSelected
    ? "bg-[#222b3a] border-[#ff4fa6]"
    : "bg-[#1b2230] border-[#2a3447] hover:bg-[#222b3a]";

  return (
    <button
      type="button"
      className={`${wrapperBase} ${wrapperState} text-left`}
      onClick={() => onClick(ticker)}
    >
      {/* Top line: ticker, risk badge, news badge, change% */}
      <div className="flex items-center gap-1.5 w-full">
        <span
          className="font-bold text-sm leading-tight"
          style={{ color: "#63D3FF", fontFamily: "'JetBrains Mono', monospace" }}
        >
          {ticker}
        </span>

        {risk !== null && (
          <span
            className="text-white text-[10px] font-bold px-1.5 py-0.5 rounded-[3px] leading-none"
            style={{ backgroundColor: RISK_BADGE_BG[risk] }}
          >
            {risk}
          </span>
        )}

        {newsToday && (
          <span
            className="text-white text-[10px] font-bold px-1.5 py-0.5 rounded-[3px] leading-none bg-[#1F8FB3]"
          >
            NEWS
          </span>
        )}

        <span className={`ml-auto text-xs font-semibold ${changeColor}`}>
          {changeLabel}
        </span>
      </div>

      {/* Middle line: price, volume */}
      <div className="flex items-center justify-between mt-0.5">
        <span className="text-[#eef1f8] text-xs">${formatPrice(price)}</span>
        <span className="text-[#9aa7c7] text-xs">
          Vol {formatMillions(volume)}
        </span>
      </div>

      {/* Bottom line: float | mcap | sector | country */}
      {hasBottomLine && (
        <div className="mt-0.5 text-[#9aa7c7] text-[10px] leading-tight truncate">
          {bottomParts.join(" | ")}
        </div>
      )}

      {/* Enrichment badges (compact) */}
      {enrichmentData && (
        <div className="flex flex-wrap gap-1 mt-1">
          <PumpDumpBadge data={enrichmentData.pumpdump} compact />
          <ComplianceWarning hasDeficiency={enrichmentData.hasComplianceDeficiency} compact />
          <ReverseSplitFlag hasSplits={enrichmentData.hasReverseSplits} compact />
        </div>
      )}
    </button>
  );
}
