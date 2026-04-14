"use client";

interface ReverseSplitFlagProps {
  hasSplits: boolean;
  compact?: boolean;
}

export default function ReverseSplitFlag({ hasSplits, compact = false }: ReverseSplitFlagProps) {
  if (!hasSplits) return null;
  return (
    <span className="text-[#a78bfa] text-[10px] font-medium">
      {compact ? "↩ Rev Split" : "↩ Reverse Split History"}
    </span>
  );
}
