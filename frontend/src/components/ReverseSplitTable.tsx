"use client";

import type { ReverseSplitRecord } from "@/types/dilution";

interface ReverseSplitTableProps {
  records: ReverseSplitRecord[];
  isLoading: boolean;
}

export default function ReverseSplitTable({ records, isLoading }: ReverseSplitTableProps) {
  if (isLoading) {
    return (
      <div>
        <div className="text-text-muted text-label uppercase tracking-widest mb-1">Reverse Split History</div>
        <div className="bg-border-card animate-pulse rounded h-4 w-full mb-1" />
        <div className="bg-border-card animate-pulse rounded h-4 w-3/4" />
      </div>
    );
  }

  return (
    <div>
      <div className="text-text-muted text-label uppercase tracking-widest mb-1">Reverse Split History</div>
      {records.length === 0 ? (
        <p className="text-text-muted text-meta italic">No reverse split history</p>
      ) : (
        <table className="w-full text-meta">
          <thead>
            <tr className="text-text-muted text-label uppercase tracking-widest">
              <th className="text-left py-1">Execution Date</th>
              <th className="text-right py-1">From</th>
              <th className="text-right py-1">To</th>
            </tr>
          </thead>
          <tbody>
            {records.map((record, idx) => (
              <tr key={idx} className="border-t border-border-card">
                <td className="py-1 text-text-primary">{record.executionDate}</td>
                <td className="py-1 text-right text-text-primary">{record.splitFrom}</td>
                <td className="py-1 text-right text-text-primary">{record.splitTo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
