"use client";

import type { KeyStatsData, RiskLevel } from "@/types/dilution";
import { formatNum } from "@/utils/dilutionMappers";

interface KeyStatsGridProps {
  data: KeyStatsData;
  isLoading: boolean;
}

const riskBadgeColors: Record<string, string> = {
  High: "#A93232",
  Medium: "#B96A16",
  Low: "#2F7D57",
  "N/A": "#4A525C",
};

function RiskBadge({ level }: { level: RiskLevel | null }) {
  const display = level ?? "N/A";
  const bg = riskBadgeColors[display] ?? riskBadgeColors["N/A"];
  return (
    <span
      className="text-[10px] font-bold px-1.5 py-0.5 rounded-[3px] text-white inline-block"
      style={{ backgroundColor: bg }}
    >
      {display}
    </span>
  );
}

function formatValue(val: number | null | undefined): string {
  if (val === null || val === undefined) return "—";
  return formatNum(val);
}

function formatPercent(val: number | null | undefined): string {
  if (val === null || val === undefined) return "—";
  return `${(val * 100).toFixed(1)}%`;
}

function formatDecimal(val: number | null | undefined, decimals = 1): string {
  if (val === null || val === undefined) return "—";
  return val.toFixed(decimals);
}

// Cell definition for the grid
interface CellDef {
  label: string;
  type: "text" | "number" | "percent" | "decimal" | "risk";
  value?: string | number | null | undefined;
  riskLevel?: RiskLevel | null;
}

function SkeletonCell() {
  return (
    <div>
      <div className="bg-[#2a3447] animate-pulse rounded h-3 w-16 mb-1" />
      <div className="bg-[#2a3447] animate-pulse rounded h-4 w-12" />
    </div>
  );
}

export default function KeyStatsGrid({ data, isLoading }: KeyStatsGridProps) {
  if (isLoading) {
    return (
      <div className="bg-[#1b2230] border border-[#2a3447] rounded-[5px] p-3">
        <div className="grid grid-cols-3 gap-x-3 gap-y-2">
          {Array.from({ length: 18 }).map((_, i) => (
            <SkeletonCell key={i} />
          ))}
        </div>
      </div>
    );
  }

  const col1: CellDef[] = [
    { label: "Sector", type: "text", value: data.sector },
    { label: "Industry", type: "text", value: data.industry },
    { label: "Country", type: "text", value: data.country },
    { label: "Exchange", type: "text", value: data.exchange },
    { label: "Vol Avg", type: "number", value: data.volAvg },
    { label: "Inst. Own", type: "percent", value: data.institutionalOwnership },
  ];

  const col2: CellDef[] = [
    { label: "Float", type: "number", value: data.float },
    { label: "Outstanding", type: "number", value: data.outstanding },
    { label: "Cash/Share", type: "decimal", value: data.cashPerShare },
    { label: "Market Cap", type: "number", value: data.marketCap },
    { label: "Short Interest", type: "percent", value: data.shortInterest },
    { label: "Borrow Rate", type: "decimal", value: data.borrowRate },
    { label: "Days to Cover", type: "decimal", value: data.daysToCover },
    { label: "Enterprise Val", type: "number", value: data.enterpriseValue },
  ];

  const col3: CellDef[] = [
    { label: "Offering Ability", type: "risk", riskLevel: data.offeringAbility },
    { label: "Offering Freq", type: "risk", riskLevel: data.offeringFrequency },
    { label: "Dilution Risk", type: "risk", riskLevel: data.dilutionRisk },
    { label: "Cash Need", type: "risk", riskLevel: data.cashNeed },
    { label: "Overall Risk", type: "risk", riskLevel: data.overallOfferingRisk },
    { label: "Warrant Risk", type: "risk", riskLevel: data.warrantExerciseRisk },
  ];

  function renderCell(cell: CellDef, idx: number) {
    let display: React.ReactNode;

    if (cell.type === "risk") {
      display = <RiskBadge level={cell.riskLevel ?? null} />;
    } else if (cell.type === "number") {
      const val = typeof cell.value === "number" ? cell.value : null;
      const formatted = formatValue(val);
      display = <span className={`text-sm font-semibold ${formatted === "—" ? "text-[#9aa7c7]" : "text-[#eef1f8]"}`}>{formatted}</span>;
    } else if (cell.type === "percent") {
      const val = typeof cell.value === "number" ? cell.value : null;
      const formatted = formatPercent(val);
      display = <span className={`text-sm font-semibold ${formatted === "—" ? "text-[#9aa7c7]" : "text-[#eef1f8]"}`}>{formatted}</span>;
    } else if (cell.type === "decimal") {
      const val = typeof cell.value === "number" ? cell.value : null;
      const formatted = formatDecimal(val);
      display = <span className={`text-sm font-semibold ${formatted === "—" ? "text-[#9aa7c7]" : "text-[#eef1f8]"}`}>{formatted}</span>;
    } else {
      const formatted = cell.value ?? "—";
      display = <span className={`text-sm font-semibold ${formatted === "—" ? "text-[#9aa7c7]" : "text-[#eef1f8]"}`}>{String(formatted)}</span>;
    }

    return (
      <div key={idx}>
        <div className="text-[#9aa7c7] text-[10px] uppercase tracking-widest">{cell.label}</div>
        {display}
      </div>
    );
  }

  // Interleave columns to fill the 3-column grid row by row
  const maxRows = Math.max(col1.length, col2.length, col3.length);
  const cells: React.ReactNode[] = [];
  for (let row = 0; row < maxRows; row++) {
    cells.push(col1[row] ? renderCell(col1[row], row * 3) : <div key={row * 3} />);
    cells.push(col2[row] ? renderCell(col2[row], row * 3 + 1) : <div key={row * 3 + 1} />);
    cells.push(col3[row] ? renderCell(col3[row], row * 3 + 2) : <div key={row * 3 + 2} />);
  }

  return (
    <div className="bg-[#1b2230] border border-[#2a3447] rounded-[5px] p-3">
      <div className="grid grid-cols-3 gap-x-3 gap-y-2">
        {cells}
      </div>
    </div>
  );
}
