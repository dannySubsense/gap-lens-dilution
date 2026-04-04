import { HeaderData } from "@/types/dilution";
import ChartAnalysisBadge from "@/components/ChartAnalysisBadge";

interface HeaderProps {
  data: HeaderData | null;
}

function RiskBadgeInline({ level }: { level: string }) {
  const colorMap: Record<string, string> = {
    Low: "bg-risk-low",
    Medium: "bg-risk-medium",
    High: "bg-risk-high",
  };
  return (
    <span
      className={`${colorMap[level] ?? "bg-badge-default"} text-white text-sm font-bold px-3 py-1 rounded-[var(--radius-sm)]`}
    >
      RISK: {level}
    </span>
  );
}

function HeaderSkeleton() {
  return (
    <div className="bg-bg-card border border-border-card rounded-[var(--radius)] p-5 animate-pulse">
      <div className="flex items-start justify-between mb-3">
        <div className="h-9 w-32 bg-border-card rounded" />
        <div className="h-7 w-24 bg-border-card rounded" />
      </div>
      <div className="h-6 w-20 bg-border-card rounded animate-pulse mt-1 mb-2" />
      <div className="h-4 w-96 bg-border-card rounded" />
    </div>
  );
}

function formatStockPrice(price: number): string {
  if (price >= 1) return `$${price.toFixed(2)}`;
  return `$${price.toFixed(4)}`;
}

export default function Header({ data }: HeaderProps) {
  if (!data) return <HeaderSkeleton />;

  return (
    <div className="bg-bg-card border border-border-card rounded-[var(--radius)] p-5">
      {/* Row 1: ticker + chart analysis badge + risk badge */}
      <div className="flex items-center gap-3 mb-2 flex-wrap">
        <h1 className="text-3xl font-bold text-[#a78bfa]">{data.ticker}</h1>
        <ChartAnalysisBadge analysis={data.chartAnalysis} />
        <div className="ml-auto">
          <RiskBadgeInline level={data.overallRisk} />
        </div>
      </div>

      {/* Row 2: stock price (only when > 0) */}
      {data.stockPrice !== null && data.stockPrice > 0 && (
        <p className="text-sm font-bold text-[#eef1f8] mb-2">
          {formatStockPrice(data.stockPrice)}
        </p>
      )}

      {/* Row 3: metadata */}
      <p className="text-text-secondary text-sm">
        Float/OS: {data.float}/{data.outstandingShares}
        <span className="mx-2 text-text-muted">|</span>
        MC: {data.marketCap}
        <span className="mx-2 text-text-muted">|</span>
        {data.sector}
        <span className="mx-2 text-text-muted">|</span>
        {data.country}
      </p>
    </div>
  );
}
