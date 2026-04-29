"use client";

import type { FilingTitle } from "@/types/dilution";

interface FilingTitlesListProps {
  items: FilingTitle[];
  maxItems?: number;
  isLoading: boolean;
}

export default function FilingTitlesList({ items, maxItems, isLoading }: FilingTitlesListProps) {
  if (isLoading) {
    return (
      <div>
        <div className="text-text-muted text-label uppercase tracking-widest mb-1">
          {maxItems === 1 ? "Latest Filing" : "Filing History"}
        </div>
        <div className="bg-border-card animate-pulse rounded h-4 w-3/4 mb-1" />
        <div className="bg-border-card animate-pulse rounded h-3 w-1/2" />
      </div>
    );
  }

  if (items.length === 0) return null;

  const display = maxItems ? items.slice(0, maxItems) : items;

  return (
    <div>
      <div className="text-text-muted text-label uppercase tracking-widest mb-1">
        {maxItems === 1 ? "Latest Filing" : "Filing History"}
      </div>
      {display.map((item, idx) => (
        <div key={idx} className="mb-2">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="bg-border-card text-text-muted text-label font-bold px-1.5 py-0.5 rounded-[3px]">
              {item.formType}
            </span>
            <span className="text-text-muted text-label">
              {item.filedAt ? new Date(item.filedAt).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : ""}
            </span>
          </div>
          <p className={`text-text-primary text-meta leading-relaxed${maxItems === 1 ? " line-clamp-2" : ""}`}>
            {item.headline}
          </p>
        </div>
      ))}
    </div>
  );
}
