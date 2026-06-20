#!/usr/bin/env bash
# Checks that no component or page file contains:
#   1. Raw hex color literals in className or style attributes
#   2. Arbitrary text-[Xpx] / text-[Xrem] size classes
#   3. Stock Tailwind size classes (text-xs, text-sm, text-base, text-lg, text-xl,
#      text-2xl, text-3xl, text-4xl, text-5xl, text-6xl)
#   4. Inline style fontSize with a raw px or rem value
#   5. Raw hex literals anywhere in .tsx source (const maps, function bodies, JSX
#      expressions) — catches hex that escapes attribute-context checks (Check 1).
#      Uses 6-char form first (#[0-9a-fA-F]{6}) then 3-char with word boundary
#      (#[0-9a-fA-F]{3}\b) so 6-char sequences are never half-matched.
#   6. Reserved typography tokens text-heading, text-body, text-display in production
#      component code — these tokens remain defined in globals.css for backward
#      compatibility but must not be used in component code. Use text-section (13px),
#      text-meta (12px), or text-label (10px) per the role-to-token mapping.
# Fails with exit code 1 if any violation is found.
#
# Exemptions:
#   - frontend/src/app/globals.css (token source of truth — not scanned)
#   - tailwind.config.* (config, not component code — not scanned)
#   - *.test.tsx, *.spec.tsx (test files — excluded via --exclude flags)
#   - tests/, __tests__/ directories (not in TARGETS)
#   - Lines containing the comment token "tv-exempt" (TradingView widget constructor config)
#   - Lines containing "// token-reserved-ok" (Check 6 escape hatch — requires human
#     orchestrator approval before use in any component)

set -euo pipefail

COMPONENT_DIR="frontend/src/components"
PAGE_FILES=(
  "frontend/src/app/page.tsx"
  "frontend/src/app/test/page.tsx"
  "frontend/src/app/admin/page.tsx"
)

VIOLATION=0

check_target() {
  local TARGET="$1"
  local INCLUDE_FLAGS="--include=*.tsx --include=*.ts"
  local EXCLUDE_FLAGS="--exclude=*.test.tsx --exclude=*.spec.tsx"

  # Check 1: Raw hex in className or style attributes
  if grep -rn $INCLUDE_FLAGS $EXCLUDE_FLAGS \
    -E '(className|style)=.*#[0-9a-fA-F]{3,6}' \
    "$TARGET" | grep -v "tv-exempt"; then
    echo "ERROR: Raw hex literal found in $TARGET"
    VIOLATION=1
  fi

  # Check 2: Arbitrary text-[Xpx] or text-[Xrem] size classes
  if grep -rn $INCLUDE_FLAGS $EXCLUDE_FLAGS \
    -E 'text-\[[0-9]+(px|rem)\]' \
    "$TARGET" | grep -v "tv-exempt"; then
    echo "ERROR: Arbitrary text-[Xpx] class found in $TARGET"
    VIOLATION=1
  fi

  # Check 3: Stock Tailwind size classes (must be replaced with token utilities)
  #    Matches: text-xs, text-sm, text-base, text-lg, text-xl,
  #             text-2xl, text-3xl, text-4xl, text-5xl, text-6xl
  #    Character-class anchor ([^a-zA-Z]|$) prevents false matches on token
  #    utilities like text-label, text-meta, text-section, etc.
  if grep -rn $INCLUDE_FLAGS $EXCLUDE_FLAGS \
    -E 'text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl)([^a-zA-Z]|$)' \
    "$TARGET" | grep -v "tv-exempt"; then
    echo "ERROR: Stock Tailwind size class found in $TARGET"
    echo "       Replace with a semantic token: text-label, text-meta, text-section,"
    echo "       text-body, text-heading, or text-display"
    VIOLATION=1
  fi

  # Check 4: Inline style fontSize with raw px or rem value
  if grep -rn $INCLUDE_FLAGS $EXCLUDE_FLAGS \
    -E 'fontSize:[[:space:]]*["'"'"'][0-9]+(px|rem)["'"'"']' \
    "$TARGET" | grep -v "tv-exempt"; then
    echo "ERROR: Inline style fontSize with raw value found in $TARGET"
    echo "       Use style={{ fontSize: 'var(--font-size-...)' }} instead"
    VIOLATION=1
  fi

  # Check 5: Raw hex literal anywhere in .tsx source (const maps, function bodies,
  #           JSX expressions, etc.) — catches hex that escapes attribute-context checks.
  #
  #   Pattern uses alternation with the 6-char form first so that a 6-char sequence
  #   is never partially matched by the 3-char branch:
  #     #[0-9a-fA-F]{6}      — full 6-char hex (e.g. #1b2230, #a78bfa)
  #     #[0-9a-fA-F]{3}\b    — 3-char shorthand (e.g. #fff, #000); \b prevents
  #                             matching the leading 3 chars of a 6-char hex
  #
  #   Only .tsx files are scanned (INCLUDE_FLAGS already limits to *.tsx / *.ts;
  #   test files are excluded via EXCLUDE_FLAGS). tv-exempt lines are filtered out.
  if grep -rn --include=*.tsx $EXCLUDE_FLAGS \
    -E '#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}\b' \
    "$TARGET" | grep -v "tv-exempt" | grep -v '&#[0-9]'; then
    echo "ERROR: Raw hex literal found outside attribute context in $TARGET"
    echo "       Move color values into design tokens (CSS vars / Tailwind config)"
    echo "       and reference them via className or var(--token-name)."
    VIOLATION=1
  fi

  # Check 6: Reserved typography tokens must not appear in production component code.
  # text-heading (16px), text-body (14px), and text-display (20px) remain defined in
  # globals.css for backward compatibility, but no production component may use them.
  # The substrate is correct; the role-to-token mapping is now mechanically enforced.
  #
  # Exemptions:
  #   - frontend/src/app/globals.css (token definitions — not scanned)
  #   - tailwind.config.* (not scanned)
  #   - *.test.tsx, *.spec.tsx (excluded via EXCLUDE_FLAGS)
  #   - Lines containing "// token-reserved-ok" (escape hatch for any future legitimate
  #     use — requires human orchestrator approval before use in any component)
  if grep -rn $INCLUDE_FLAGS $EXCLUDE_FLAGS \
    -E '\btext-(heading|body|display)\b' \
    "$TARGET" | grep -v "token-reserved-ok"; then
    echo "ERROR: Reserved typography token (text-heading, text-body, text-display) found in $TARGET"
    echo "       These tokens remain defined for backward compatibility but must not be used in"
    echo "       production component code. Use the role-to-token mapping:"
    echo "         Card/zone heading  -> text-section  (13px)"
    echo "         Body/value content -> text-meta     (12px)"
    echo "         Sub-label          -> text-label    (10px)"
    echo "       Reserved tokens text-heading/text-body/text-display are forbidden in component code."
    echo "       Use text-section (card/zone heading), text-meta (body/value), or text-label"
    echo "       (sub-label) per design-tokens role mapping. If you genuinely need a reserved token,"
    echo "       add '// token-reserved-ok' on the line above with orchestrator sign-off."
    echo "       See docs/specs/design-tokens/02-ARCHITECTURE.md §Grep enforcement extension"
    VIOLATION=1
  fi
}

check_target "$COMPONENT_DIR"

for PAGE in "${PAGE_FILES[@]}"; do
  check_target "$PAGE"
done

if [ "$VIOLATION" -eq 1 ]; then
  echo ""
  echo "Design token violations found."
  echo "See docs/specs/design-tokens/02-ARCHITECTURE.md §Enforcement for rules and exemptions."
  exit 1
fi

echo "Design token check: PASSED"
