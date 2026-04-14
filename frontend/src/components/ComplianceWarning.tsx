"use client";

interface ComplianceWarningProps {
  hasDeficiency: boolean;
  compact?: boolean;
}

export default function ComplianceWarning({ hasDeficiency, compact = false }: ComplianceWarningProps) {
  if (!hasDeficiency) return null;
  return (
    <span className="text-[#eab308] text-[10px] font-medium">
      {compact ? "⚠ Non-Compl" : "⚠ Nasdaq Non-Compliant"}
    </span>
  );
}
