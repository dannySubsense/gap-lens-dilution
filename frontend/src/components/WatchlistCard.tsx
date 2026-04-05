"use client";

import type { GainerEntry, RiskLevel } from "@/types/dilution";
import { formatMillions } from "./GainerRow";

// ── Helpers (mirrors GainerRow) ───────────────────────────────────────────

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

interface WatchlistCardProps {
  ticker: string;
  gainerData: GainerEntry | null;
  isSelected: boolean;
  isFlashing: boolean;
  isActive: boolean;
  onActivate: (ticker: string) => void;
  onDelete: (ticker: string) => void;
  onMultiSelect: (ticker: string, event: React.MouseEvent) => void;
}

// ── Component ─────────────────────────────────────────────────────────────

export default function WatchlistCard({
  ticker,
  gainerData,
  isSelected,
  isFlashing,
  isActive,
  onDelete,
  onMultiSelect,
}: WatchlistCardProps) {
  // Same wrapperBase as GainerRow — inherits padding fix from Slice 3
  const wrapperBase =
    "cursor-pointer w-full mx-2 my-1 px-2.5 py-1.5 border rounded-[5px] transition-colors group";

  // State precedence: Active > Selected > Normal/Hover
  let wrapperState: string;
  if (isActive) {
    wrapperState = "bg-[#222b3a] border-[#ff4fa6]";
  } else if (isSelected) {
    wrapperState = "bg-[#222b3a] border-[#a78bfa]";
  } else {
    wrapperState = "bg-[#1b2230] border-[#2a3447] hover:bg-[#222b3a]";
  }

  // Flash class overrides border animation (applied in addition to state classes)
  const flashClass = isFlashing ? "flash-card" : "";

  // Build bottom line parts if gainerData is available
  let bottomParts: string[] | null = null;
  if (gainerData) {
    const parts: string[] = [];
    if (gainerData.float !== null) parts.push(formatMillions(gainerData.float));
    if (gainerData.marketCap !== null) parts.push(formatMillions(gainerData.marketCap));
    const sectorAbbr = abbreviateSector(gainerData.sector);
    if (sectorAbbr !== null) parts.push(sectorAbbr);
    if (gainerData.country !== null) parts.push(gainerData.country);
    if (parts.length > 0) bottomParts = parts;
  }

  const changeLabel = gainerData
    ? `${gainerData.todaysChangePerc >= 0 ? "+" : ""}${gainerData.todaysChangePerc.toFixed(2)}%`
    : "—";
  const changeColor = gainerData
    ? gainerData.todaysChangePerc >= 0
      ? "text-[#5ce08a]"
      : "text-[#ff6b6b]"
    : "text-[#9aa7c7]";

  return (
    <button
      type="button"
      className={`${wrapperBase} ${wrapperState} ${flashClass} text-left`}
      onClick={(e) => onMultiSelect(ticker, e)}
    >
      {/* Top line: ticker, risk badge, news badge, change%, trash icon */}
      <div className="flex items-center gap-1.5 w-full">
        <span
          className="font-bold text-xs leading-tight"
          style={{ color: "#63D3FF", fontFamily: "'JetBrains Mono', monospace" }}
        >
          {ticker}
        </span>

        {gainerData?.risk !== null && gainerData?.risk !== undefined && (
          <span
            className="text-white text-[10px] font-bold px-1.5 py-0.5 rounded-[3px] leading-none"
            style={{ backgroundColor: RISK_BADGE_BG[gainerData.risk] }}
          >
            {gainerData.risk}
          </span>
        )}

        {gainerData?.newsToday && (
          <span className="text-white text-[10px] font-bold px-1.5 py-0.5 rounded-[3px] leading-none bg-[#1F8FB3]">
            NEWS
          </span>
        )}

        <span className={`ml-auto text-xs font-semibold ${changeColor}`}>
          {changeLabel}
        </span>

        {/* Trash icon — always rendered, group-hover makes it fully visible */}
        <span
          className="text-[#9aa7c7] opacity-40 group-hover:opacity-100 group-hover:text-[#ff4fa6] text-xs ml-1 leading-none"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(ticker);
          }}
          aria-label={`Remove ${ticker}`}
          role="button"
        >
          &#128465;
        </span>
      </div>

      {/* Middle line: price, volume */}
      <div className="flex items-center justify-between mt-0.5">
        <span className="text-[#eef1f8] text-xs">
          {gainerData ? `$${formatPrice(gainerData.price)}` : "—"}
        </span>
        <span className="text-[#9aa7c7] text-xs">
          {gainerData ? `Vol ${formatMillions(gainerData.volume)}` : "—"}
        </span>
      </div>

      {/* Bottom line: float | mcap | sector | country (omitted if no gainerData) */}
      {bottomParts !== null && (
        <div className="mt-0.5 text-[#9aa7c7] text-[10px] leading-tight truncate">
          {bottomParts.join(" | ")}
        </div>
      )}
    </button>
  );
}
