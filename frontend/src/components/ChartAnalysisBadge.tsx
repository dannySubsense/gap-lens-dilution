import { ChartAnalysis, ChartRating } from "@/types/dilution";

interface ChartAnalysisBadgeProps {
  analysis: ChartAnalysis | null;
}

const HISTORY_MAP: Record<ChartRating, { label: string; bg: string }> = {
  green:  { label: "HISTORY: Strong",      bg: "var(--color-positive)" },
  yellow: { label: "HISTORY: Semi-Strong", bg: "var(--color-warning)" },
  orange: { label: "HISTORY: Mixed",       bg: "var(--color-warning-orange)" },
  red:    { label: "HISTORY: Fader",       bg: "var(--color-negative)" },
};

export default function ChartAnalysisBadge({ analysis }: ChartAnalysisBadgeProps) {
  if (!analysis) return null;

  const entry = HISTORY_MAP[analysis.rating];
  if (!entry) return null;

  return (
    <span
      className="text-meta font-bold px-2.5 py-1 rounded-[5px] text-white"
      style={{ backgroundColor: entry.bg }}
    >
      {entry.label}
    </span>
  );
}
