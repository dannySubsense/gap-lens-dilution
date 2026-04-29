"use client";

interface ComplianceWarningProps {
  hasDeficiency: boolean;
  compact?: boolean;
}

export default function ComplianceWarning({ hasDeficiency, compact = false }: ComplianceWarningProps) {
  if (!hasDeficiency) return null;
  return (
    <span className="text-warning text-label font-medium">
      {compact ? "⚠ Non-Compl" : "⚠ Nasdaq Non-Compliant"}
    </span>
  );
}
