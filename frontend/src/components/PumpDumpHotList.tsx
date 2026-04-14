"use client";

import type { PumpDumpData, RiskLevelLower } from "@/types/dilution";

interface PumpDumpHotListProps {
  items: PumpDumpData[];
  isLoading: boolean;
  error: string | null;
}

function getHighestRisk(data: PumpDumpData): RiskLevelLower | null {
  // Priority: scamRisk > floatRisk > underwriterRisk > countryRisk
  if (data.scamRisk === "high" || data.floatRisk === "high" || data.underwriterRisk === "high" || data.countryRisk === "high") return "high";
  if (data.scamRisk === "medium" || data.floatRisk === "medium" || data.underwriterRisk === "medium" || data.countryRisk === "medium") return "medium";
  if (data.scamRisk === "low" || data.floatRisk === "low" || data.underwriterRisk === "low" || data.countryRisk === "low") return "low";
  return null;
}

const riskColors: Record<RiskLevelLower, string> = {
  high: "#ef4444",
  medium: "#eab308",
  low: "#22c55e",
};

export default function PumpDumpHotList({ items, isLoading, error }: PumpDumpHotListProps) {
  if (error) {
    return (
      <div className="w-[260px] shrink-0 overflow-y-auto">
        <div className="text-[#9aa7c7] text-[10px] uppercase tracking-widest mb-1">P&D Risk</div>
        <p className="text-[#9aa7c7] text-xs italic">P&D data unavailable</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="w-[260px] shrink-0 overflow-y-auto">
        <div className="text-[#9aa7c7] text-[10px] uppercase tracking-widest mb-1">P&D Risk</div>
        {[1, 2, 3].map(i => (
          <div key={i} className="bg-[#2a3447] animate-pulse h-4 rounded mb-2" />
        ))}
      </div>
    );
  }

  const display = items.slice(0, 10);

  if (display.length === 0) {
    return (
      <div className="w-[260px] shrink-0 overflow-y-auto">
        <div className="text-[#9aa7c7] text-[10px] uppercase tracking-widest mb-1">P&D Risk</div>
        <p className="text-[#9aa7c7] text-xs italic">No P&D alerts</p>
      </div>
    );
  }

  return (
    <div className="w-[260px] shrink-0 overflow-y-auto">
      <div className="text-[#9aa7c7] text-[10px] uppercase tracking-widest mb-1">P&D Risk</div>
      {display.map((item, idx) => {
        const risk = getHighestRisk(item);
        const gain = item.gain1Day;
        return (
          <div key={item.ticker + idx} className="flex items-center gap-2 py-1 border-b border-[#2a3447]">
            <span className="text-[#63D3FF] text-xs font-bold font-mono">{item.ticker}</span>
            {risk && (
              <span
                className="text-[10px] px-1.5 py-0.5 rounded-[3px] text-white font-bold"
                style={{ backgroundColor: riskColors[risk] }}
              >
                {risk.toUpperCase()}
              </span>
            )}
            <span className={`text-xs ml-auto ${gain === null ? "text-[#9aa7c7]" : gain >= 0 ? "text-[#5ce08a]" : "text-[#ff6b6b]"}`}>
              {gain !== null ? `${gain >= 0 ? "+" : ""}${gain.toFixed(1)}%` : "—"}
            </span>
          </div>
        );
      })}
    </div>
  );
}
