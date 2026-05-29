import { useState, useEffect } from "react";
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
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  useEffect(() => {
    setExpandedIndex(null);
  }, [data]);

  function handleToggle(index: number): void {
    setExpandedIndex(prev => (prev === index ? null : index));
  }

  if (!data) return <HeadlinesSkeleton />;

  const displayData = isCollapsed ? data.slice(0, 1) : data;

  return (
    <div className="bg-bg-card border border-border-card rounded-[var(--radius)] p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-label font-bold text-text-muted uppercase tracking-wide">News</span>
        <button
          onClick={onToggleCollapse}
          className="text-text-muted hover:text-text-primary text-meta p-1 rounded cursor-pointer"
        >
          {isCollapsed ? "▸" : "▾"}
        </button>
      </div>
      {displayData.map((item, i) => (
        <div
          key={i}
          className={`py-3 ${
            i < displayData.length - 1 ? "border-b border-border-card" : ""
          }`}
        >
          <div className="flex items-center gap-3 mb-1.5">
            <span
              className={`${BADGE_COLORS[item.filingType] ?? "bg-badge-default"} text-white text-meta font-bold px-2 py-1 rounded-[var(--radius-sm)] shrink-0 min-w-[3rem] text-center`}
            >
              {item.filingType}
            </span>
            <span className="text-text-muted text-meta shrink-0 font-[JetBrains_Mono,ui-monospace,monospace] pt-0.5">
              {formatTimestamp(item.filedAt)}
            </span>
            {item.site && (
              <span className="text-text-muted text-meta">· {item.site}</span>
            )}
          </div>
          <div className="flex items-start justify-between gap-2">
            {item.url ? (
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`text-accent-purple hover:underline text-meta leading-relaxed flex-1${isCollapsed ? " line-clamp-2" : ""}`}
              >
                {item.headline}
              </a>
            ) : (
              <span className={`text-text-primary text-meta leading-relaxed flex-1${isCollapsed ? " line-clamp-2" : ""}`}>
                {item.headline}
              </span>
            )}
            {item.text?.trim() && !isCollapsed && (
              <button
                onClick={() => handleToggle(i)}
                className="text-text-muted hover:text-accent-purple shrink-0 ml-2 cursor-pointer"
                aria-label={expandedIndex === i ? "Collapse" : "Expand"}
              >
                {expandedIndex === i ? "▾" : "▸"}
              </button>
            )}
          </div>
          {item.text?.trim() && expandedIndex === i && (
            <div className="mt-2">
              <p className="text-text-muted text-meta leading-relaxed">
                {item.text.length > 400 ? item.text.slice(0, 400) + "…" : item.text}
              </p>
              {item.url && item.text.length > 400 && (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent-purple hover:underline text-meta mt-1 inline-block"
                >
                  → Read full article
                </a>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
