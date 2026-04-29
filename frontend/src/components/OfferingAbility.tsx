interface OfferingAbilityProps {
  offeringAbilityDesc: string | null;
}

function getSegmentStyle(segment: string): string {
  const lower = segment.toLowerCase();

  if (lower.includes("pending s-1") || lower.includes("pending f-1")) {
    return "text-positive font-semibold";
  }

  const isCapacity =
    lower.includes("shelf capacity") ||
    lower.includes("atm capacity") ||
    lower.includes("equity line capacity");

  if (isCapacity) {
    if (lower.includes("$0.00")) {
      return "text-negative";
    }
    return "text-positive font-semibold";
  }

  return "text-text-primary";
}

export default function OfferingAbility({ offeringAbilityDesc }: OfferingAbilityProps) {
  if (!offeringAbilityDesc) return null;

  const segments = offeringAbilityDesc
    .split(",")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

  if (segments.length === 0) return null;

  return (
    <div className="bg-bg-card border border-border-card rounded-[9px] p-5">
      <h2 className="text-section font-bold text-accent-purple mb-3">Offering Ability</h2>
      <div className="space-y-1">
        {segments.map((segment, i) => (
          <div key={i} className={`text-meta px-3 py-1 rounded-[5px] ${getSegmentStyle(segment)}`}>
            {segment}
          </div>
        ))}
      </div>
    </div>
  );
}
