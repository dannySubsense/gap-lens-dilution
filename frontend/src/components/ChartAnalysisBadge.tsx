import { ChartAnalysis, ChartRating } from "@/types/dilution";

interface ChartAnalysisBadgeProps {
  analysis: ChartAnalysis | null;
}

const HISTORY_MAP: Record<ChartRating, { label: string; bg: string }> = {
  green:  { label: "HISTORY: Strong",      bg: "#2F7D57" },
  yellow: { label: "HISTORY: Semi-Strong", bg: "#B9A816" },
  orange: { label: "HISTORY: Mixed",       bg: "#B96A16" },
  red:    { label: "HISTORY: Fader",       bg: "#A93232" },
};

export default function ChartAnalysisBadge({ analysis }: ChartAnalysisBadgeProps) {
  if (!analysis) return null;

  const entry = HISTORY_MAP[analysis.rating];
  if (!entry) return null;

  return (
    <span
      className="text-xs font-bold px-2.5 py-1 rounded-[5px] text-white"
      style={{ backgroundColor: entry.bg }}
    >
      {entry.label}
    </span>
  );
}
