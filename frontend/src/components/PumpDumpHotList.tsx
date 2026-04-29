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
  high: "var(--color-risk-pd-high)",
  medium: "var(--color-warning)",
  low: "var(--color-risk-pd-low)",
};

export default function PumpDumpHotList({ items, isLoading, error }: PumpDumpHotListProps) {
  if (error) {
    return (
      <div className="w-[260px] shrink-0 overflow-y-auto">
        <div className="text-text-muted text-label uppercase tracking-widest mb-1">P&D Risk</div>
        <p className="text-text-muted text-meta italic">P&D data unavailable</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="w-[260px] shrink-0 overflow-y-auto">
        <div className="text-text-muted text-label uppercase tracking-widest mb-1">P&D Risk</div>
        {[1, 2, 3].map(i => (
          <div key={i} className="bg-border-card animate-pulse h-4 rounded mb-2" />
        ))}
      </div>
    );
  }

  const display = items.slice(0, 10);

  if (display.length === 0) {
    return (
      <div className="w-[260px] shrink-0 overflow-y-auto">
        <div className="text-text-muted text-label uppercase tracking-widest mb-1">P&D Risk</div>
        <p className="text-text-muted text-meta italic">No P&D alerts</p>
      </div>
    );
  }

  return (
    <div className="w-[260px] shrink-0 overflow-y-auto">
      <div className="text-text-muted text-label uppercase tracking-widest mb-1">P&D Risk</div>
      {display.map((item, idx) => {
        const risk = getHighestRisk(item);
        const gain = item.gain1Day;
        return (
          <div key={item.ticker + idx} className="flex items-center gap-2 py-1 border-b border-border-card">
            <span className="text-accent-cyan text-meta font-bold font-mono">{item.ticker}</span>
            {risk && (
              <span
                className="text-label px-1.5 py-0.5 rounded-[3px] text-white font-bold"
                style={{ backgroundColor: riskColors[risk] }}
              >
                {risk.toUpperCase()}
              </span>
            )}
            <span className={`text-meta ml-auto ${gain === null ? "text-text-muted" : gain >= 0 ? "text-positive" : "text-negative"}`}>
              {gain !== null ? `${gain >= 0 ? "+" : ""}${gain.toFixed(1)}%` : "—"}
            </span>
          </div>
        );
      })}
    </div>
  );
}
