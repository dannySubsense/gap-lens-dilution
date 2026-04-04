interface MgmtCommentaryProps {
  text: string | null;
}

export default function MgmtCommentary({ text }: MgmtCommentaryProps) {
  if (!text) return null;

  return (
    <div className="bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5">
      <h2 className="text-lg font-bold text-[#a78bfa] mb-3">Mgmt Commentary</h2>
      <p className="text-sm text-[#eef1f8] leading-relaxed whitespace-pre-line">{text}</p>
    </div>
  );
}
