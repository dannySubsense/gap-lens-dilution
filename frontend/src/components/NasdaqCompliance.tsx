"use client";

import type { ComplianceRecord } from "@/types/dilution";

interface NasdaqComplianceProps {
  records: ComplianceRecord[];
  isLoading: boolean;
}

export default function NasdaqCompliance({ records, isLoading }: NasdaqComplianceProps) {
  if (isLoading) {
    return (
      <div>
        <div className="text-text-muted text-label uppercase tracking-widest mb-1">Nasdaq Compliance</div>
        <div className="bg-border-card animate-pulse rounded h-4 w-full mb-1" />
        <div className="bg-border-card animate-pulse rounded h-4 w-3/4" />
      </div>
    );
  }

  return (
    <div>
      <div className="text-text-muted text-label uppercase tracking-widest mb-1">Nasdaq Compliance</div>
      {records.length === 0 ? (
        <p className="text-text-muted text-meta italic">No compliance deficiencies</p>
      ) : (
        records.map((record, idx) => (
          <div key={idx} className="bg-bg-card border border-border-card rounded-[5px] p-2 mb-2">
            {record.deficiency && (
              <p className="text-text-primary text-meta font-semibold mb-1">{record.deficiency}</p>
            )}
            <div className="flex flex-wrap gap-x-3 gap-y-1 text-label">
              {record.status && (
                <span className="text-text-muted">Status: <span className="text-text-primary">{record.status}</span></span>
              )}
              {record.date && (
                <span className="text-text-muted">Date: <span className="text-text-primary">{record.date}</span></span>
              )}
              {record.risk && (
                <span className="text-text-muted">Risk: <span className="text-text-primary">{record.risk}</span></span>
              )}
            </div>
            {record.notes && (
              <p className="text-text-muted text-label mt-1">{record.notes}</p>
            )}
          </div>
        ))
      )}
    </div>
  );
}
