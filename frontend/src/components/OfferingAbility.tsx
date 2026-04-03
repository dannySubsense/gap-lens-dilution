import { OfferingAbilityData } from "@/types/dilution";

interface OfferingAbilityProps {
  data: OfferingAbilityData | null;
}

function OfferingAbilitySkeleton() {
  return (
    <div className="bg-bg-card border border-border-card rounded-[var(--radius)] p-5 animate-pulse">
      <div className="h-6 w-40 bg-border-card rounded mb-4" />
      <div className="space-y-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-4 w-48 bg-border-card rounded" />
        ))}
      </div>
    </div>
  );
}

export default function OfferingAbility({ data }: OfferingAbilityProps) {
  if (!data) return <OfferingAbilitySkeleton />;

  return (
    <div className="bg-bg-card border border-border-card rounded-[var(--radius)] p-5">
      <h2 className="text-lg font-bold text-[#a78bfa] mb-3">
        Offering Ability
      </h2>
      <div className="space-y-1.5">
        {[
          { concerning: data.shelfCapacityConcerning, text: `Shelf Capacity: ${data.shelfCapacity}` },
          { concerning: data.hasATM, text: data.hasATM ? "Active ATM" : "No ATM" },
          { concerning: data.hasEquityLine, text: data.hasEquityLine ? "Active Equity Line" : "No Equity Line" },
          { concerning: data.hasS1Offering, text: data.hasS1Offering ? "Active S-1 Offering" : "No S-1 Offering" },
        ].map((item, i) => (
          <div
            key={i}
            className={`text-sm px-3 py-1.5 rounded-[var(--radius-sm)] ${
              item.concerning
                ? "text-accent-red font-semibold bg-[rgba(255,107,107,0.08)]"
                : "text-text-primary"
            }`}
          >
            {item.text}
          </div>
        ))}
      </div>
    </div>
  );
}
