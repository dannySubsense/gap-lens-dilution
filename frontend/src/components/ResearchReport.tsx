"use client";

import type { ReportSection } from "@/types/dilution";

interface ResearchReportProps {
  sections: ReportSection[];
  gainPercentage: number | null;
  createdAt: string | null;
}

const riskDotColors: Record<string, string> = {
  red: "var(--color-risk-pd-high)",
  yellow: "var(--color-warning)",
  orange: "var(--color-warning-orange)",
  green: "var(--color-risk-pd-low)",
};

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export default function ResearchReport({ sections, gainPercentage, createdAt }: ResearchReportProps) {
  if (sections.length === 0) return null;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center mb-2">
        <span className="text-text-muted text-label uppercase tracking-widest">AI Research Report</span>
        {gainPercentage !== null && (
          <span className="text-positive text-meta font-semibold ml-2">
            +{gainPercentage.toFixed(1)}%
          </span>
        )}
        {createdAt && (
          <span className="text-text-muted text-meta ml-2">
            {formatDate(createdAt)}
          </span>
        )}
      </div>

      {/* Continuous flowing sections */}
      <div className="text-meta leading-relaxed space-y-2">
        {sections.map((section, idx) => (
          <div key={idx}>
            {section.title && (
              <div className="flex items-center gap-1.5 mb-0.5">
                {section.riskColor && (
                  <span style={{ color: riskDotColors[section.riskColor] }}>●</span>
                )}
                <span className="text-text-primary font-semibold">{section.title}</span>
              </div>
            )}
            <p className="text-text-muted whitespace-pre-wrap">{section.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
