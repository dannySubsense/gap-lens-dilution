import { OfferingEntry } from "@/types/dilution";

interface OfferingsProps {
  entries: OfferingEntry[];
  stockPrice: number | null;
}

function formatOfferingAmount(amount: number | null): string {
  if (amount === null) return "—";
  const m = amount / 1_000_000;
  return `$${m.toFixed(2)}M`;
}

function formatShareCount(n: number | null): string {
  if (n === null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

export default function Offerings({ entries, stockPrice }: OfferingsProps) {
  if (entries.length === 0) return null;

  const visible = entries.slice(0, 3);

  return (
    <div className="bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5">
      <h2 className="text-lg font-bold text-[#a78bfa] mb-3">Recent Offerings</h2>
      <div>
        {visible.map((entry, i) => {
          const inTheMoney =
            entry.sharePrice !== null &&
            stockPrice !== null &&
            entry.sharePrice > 0 &&
            stockPrice > 0 &&
            entry.sharePrice <= stockPrice;

          const dataColor = inTheMoney ? "#5ce08a" : "#f7b731";

          return (
            <div
              key={i}
              className="border border-[#2a3447] rounded-[5px] px-3 py-2 mb-2 bg-[rgba(10,14,22,0.4)]"
            >
              {/* Line 1: headline */}
              <p className="text-sm text-[#eef1f8] mb-1">{entry.headline ?? "—"}</p>

              {/* Line 2: data fields */}
              {entry.isAtmUsed ? (
                <div className="text-sm font-[JetBrains_Mono,ui-monospace,monospace] flex gap-1 items-center">
                  <span style={{ color: "#5ce08a" }}>
                    {formatOfferingAmount(entry.offeringAmount)}
                  </span>
                  <span className="text-[#9aa7c7]">|</span>
                  <span className="text-[#9aa7c7]">
                    {entry.filedAt ? entry.filedAt.slice(0, 10) : "—"}
                  </span>
                </div>
              ) : (
                <div className="text-sm font-[JetBrains_Mono,ui-monospace,monospace] flex gap-1 items-center flex-wrap">
                  {entry.sharesAmount !== null && (
                    <>
                      <span style={{ color: dataColor }}>
                        Amt: {formatShareCount(entry.sharesAmount)}
                      </span>
                    </>
                  )}
                  {entry.sharePrice !== null && (
                    <>
                      <span className="text-[#9aa7c7]">|</span>
                      <span style={{ color: dataColor }}>
                        ${entry.sharePrice.toFixed(2)}
                      </span>
                    </>
                  )}
                  {entry.warrantsAmount !== null && (
                    <>
                      <span className="text-[#9aa7c7]">|</span>
                      <span style={{ color: dataColor }}>
                        Wrrnts: {formatShareCount(entry.warrantsAmount)}
                      </span>
                    </>
                  )}
                  {entry.filedAt !== null && (
                    <>
                      <span className="text-[#9aa7c7]">|</span>
                      <span className="text-[#9aa7c7]">
                        {entry.filedAt.slice(0, 10)}
                      </span>
                    </>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
