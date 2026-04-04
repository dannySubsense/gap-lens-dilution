import { OwnershipData } from "@/types/dilution";

interface OwnershipProps {
  data: OwnershipData | null;
}

export default function Ownership({ data }: OwnershipProps) {
  if (!data || data.owners.length === 0) return null;

  const reportedDateShort = data.reportedDate.slice(0, 10);

  return (
    <div className="bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5">
      <h2 className="text-lg font-bold text-[#a78bfa] mb-1">Ownership</h2>
      <p className="text-xs text-[#9aa7c7] mb-3 font-[JetBrains_Mono,ui-monospace,monospace]">
        As of {reportedDateShort}
      </p>
      <table className="w-full">
        <thead>
          <tr className="text-xs text-[#9aa7c7] uppercase tracking-wide border-b border-[#2a3447] pb-1">
            <th className="text-left pb-1 font-normal">Owner</th>
            <th className="text-left pb-1 font-normal">Title</th>
            <th className="text-right pb-1 font-normal">Shares</th>
          </tr>
        </thead>
        <tbody>
          {data.owners.map((owner, i) => (
            <tr
              key={i}
              className={`text-sm text-[#eef1f8] py-1.5 ${
                i < data.owners.length - 1 ? "border-b border-[#2a3447]" : ""
              }`}
            >
              <td className="font-medium py-1.5">{owner.ownerName}</td>
              <td className="text-[#9aa7c7] py-1.5">{owner.title}</td>
              <td className="text-[#5ce08a] font-bold font-[JetBrains_Mono,ui-monospace,monospace] text-right py-1.5">
                {owner.commonSharesAmount !== null
                  ? owner.commonSharesAmount.toLocaleString()
                  : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
