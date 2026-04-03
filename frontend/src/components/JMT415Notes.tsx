import { JMT415Note } from "@/types/dilution";

interface JMT415NotesProps {
  data: JMT415Note[] | null;
}

function JMT415NotesSkeleton() {
  return (
    <div className="bg-bg-card border border-border-card rounded-[var(--radius)] p-5 animate-pulse">
      <div className="h-6 w-48 bg-border-card rounded mb-4" />
      <div className="space-y-4">
        {[1, 2].map((i) => (
          <div key={i} className="space-y-2">
            <div className="h-4 w-24 bg-border-card rounded" />
            <div className="h-4 w-full bg-border-card rounded" />
            <div className="h-4 w-3/4 bg-border-card rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function JMT415Notes({ data }: JMT415NotesProps) {
  if (!data) return <JMT415NotesSkeleton />;

  return (
    <div className="bg-bg-card border border-border-card rounded-[var(--radius)] p-5">
      <h2 className="text-lg font-bold text-[#a78bfa] mb-3">
        JMT415 Previous Notes
      </h2>
      <div className="max-h-96 overflow-y-auto space-y-4 pr-1">
        {data.map((note, i) => (
          <div
            key={i}
            className={`pb-4 ${
              i < data.length - 1 ? "border-b border-border-card" : ""
            }`}
          >
            <p className="text-text-muted text-sm font-[JetBrains_Mono,ui-monospace,monospace] mb-1">
              {note.date}
            </p>
            <p className="text-text-primary text-sm font-bold mb-1">
              {note.ticker}
            </p>
            {note.content.map((line, j) => (
              <p key={j} className="text-text-secondary text-sm leading-relaxed">
                {line}
              </p>
            ))}
          </div>
        ))}
        {data.length === 0 && (
          <p className="text-text-muted text-sm">No notes available.</p>
        )}
      </div>
    </div>
  );
}
