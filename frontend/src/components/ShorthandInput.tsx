"use client";

import { useState, useEffect, useRef } from "react";
import { parseShorthand, formatShorthand } from "@/utils/shorthand";

export interface ShorthandInputProps {
  /** The current numeric value from GainerFilter context (number | null). */
  value: number | null | undefined;

  /** Called with the parsed numeric value after a valid blur, but only when
   *  the parent's conflict check does not veto the write. The component does
   *  not know whether the parent will commit the value; it uses the useEffect
   *  on value to sync displayValue after the parent resolves the write. */
  onChange: (value: number | null) => void;

  /** HTML id for the input element (for label association). */
  id: string;

  /** aria-label for inputs that have no visible label sibling. */
  ariaLabel?: string;

  /** Additional Tailwind class string appended to the base input class.
   *  Reserved for layout or presentational overrides only. Conflict and error
   *  state borders are handled internally via hasError. */
  className?: string;

  /** Whether this field's value is required (non-nullable in GainerFilter:
   *  priceMin, priceMax, volumeMin, changePctMin).
   *  When true, empty-string blur reverts to formatShorthand(value) instead
   *  of clearing to null. */
  required?: boolean;

  /** Called by the parent when it detects a min > max conflict after a valid
   *  parse. Causes ShorthandInput to set hasError = true (red border for 1500ms).
   *  The display revert is handled automatically by the useEffect on value.
   *  GainerFilterSection (Slice 3) passes a stable closure wrapping the
   *  triggerConflict handle obtained via forwardRef/useImperativeHandle. */
  onConflict?: () => void;

  /** When this prop transitions from false to true, the component reverts its
   *  display to formatShorthand(value) and shows the red error border for 1500ms.
   *  Used by GainerFilterSection to signal conflict state back to the input when
   *  the parent withholds a context write (value prop stays unchanged, so the
   *  useEffect alone cannot distinguish a conflict from no change). */
  conflictError?: boolean;
}

export default function ShorthandInput({
  value,
  onChange,
  id,
  ariaLabel,
  className,
  required = false,
  conflictError,
}: ShorthandInputProps) {
  const [displayValue, setDisplayValue] = useState<string>(formatShorthand(value));
  const [hasError, setHasError] = useState(false);
  const errorTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync display when parent resets or value changes externally (including
  // conflict revert where value prop stays unchanged, triggering displayValue
  // to revert to the last committed shorthand string).
  useEffect(() => {
    setDisplayValue(formatShorthand(value));
  }, [value]);

  // Fire revert + showError only on the rising edge of conflictError (false → true).
  // Handles the case where value prop stays unchanged after a withheld conflict
  // write, so the useEffect above cannot distinguish the conflict from no change.
  const prevConflictRef = useRef(false);
  useEffect(() => {
    const curr = conflictError ?? false;
    if (curr && !prevConflictRef.current) {
      setDisplayValue(formatShorthand(value));
      showError();
    }
    prevConflictRef.current = curr;
  }, [conflictError, value]);

  function showError() {
    if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
    setHasError(true);
    errorTimerRef.current = setTimeout(() => setHasError(false), 1500);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setDisplayValue(e.target.value);
  }

  function handleBlur() {
    const trimmed = displayValue.trim();

    if (!trimmed) {
      if (required) {
        setDisplayValue(formatShorthand(value));
        showError();
      } else {
        onChange(null);
        setDisplayValue("");
      }
      return;
    }

    const parsed = parseShorthand(trimmed);
    if (parsed === null) {
      setDisplayValue(formatShorthand(value));
      showError();
      return;
    }

    // Update display immediately to formatted shorthand.
    // If parent withholds on conflict, conflictError prop triggers revert.
    setDisplayValue(formatShorthand(parsed));
    onChange(parsed);
  }

  const baseClass =
    "bg-bg-input border rounded-[5px] px-2 py-1 text-meta text-text-primary w-full";
  const borderClass = hasError ? "border-negative" : "border-border-card";
  const combinedClass = [baseClass, borderClass, className].filter(Boolean).join(" ");

  return (
    <input
      type="text"
      id={id}
      aria-label={ariaLabel}
      value={displayValue}
      onChange={handleChange}
      onBlur={handleBlur}
      className={combinedClass}
    />
  );
}
