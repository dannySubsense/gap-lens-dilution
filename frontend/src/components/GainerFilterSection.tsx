"use client";
import { useAppSettings } from "@/context/AppSettingsContext";
import { DEFAULT_GAINER_FILTER } from "@/types/dilution";
import { useState } from "react";
import ShorthandInput from "@/components/ShorthandInput";

const FMP_SECTORS = [
  "Technology",
  "Healthcare",
  "Financial Services",
  "Consumer Cyclical",
  "Consumer Defensive",
  "Industrials",
  "Basic Materials",
  "Energy",
  "Real Estate",
  "Utilities",
  "Communication Services",
] as const;

const inputBase =
  "bg-bg-input border border-border-card rounded-[5px] px-2 py-1 text-meta text-text-primary w-full";
const inputConflict =
  "bg-bg-input border border-negative rounded-[5px] px-2 py-1 text-meta text-text-primary w-full";

export default function GainerFilterSection() {
  const { gainerFilter, setGainerFilter } = useAppSettings();

  const [priceConflict, setPriceConflict] = useState(false);
  const [volumeConflict, setVolumeConflict] = useState(false);
  const [changePctConflict, setChangePctConflict] = useState(false);
  const [mcapConflict, setMcapConflict] = useState(false);
  const [floatConflict, setFloatConflict] = useState(false);

  // Country free-text input draft
  const [countryInputDraft, setCountryInputDraft] = useState("");
  const [countryInputError, setCountryInputError] = useState<string | null>(null);

  function handleCountryBlur() {
    const tokens = countryInputDraft
      .split(",")
      .map((t) => t.trim().toUpperCase())
      .filter((t) => t.length > 0);

    if (tokens.length === 0) {
      return;
    }

    const invalid = tokens.find((t) => !/^[A-Z]{2}$/.test(t));
    if (invalid !== undefined) {
      setCountryInputError("Each code must be 2 letters (e.g. US, CN)");
      return;
    }

    const deduped = [...new Set(tokens)];
    const existing = gainerFilter.countryExclude;
    const merged = [...new Set([...existing, ...deduped])];

    if (merged.length > 5) {
      setCountryInputError("Maximum 5 country codes");
      return;
    }

    setGainerFilter({ ...gainerFilter, countryExclude: merged });
    setCountryInputDraft("");
    setCountryInputError(null);
  }

  function removeCountryCode(code: string) {
    setGainerFilter({
      ...gainerFilter,
      countryExclude: gainerFilter.countryExclude.filter((c) => c !== code),
    });
  }

  function handleReset() {
    setGainerFilter(DEFAULT_GAINER_FILTER);
    setPriceConflict(false);
    setVolumeConflict(false);
    setChangePctConflict(false);
    setMcapConflict(false);
    setFloatConflict(false);
    setCountryInputDraft("");
    setCountryInputError(null);
  }

  return (
    <div>
      <p className="text-meta font-bold text-text-muted uppercase tracking-wide mb-3">
        GAINER FILTER
      </p>

      {/* Price Range */}
      <div className="mb-3">
        <label
          htmlFor="price-min"
          className="text-meta text-text-muted mb-1 block"
        >
          Price ($)
        </label>
        <div className="flex items-center gap-2">
          <ShorthandInput
            id="price-min"
            value={gainerFilter.priceMin}
            required
            conflictError={priceConflict}
            onChange={(val) => {
              const newMin = val ?? DEFAULT_GAINER_FILTER.priceMin;
              const conflict = newMin >= gainerFilter.priceMax;
              setPriceConflict(conflict);
              if (!conflict) {
                setGainerFilter({ ...gainerFilter, priceMin: newMin });
              }
            }}
          />
          <span className="text-meta text-text-muted shrink-0">–</span>
          <ShorthandInput
            id="price-max"
            value={gainerFilter.priceMax}
            required
            ariaLabel="Price Max"
            conflictError={priceConflict}
            onChange={(val) => {
              const newMax = val ?? DEFAULT_GAINER_FILTER.priceMax;
              const conflict = gainerFilter.priceMin >= newMax;
              setPriceConflict(conflict);
              if (!conflict) {
                setGainerFilter({ ...gainerFilter, priceMax: newMax });
              }
            }}
          />
        </div>
        {priceConflict && (
          <span className="text-label text-negative">
            Min must be less than Max
          </span>
        )}
      </div>

      {/* Volume Range */}
      <div className="mb-3">
        <label
          htmlFor="volume-min"
          className="text-meta text-text-muted mb-1 block"
        >
          Volume
        </label>
        <div className="flex items-center gap-2">
          <ShorthandInput
            id="volume-min"
            value={gainerFilter.volumeMin}
            required
            conflictError={volumeConflict}
            onChange={(val) => {
              const newMin = val ?? DEFAULT_GAINER_FILTER.volumeMin;
              const conflict =
                gainerFilter.volumeMax !== null && newMin >= gainerFilter.volumeMax;
              setVolumeConflict(conflict);
              if (!conflict) {
                setGainerFilter({ ...gainerFilter, volumeMin: newMin });
              }
            }}
          />
          <span className="text-meta text-text-muted shrink-0">–</span>
          <ShorthandInput
            id="volume-max"
            value={gainerFilter.volumeMax}
            ariaLabel="Volume Max"
            conflictError={volumeConflict}
            onChange={(val) => {
              const conflict =
                val !== null && val <= gainerFilter.volumeMin;
              setVolumeConflict(conflict);
              if (!conflict) {
                setGainerFilter({ ...gainerFilter, volumeMax: val });
              }
            }}
          />
        </div>
        {volumeConflict && (
          <span className="text-label text-negative">
            Min must be less than Max
          </span>
        )}
      </div>

      {/* % Change Range */}
      <div className="mb-3">
        <label
          htmlFor="change-pct-min"
          className="text-meta text-text-muted mb-1 block"
        >
          % Change
        </label>
        <div className="flex items-center gap-2">
          <ShorthandInput
            id="change-pct-min"
            value={gainerFilter.changePctMin}
            required
            conflictError={changePctConflict}
            onChange={(val) => {
              const newMin = val ?? DEFAULT_GAINER_FILTER.changePctMin;
              const conflict =
                gainerFilter.changePctMax !== null && newMin >= gainerFilter.changePctMax;
              setChangePctConflict(conflict);
              if (!conflict) {
                setGainerFilter({ ...gainerFilter, changePctMin: newMin });
              }
            }}
          />
          <span className="text-meta text-text-muted shrink-0">–</span>
          <ShorthandInput
            id="change-pct-max"
            value={gainerFilter.changePctMax}
            ariaLabel="% Change Max"
            conflictError={changePctConflict}
            onChange={(val) => {
              const conflict =
                val !== null && val <= gainerFilter.changePctMin;
              setChangePctConflict(conflict);
              if (!conflict) {
                setGainerFilter({ ...gainerFilter, changePctMax: val });
              }
            }}
          />
        </div>
        {changePctConflict && (
          <span className="text-label text-negative">
            Min must be less than Max
          </span>
        )}
      </div>

      {/* Market Cap Range */}
      <div className="mb-3">
        <label
          htmlFor="mcap-min"
          className="text-meta text-text-muted mb-1 block"
        >
          Market Cap ($)
        </label>
        <div className="flex items-center gap-2">
          <ShorthandInput
            id="mcap-min"
            value={gainerFilter.mcapMin}
            ariaLabel="Market Cap Min"
            conflictError={mcapConflict}
            onChange={(val) => {
              const conflict =
                val !== null && gainerFilter.mcapMax !== null && val >= gainerFilter.mcapMax;
              setMcapConflict(conflict);
              if (!conflict) {
                setGainerFilter({ ...gainerFilter, mcapMin: val });
              }
            }}
          />
          <span className="text-meta text-text-muted shrink-0">–</span>
          <ShorthandInput
            id="mcap-max"
            value={gainerFilter.mcapMax}
            ariaLabel="Market Cap Max"
            conflictError={mcapConflict}
            onChange={(val) => {
              const conflict =
                gainerFilter.mcapMin !== null && val !== null && gainerFilter.mcapMin >= val;
              setMcapConflict(conflict);
              if (!conflict) {
                setGainerFilter({ ...gainerFilter, mcapMax: val });
              }
            }}
          />
        </div>
        {mcapConflict && (
          <span className="text-label text-negative">
            Min must be less than Max
          </span>
        )}
      </div>

      {/* Float Range */}
      <div className="mb-3">
        <label
          htmlFor="float-min"
          className="text-meta text-text-muted mb-1 block"
        >
          Float (shares)
        </label>
        <div className="flex items-center gap-2">
          <ShorthandInput
            id="float-min"
            value={gainerFilter.floatMin}
            ariaLabel="Float Min"
            conflictError={floatConflict}
            onChange={(val) => {
              const conflict =
                val !== null && gainerFilter.floatMax !== null && val >= gainerFilter.floatMax;
              setFloatConflict(conflict);
              if (!conflict) {
                setGainerFilter({ ...gainerFilter, floatMin: val });
              }
            }}
          />
          <span className="text-meta text-text-muted shrink-0">–</span>
          <ShorthandInput
            id="float-max"
            value={gainerFilter.floatMax}
            ariaLabel="Float Max"
            conflictError={floatConflict}
            onChange={(val) => {
              const conflict =
                gainerFilter.floatMin !== null && val !== null && gainerFilter.floatMin >= val;
              setFloatConflict(conflict);
              if (!conflict) {
                setGainerFilter({ ...gainerFilter, floatMax: val });
              }
            }}
          />
        </div>
        {floatConflict && (
          <span className="text-label text-negative">
            Min must be less than Max
          </span>
        )}
      </div>

      {/* Sector Exclude */}
      <div className="mb-3">
        <label className="text-meta text-text-muted mb-2 block">
          Sector Exclude
        </label>
        <div className="flex flex-wrap gap-1.5">
          {FMP_SECTORS.map((sector) => {
            const isActive = gainerFilter.sectorExclude.includes(sector);
            return (
              <button
                key={sector}
                type="button"
                role="checkbox"
                aria-checked={isActive}
                onClick={() => {
                  const next = isActive
                    ? gainerFilter.sectorExclude.filter((s) => s !== sector)
                    : [...gainerFilter.sectorExclude, sector];
                  setGainerFilter({ ...gainerFilter, sectorExclude: next });
                }}
                className={
                  isActive
                    ? "text-label text-text-inverse bg-accent-purple border border-accent-purple rounded-full px-2 py-0.5 cursor-pointer"
                    : "text-label text-text-muted border border-border-card rounded-full px-2 py-0.5 cursor-pointer"
                }
              >
                {sector}
              </button>
            );
          })}
        </div>
      </div>

      {/* Country Exclude */}
      <div className="mb-3">
        <label htmlFor="country-input" className="text-meta text-text-muted mb-2 block">
          Country Exclude
        </label>
        <input
          id="country-input"
          type="text"
          placeholder="e.g. CN, IL, KY"
          value={countryInputDraft}
          onChange={(e) => {
            setCountryInputDraft(e.target.value);
            setCountryInputError(null);
          }}
          onBlur={handleCountryBlur}
          className={countryInputError ? inputConflict : inputBase}
        />
        {countryInputError && (
          <span className="text-label text-negative">{countryInputError}</span>
        )}
        {gainerFilter.countryExclude.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {gainerFilter.countryExclude.map((code) => (
              <span
                key={code}
                className="text-label text-text-inverse bg-accent-purple border border-accent-purple rounded-full px-2 py-0.5 flex items-center gap-1"
              >
                {code}
                <button
                  type="button"
                  aria-label={`Remove ${code}`}
                  onClick={() => removeCountryCode(code)}
                  className="text-label text-text-inverse leading-none"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Reset button */}
      <button
        type="button"
        onClick={handleReset}
        className="w-full text-meta text-text-muted border border-border-card rounded-[5px] py-1.5 mt-2 hover:text-text-primary hover:border-accent-purple transition-colors"
      >
        Reset to defaults
      </button>
    </div>
  );
}
