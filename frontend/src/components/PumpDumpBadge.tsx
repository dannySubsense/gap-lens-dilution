"use client";

import type { PumpDumpData, RiskLevelLower } from "@/types/dilution";

interface PumpDumpBadgeProps {
  data: PumpDumpData | null;
  compact?: boolean;
}

const riskColors: Record<RiskLevelLower, string> = {
  high: "text-[#ef4444]",
  medium: "text-[#eab308]",
  low: "text-[#22c55e]",
};

function getHighestRisk(data: PumpDumpData): RiskLevelLower | null {
  // Priority: scamRisk > floatRisk > underwriterRisk > countryRisk
  for (const level of ["high", "medium", "low"] as RiskLevelLower[]) {
    if (data.scamRisk === level) return level;
    if (data.floatRisk === level) return level;
    if (data.underwriterRisk === level) return level;
    if (data.countryRisk === level) return level;
  }
  return null;
}

export default function PumpDumpBadge({ data, compact = false }: PumpDumpBadgeProps) {
  if (!data) return null;
  const risk = getHighestRisk(data);
  if (!risk) return null;

  return (
    <span className={`text-[10px] font-medium ${riskColors[risk]}`}>
      {compact ? `☠ P&D: ${risk.toUpperCase()}` : `☠ P&D Risk: ${risk.toUpperCase()}`}
    </span>
  );
}
