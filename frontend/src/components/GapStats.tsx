import { GapStatEntry } from "@/types/dilution";

interface GapStatsProps {
  rawEntries: GapStatEntry[];
}

function GapStatsSkeleton() {
  return (
    <div className="bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5 animate-pulse">
      <div className="h-6 w-36 bg-[#2a3447] rounded mb-4" />
      {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
        <div key={i} className="h-4 w-full bg-[#2a3447] rounded mb-2" />
      ))}
    </div>
  );
}

// EST offset: UTC-5 (no DST adjustment — spec says UTC-5)
function parseHighTimeHourEST(highTime: string | null): number | null {
  if (!highTime) return null;
  try {
    const d = new Date(highTime);
    if (isNaN(d.getTime())) return null;
    // UTC hour - 5 to get EST
    const utcHour = d.getUTCHours();
    const utcMinutes = d.getUTCMinutes();
    // Convert to fractional hour in EST
    const estFractional = utcHour - 5 + utcMinutes / 60;
    return estFractional;
  } catch {
    return null;
  }
}

function computeStats(entries: GapStatEntry[]) {
  const n = entries.length;

  // Last Gap Date: first entry's date (entries assumed ordered descending)
  const lastGapDate = entries[0]?.date ?? null;

  // Avg Gap %
  const gapPcts = entries
    .map((e) => e.gap_percentage)
    .filter((v): v is number => v !== null);
  const avgGapPct = gapPcts.length > 0
    ? gapPcts.reduce((a, b) => a + b, 0) / gapPcts.length
    : 0;

  // Avg Open→High
  const openToHighVals = entries
    .filter((e) => e.high_price !== null && e.market_open !== null && e.market_open > 0)
    .map((e) => ((e.high_price! - e.market_open!) / e.market_open!) * 100);
  const avgOpenToHigh = openToHighVals.length > 0
    ? openToHighVals.reduce((a, b) => a + b, 0) / openToHighVals.length
    : 0;

  // Avg Open→Low
  const openToLowVals = entries
    .filter((e) => e.low_price !== null && e.market_open !== null && e.market_open > 0)
    .map((e) => ((e.low_price! - e.market_open!) / e.market_open!) * 100);
  const avgOpenToLow = openToLowVals.length > 0
    ? openToLowVals.reduce((a, b) => a + b, 0) / openToLowVals.length
    : 0;

  // % New High After 11am (EST)
  const parseable = entries.filter((e) => {
    const h = parseHighTimeHourEST(e.high_time);
    return h !== null;
  });
  const after11 = parseable.filter((e) => {
    const h = parseHighTimeHourEST(e.high_time)!;
    return h >= 11;
  });
  const pctNewHighAfter11am = parseable.length > 0
    ? (after11.length / parseable.length) * 100
    : 0;

  // % Closed Below VWAP
  const closedBelowVwap = entries.filter((e) => e.closed_over_vwap === false).length;
  const pctClosedBelowVwap = n > 0 ? (closedBelowVwap / n) * 100 : 0;

  // % Closed Below Open
  const closedBelowOpen = entries.filter(
    (e) => e.market_close !== null && e.market_open !== null && e.market_close < e.market_open!
  ).length;
  const pctClosedBelowOpen = n > 0 ? (closedBelowOpen / n) * 100 : 0;

  return {
    lastGapDate,
    numGaps: n,
    avgGapPct,
    avgOpenToHigh,
    avgOpenToLow,
    pctNewHighAfter11am,
    pctClosedBelowVwap,
    pctClosedBelowOpen,
  };
}

function colorFor11am(pct: number): string {
  if (pct >= 45) return "#5ce08a";
  if (pct >= 21) return "#f7b731";
  return "#ff6b6b";
}

function colorForBelowVwap(pct: number): string {
  if (pct <= 59) return "#5ce08a";
  if (pct <= 84) return "#f7b731";
  return "#ff6b6b";
}

function colorForBelowOpen(pct: number): string {
  if (pct <= 50) return "#5ce08a";
  if (pct <= 74) return "#f7b731";
  return "#ff6b6b";
}

export default function GapStats({ rawEntries }: GapStatsProps) {
  if (rawEntries.length === 0) return null;

  const stats = computeStats(rawEntries);

  const rows: Array<{ label: string; value: string; color: string }> = [
    {
      label: "Last Gap Date",
      value: stats.lastGapDate ?? "—",
      color: "#eef1f8",
    },
    {
      label: "Number of Gaps",
      value: String(stats.numGaps),
      color: "#eef1f8",
    },
    {
      label: "Avg Gap %",
      value: `+${stats.avgGapPct.toFixed(1)}%`,
      color: "#eef1f8",
    },
    {
      label: "Avg Open\u2192High",
      value: `+${stats.avgOpenToHigh.toFixed(1)}%`,
      color: "#5ce08a",
    },
    {
      label: "Avg Open\u2192Low",
      value: `${stats.avgOpenToLow.toFixed(1)}%`,
      color: "#ff6b6b",
    },
    {
      label: "% New High After 11am",
      value: `${stats.pctNewHighAfter11am.toFixed(0)}%`,
      color: colorFor11am(stats.pctNewHighAfter11am),
    },
    {
      label: "% Closed Below VWAP",
      value: `${stats.pctClosedBelowVwap.toFixed(0)}%`,
      color: colorForBelowVwap(stats.pctClosedBelowVwap),
    },
    {
      label: "% Closed Below Open",
      value: `${stats.pctClosedBelowOpen.toFixed(0)}%`,
      color: colorForBelowOpen(stats.pctClosedBelowOpen),
    },
  ];

  return (
    <div className="bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5">
      <h2 className="text-lg font-bold text-[#a78bfa] mb-3">Gap Stats</h2>
      <div>
        {rows.map((row) => (
          <div key={row.label} className="flex items-center justify-between py-1">
            <span className="text-sm text-[#9aa7c7] w-44 shrink-0">{row.label}</span>
            <span
              className="text-sm font-bold font-[JetBrains_Mono,ui-monospace,monospace]"
              style={{ color: row.color }}
            >
              {row.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export { GapStatsSkeleton };
