import { Headline, FilingType } from "@/types/dilution";

interface HeadlinesProps {
  data: Headline[] | null;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

const BADGE_COLORS: Record<FilingType, string> = {
  "6-K": "bg-badge-6k",
  "8-K": "bg-badge-8k",
  "S-1": "bg-badge-s1",
  "10-K": "bg-badge-10k",
  "10-Q": "bg-badge-10k",
  "SC 13D": "bg-badge-sc13",
  "SC 13G": "bg-badge-sc13",
  GROK: "bg-badge-grok",
  news: "bg-badge-default",
  jmt415: "bg-badge-default",
};

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  const date = d.toISOString().slice(0, 10);
  const time = d.toTimeString().slice(0, 5);
  return `${date} ${time}`;
}

function HeadlinesSkeleton() {
  return (
    <div className="bg-bg-card border border-border-card rounded-[var(--radius)] p-5 space-y-3 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-start gap-3">
          <div className="h-6 w-12 bg-border-card rounded shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="h-4 w-36 bg-border-card rounded" />
            <div className="h-4 w-full bg-border-card rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function Headlines({ data, isCollapsed, onToggleCollapse }: HeadlinesProps) {
  if (!data) return <HeadlinesSkeleton />;

  const displayData = isCollapsed ? data.slice(0, 1) : data;

  return (
    <div className="bg-bg-card border border-border-card rounded-[var(--radius)] p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold text-[#9aa7c7] uppercase tracking-wide">News</span>
        <button
          onClick={onToggleCollapse}
          className="text-[#9aa7c7] hover:text-[#eef1f8] text-sm p-1 rounded cursor-pointer"
        >
          {isCollapsed ? "▸" : "▾"}
        </button>
      </div>
      {displayData.map((item, i) => (
        <div
          key={i}
          className={`flex items-start gap-3 py-3 ${
            i < displayData.length - 1 ? "border-b border-border-card" : ""
          }`}
        >
          <span
            className={`${BADGE_COLORS[item.filingType] ?? "bg-badge-default"} text-white text-xs font-bold px-2 py-1 rounded-[var(--radius-sm)] shrink-0 min-w-[3rem] text-center`}
          >
            {item.filingType}
          </span>
          <span className="text-text-muted text-sm shrink-0 font-[JetBrains_Mono,ui-monospace,monospace] pt-0.5">
            {formatTimestamp(item.filedAt)}
          </span>
          <p className={`flex-1 min-w-0 text-text-primary text-sm leading-relaxed ${isCollapsed ? "line-clamp-2" : ""}`}>
            {isCollapsed
              ? item.headline.split(/\s+/).slice(0, 150).join(" ") + (item.headline.split(/\s+/).length > 150 ? "..." : "")
              : item.headline}
          </p>
        </div>
      ))}
    </div>
  );
}
