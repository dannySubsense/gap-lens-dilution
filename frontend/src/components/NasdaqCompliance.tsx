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
        <div className="text-[#9aa7c7] text-[10px] uppercase tracking-widest mb-1">Nasdaq Compliance</div>
        <div className="bg-[#2a3447] animate-pulse rounded h-4 w-full mb-1" />
        <div className="bg-[#2a3447] animate-pulse rounded h-4 w-3/4" />
      </div>
    );
  }

  return (
    <div>
      <div className="text-[#9aa7c7] text-[10px] uppercase tracking-widest mb-1">Nasdaq Compliance</div>
      {records.length === 0 ? (
        <p className="text-[#9aa7c7] text-xs italic">No compliance deficiencies</p>
      ) : (
        records.map((record, idx) => (
          <div key={idx} className="bg-[#1b2230] border border-[#2a3447] rounded-[5px] p-2 mb-2">
            {record.deficiency && (
              <p className="text-[#eef1f8] text-xs font-semibold mb-1">{record.deficiency}</p>
            )}
            <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10px]">
              {record.status && (
                <span className="text-[#9aa7c7]">Status: <span className="text-[#eef1f8]">{record.status}</span></span>
              )}
              {record.date && (
                <span className="text-[#9aa7c7]">Date: <span className="text-[#eef1f8]">{record.date}</span></span>
              )}
              {record.risk && (
                <span className="text-[#9aa7c7]">Risk: <span className="text-[#eef1f8]">{record.risk}</span></span>
              )}
            </div>
            {record.notes && (
              <p className="text-[#9aa7c7] text-[10px] mt-1">{record.notes}</p>
            )}
          </div>
        ))
      )}
    </div>
  );
}
