"use client";

import type { HistoricalFloatPoint } from "@/types/dilution";

interface FloatHistoryChartProps {
  data: HistoricalFloatPoint[];
  isLoading: boolean;
  height?: number;
}

export default function FloatHistoryChart({ data, isLoading, height = 120 }: FloatHistoryChartProps) {
  if (isLoading) {
    return (
      <div>
        <div className="text-[#9aa7c7] text-[10px] uppercase tracking-widest mb-1">Float Over Time</div>
        <div className="bg-[#2a3447] animate-pulse rounded" style={{ height }} />
      </div>
    );
  }

  // Sort by reportedDate, prefer tradableFloat over float, filter nulls
  const sorted = [...data].sort((a, b) => a.reportedDate.localeCompare(b.reportedDate));
  const points = sorted
    .map(d => ({
      date: d.reportedDate,
      value: d.tradableFloat ?? d.float,
    }))
    .filter((p): p is { date: string; value: number } => p.value !== null);

  if (points.length < 2) {
    return (
      <div>
        <div className="text-[#9aa7c7] text-[10px] uppercase tracking-widest mb-1">Float Over Time</div>
        <p className="text-[#9aa7c7] text-xs italic">Not enough data</p>
      </div>
    );
  }

  const padding = 24;
  const width = 300;
  const minVal = Math.min(...points.map(p => p.value));
  const maxVal = Math.max(...points.map(p => p.value));
  const range = maxVal - minVal || 1;

  const polyPoints = points.map((p, i) => {
    const x = padding + ((width - 2 * padding) * i) / (points.length - 1);
    const y = padding + ((height - 2 * padding) * (1 - (p.value - minVal) / range));
    return `${x},${y}`;
  }).join(" ");

  const lastPoint = points[points.length - 1];
  const lastX = padding + ((width - 2 * padding) * (points.length - 1)) / (points.length - 1);
  const lastY = padding + ((height - 2 * padding) * (1 - (lastPoint.value - minVal) / range));

  function formatFloat(val: number): string {
    if (val >= 1_000_000_000) return `${(val / 1_000_000_000).toFixed(1)}B`;
    if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `${(val / 1_000).toFixed(0)}K`;
    return String(Math.round(val));
  }

  function formatDate(dateStr: string): string {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
    } catch {
      return dateStr.slice(0, 7);
    }
  }

  return (
    <div>
      <div className="text-[#9aa7c7] text-[10px] uppercase tracking-widest mb-1">Float Over Time</div>
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%" }}>
        {/* Polyline */}
        <polyline
          points={polyPoints}
          fill="none"
          stroke="#a78bfa"
          strokeWidth={1.5}
        />
        {/* Last point dot */}
        <circle cx={lastX} cy={lastY} r={3} fill="#a78bfa" />

        {/* Date labels */}
        <text x={padding} y={height - 4} fill="#9aa7c7" fontSize="8" textAnchor="start">
          {formatDate(points[0].date)}
        </text>
        <text x={width - padding} y={height - 4} fill="#9aa7c7" fontSize="8" textAnchor="end">
          {formatDate(lastPoint.date)}
        </text>

        {/* Min/max float labels */}
        <text x={4} y={padding + 3} fill="#9aa7c7" fontSize="8" textAnchor="start">
          {formatFloat(maxVal)}
        </text>
        <text x={4} y={height - padding + 3} fill="#9aa7c7" fontSize="8" textAnchor="start">
          {formatFloat(minVal)}
        </text>
      </svg>
    </div>
  );
}
