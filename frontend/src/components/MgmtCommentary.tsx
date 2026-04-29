interface MgmtCommentaryProps {
  text: string | null;
}

export default function MgmtCommentary({ text }: MgmtCommentaryProps) {
  if (!text) return null;

  return (
    <div className="bg-bg-card border border-border-card rounded-[9px] p-5">
      <h2 className="text-heading font-bold text-accent-purple mb-3">Mgmt Commentary</h2>
      <p className="text-body text-text-primary leading-relaxed whitespace-pre-line">{text}</p>
    </div>
  );
}
