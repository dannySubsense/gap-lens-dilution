import { RiskAssessment, RiskLevel } from "@/types/dilution";

interface RiskBadgesProps {
  data: RiskAssessment | null;
}

const RISK_COLORS: Record<RiskLevel, string> = {
  Low: "bg-risk-low",
  Medium: "bg-risk-medium",
  High: "bg-risk-high",
  "N/A": "bg-badge-default",
};

function BadgeItem({ label, level }: { label: string; level: RiskLevel }) {
  return (
    <div className="flex flex-col items-center gap-1.5">
      <span className="text-text-muted text-xs">{label}</span>
      <span
        className={`${RISK_COLORS[level]} text-white text-xs font-bold px-3 py-1 rounded-[var(--radius-sm)] min-w-[4rem] text-center`}
      >
        {level}
      </span>
    </div>
  );
}

function RiskBadgesSkeleton() {
  return (
    <div className="bg-bg-card border border-border-card rounded-[var(--radius)] p-5 animate-pulse">
      <div className="flex gap-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="flex flex-col items-center gap-1.5">
            <div className="h-3 w-16 bg-border-card rounded" />
            <div className="h-6 w-16 bg-border-card rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function RiskBadges({ data }: RiskBadgesProps) {
  if (!data) return <RiskBadgesSkeleton />;

  return (
    <div className="bg-bg-card border border-border-card rounded-[var(--radius)] p-5">
      <div className="flex gap-6 flex-wrap">
        <BadgeItem label="Overall Risk" level={data.overallRisk} />
        <BadgeItem label="Offering" level={data.offering} />
        <BadgeItem label="Dilution" level={data.dilution} />
        <BadgeItem label="Frequency" level={data.frequency} />
        <BadgeItem label="Cash Need" level={data.cashNeed} />
        <BadgeItem label="Warrants" level={data.warrants} />
      </div>
    </div>
  );
}
