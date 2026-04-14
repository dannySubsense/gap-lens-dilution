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
        <div className="text-[#9aa7c7] text-[10px] uppercase tracking-widest mb-1">Reverse Split History</div>
        <div className="bg-[#2a3447] animate-pulse rounded h-4 w-full mb-1" />
        <div className="bg-[#2a3447] animate-pulse rounded h-4 w-3/4" />
      </div>
    );
  }

  return (
    <div>
      <div className="text-[#9aa7c7] text-[10px] uppercase tracking-widest mb-1">Reverse Split History</div>
      {records.length === 0 ? (
        <p className="text-[#9aa7c7] text-xs italic">No reverse split history</p>
      ) : (
        <table className="w-full text-xs">
          <thead>
            <tr className="text-[#9aa7c7] text-[10px] uppercase tracking-widest">
              <th className="text-left py-1">Execution Date</th>
              <th className="text-right py-1">From</th>
              <th className="text-right py-1">To</th>
            </tr>
          </thead>
          <tbody>
            {records.map((record, idx) => (
              <tr key={idx} className="border-t border-[#2a3447]">
                <td className="py-1 text-[#eef1f8]">{record.executionDate}</td>
                <td className="py-1 text-right text-[#eef1f8]">{record.splitFrom}</td>
                <td className="py-1 text-right text-[#eef1f8]">{record.splitTo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
