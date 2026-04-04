import { InPlayDilutionData } from "@/types/dilution";

interface InPlayDilutionProps {
  data: InPlayDilutionData | null;
}

function InPlayDilutionSkeleton() {
  return (
    <div className="bg-bg-card border border-border-card rounded-[var(--radius)] p-5 animate-pulse">
      <div className="h-6 w-40 bg-border-card rounded mb-4" />
      <div className="h-5 w-28 bg-border-card rounded mb-3" />
      <div className="h-16 w-full bg-border-card rounded mb-4" />
      <div className="h-5 w-32 bg-border-card rounded mb-3" />
      <div className="h-16 w-full bg-border-card rounded" />
    </div>
  );
}

export default function InPlayDilution({ data }: InPlayDilutionProps) {
  if (!data) return <InPlayDilutionSkeleton />;

  const hasWarrants = data.warrants.length > 0;
  const hasConvertibles = data.convertibles.length > 0;
  const isEmpty = !hasWarrants && !hasConvertibles;

  return (
    <div className="bg-bg-card border border-border-card rounded-[var(--radius)] p-5">
      <h2 className="text-lg font-bold text-[#a78bfa] mb-3">
        In Play Dilution
      </h2>

      {isEmpty ? (
        <p className="text-text-muted text-sm">No in-play dilution found.</p>
      ) : (
        <>
          {/* WARRANTS subsection */}
          {hasWarrants && (
            <div>
              <h3 className="text-sm font-bold text-accent-red mb-2">WARRANTS</h3>
              <div className="space-y-2">
                {data.warrants.map((w, i) => {
                  const strikeColor = w.inTheMoney ? "#5ce08a" : "#f7b731";
                  return (
                    <div
                      key={i}
                      className="border border-border-card rounded-[var(--radius-sm)] p-3 bg-[rgba(10,14,22,0.4)]"
                    >
                      <p className="text-sm text-text-primary mb-1.5">
                        {w.issueDate} - {w.details}
                      </p>
                      <div className="flex gap-4 text-sm font-[JetBrains_Mono,ui-monospace,monospace]">
                        <span className="text-accent-red">
                          Remaining: {w.remaining.toLocaleString()}
                        </span>
                        <span className="text-text-muted">|</span>
                        <span style={{ color: strikeColor }}>
                          Strike: {w.strikePrice}
                        </span>
                        <span className="text-text-muted">|</span>
                        <span className="text-text-secondary">
                          Filed: {w.filedDate}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* CONVERTIBLES subsection */}
          {hasConvertibles && (
            <div>
              <h3 className="text-sm font-bold text-[#f7b731] mb-2 mt-4">
                CONVERTIBLES
              </h3>
              <div className="space-y-2">
                {data.convertibles.map((c, i) => {
                  const itm = c.inTheMoney ? "#5ce08a" : "#f7b731";
                  return (
                    <div
                      key={i}
                      className="border border-border-card rounded-[var(--radius-sm)] p-3 bg-[rgba(10,14,22,0.4)]"
                    >
                      <p className="text-sm text-text-primary mb-1.5">
                        {c.details}
                      </p>
                      <div className="flex gap-4 text-sm font-[JetBrains_Mono,ui-monospace,monospace]">
                        <span style={{ color: itm }}>
                          Remaining: {c.sharesRemaining.toLocaleString()}
                        </span>
                        <span className="text-text-muted">|</span>
                        <span style={{ color: itm }}>
                          Conv Price: {c.conversionPrice}
                        </span>
                        <span className="text-text-muted">|</span>
                        <span className="text-text-secondary">
                          Filed: {c.filedDate}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
