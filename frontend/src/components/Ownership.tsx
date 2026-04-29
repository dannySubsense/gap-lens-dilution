import { OwnershipData } from "@/types/dilution";

interface OwnershipProps {
  data: OwnershipData | null;
}

export default function Ownership({ data }: OwnershipProps) {
  if (!data || data.owners.length === 0) return null;

  const reportedDateShort = data.reportedDate.slice(0, 10);

  return (
    <div className="bg-bg-card border border-border-card rounded-[9px] p-5">
      <h2 className="text-heading font-bold text-accent-purple mb-1">Ownership</h2>
      <p className="text-meta text-text-muted mb-3 font-[JetBrains_Mono,ui-monospace,monospace]">
        As of {reportedDateShort}
      </p>
      <table className="w-full">
        <thead>
          <tr className="text-meta text-text-muted uppercase tracking-wide border-b border-border-card pb-1">
            <th className="text-left pb-1 font-normal">Owner</th>
            <th className="text-left pb-1 font-normal">Title</th>
            <th className="text-right pb-1 font-normal">Shares</th>
          </tr>
        </thead>
        <tbody>
          {data.owners.map((owner, i) => (
            <tr
              key={i}
              className={`text-body text-text-primary py-1.5 ${
                i < data.owners.length - 1 ? "border-b border-border-card" : ""
              }`}
            >
              <td className="font-medium py-1.5">{owner.ownerName}</td>
              <td className="text-text-muted py-1.5">{owner.title}</td>
              <td className="text-positive font-bold font-[JetBrains_Mono,ui-monospace,monospace] text-right py-1.5">
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
