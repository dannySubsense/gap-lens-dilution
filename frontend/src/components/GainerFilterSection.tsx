"use client";
import { useAppSettings } from "@/context/AppSettingsContext";
import { DEFAULT_GAINER_FILTER } from "@/types/dilution";
import { useState } from "react";

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

  // Local price state — needed to handle conflict validation without committing
  // invalid values to context.
  const [localPriceMin, setLocalPriceMin] = useState(gainerFilter.priceMin);
  const [localPriceMax, setLocalPriceMax] = useState(gainerFilter.priceMax);
  const [priceConflict, setPriceConflict] = useState(false);

  // Volume — empty field guard
  const [volumeEmpty, setVolumeEmpty] = useState(false);
  // Change pct — empty field guard
  const [changePctEmpty, setChangePctEmpty] = useState(false);

  // Volume range — max is new; min already managed via direct context write
  const [localVolumeMax, setLocalVolumeMax] = useState<number | null>(gainerFilter.volumeMax);
  const [volumeConflict, setVolumeConflict] = useState(false);

  // % Change range — max is new; min already managed via direct context write
  const [localChangePctMax, setLocalChangePctMax] = useState<number | null>(gainerFilter.changePctMax);
  const [changePctConflict, setChangePctConflict] = useState(false);

  // Market Cap range — min is new; max already managed via direct context write
  const [localMcapMin, setLocalMcapMin] = useState<number | null>(gainerFilter.mcapMin);
  const [mcapConflict, setMcapConflict] = useState(false);

  // Float range — min is new; max already managed via direct context write
  const [localFloatMin, setLocalFloatMin] = useState<number | null>(gainerFilter.floatMin);
  const [floatConflict, setFloatConflict] = useState(false);

  // Country free-text input draft
  const [countryInputDraft, setCountryInputDraft] = useState("");
  const [countryInputError, setCountryInputError] = useState<string | null>(null);

  function handlePriceMinChange(e: React.ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value;
    const newMin = parseFloat(raw);
    setLocalPriceMin(isNaN(newMin) ? 0 : newMin);
    if (!isNaN(newMin) && newMin < localPriceMax) {
      setGainerFilter({ ...gainerFilter, priceMin: newMin, priceMax: localPriceMax });
      setPriceConflict(false);
    } else {
      setPriceConflict(true);
    }
  }

  function handlePriceMaxChange(e: React.ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value;
    const newMax = parseFloat(raw);
    setLocalPriceMax(isNaN(newMax) ? 0 : newMax);
    if (!isNaN(newMax) && localPriceMin < newMax) {
      setGainerFilter({ ...gainerFilter, priceMin: localPriceMin, priceMax: newMax });
      setPriceConflict(false);
    } else {
      setPriceConflict(true);
    }
  }

  function handleVolumeChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === "") {
      setVolumeEmpty(true);
      setVolumeConflict(false);
      return;
    }
    setVolumeEmpty(false);
    const val = parseFloat(e.target.value);
    if (!isNaN(val)) {
      setGainerFilter({ ...gainerFilter, volumeMin: val });
      if (localVolumeMax !== null && val > localVolumeMax) {
        setVolumeConflict(true);
      } else {
        setVolumeConflict(false);
      }
    }
  }

  function handleVolumeMaxChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === "") {
      setLocalVolumeMax(null);
      setGainerFilter({ ...gainerFilter, volumeMax: null });
      setVolumeConflict(false);
      return;
    }
    const val = parseFloat(e.target.value);
    if (!isNaN(val)) {
      setLocalVolumeMax(val);
      if (gainerFilter.volumeMin > val) {
        setVolumeConflict(true);
      } else {
        setGainerFilter({ ...gainerFilter, volumeMax: val });
        setVolumeConflict(false);
      }
    }
  }

  function handleChangePctChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === "") {
      setChangePctEmpty(true);
      setChangePctConflict(false);
      return;
    }
    setChangePctEmpty(false);
    const val = parseFloat(e.target.value);
    if (!isNaN(val)) {
      setGainerFilter({ ...gainerFilter, changePctMin: val });
      if (localChangePctMax !== null && val > localChangePctMax) {
        setChangePctConflict(true);
      } else {
        setChangePctConflict(false);
      }
    }
  }

  function handleChangePctMaxChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === "") {
      setLocalChangePctMax(null);
      setGainerFilter({ ...gainerFilter, changePctMax: null });
      setChangePctConflict(false);
      return;
    }
    const val = parseFloat(e.target.value);
    if (!isNaN(val)) {
      setLocalChangePctMax(val);
      if (gainerFilter.changePctMin > val) {
        setChangePctConflict(true);
      } else {
        setGainerFilter({ ...gainerFilter, changePctMax: val });
        setChangePctConflict(false);
      }
    }
  }

  function handleMcapMinChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === "") {
      setLocalMcapMin(null);
      setGainerFilter({ ...gainerFilter, mcapMin: null });
      setMcapConflict(false);
      return;
    }
    const val = parseFloat(e.target.value);
    if (!isNaN(val)) {
      setLocalMcapMin(val);
      if (gainerFilter.mcapMax !== null && val >= gainerFilter.mcapMax) {
        setMcapConflict(true);
      } else {
        setGainerFilter({ ...gainerFilter, mcapMin: val });
        setMcapConflict(false);
      }
    }
  }

  function handleMcapMaxChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === "") {
      setGainerFilter({ ...gainerFilter, mcapMax: null });
      setMcapConflict(false);
      return;
    }
    const newMcapMax = parseFloat(e.target.value);
    if (!isNaN(newMcapMax)) {
      setGainerFilter({ ...gainerFilter, mcapMax: newMcapMax });
      if (localMcapMin !== null && localMcapMin >= newMcapMax) {
        setMcapConflict(true);
      } else {
        setMcapConflict(false);
      }
    }
  }

  function handleFloatMinChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === "") {
      setLocalFloatMin(null);
      setGainerFilter({ ...gainerFilter, floatMin: null });
      setFloatConflict(false);
      return;
    }
    const val = parseFloat(e.target.value);
    if (!isNaN(val)) {
      setLocalFloatMin(val);
      if (gainerFilter.floatMax !== null && val >= gainerFilter.floatMax) {
        setFloatConflict(true);
      } else {
        setGainerFilter({ ...gainerFilter, floatMin: val });
        setFloatConflict(false);
      }
    }
  }

  function handleFloatMaxChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === "") {
      setGainerFilter({ ...gainerFilter, floatMax: null });
      setFloatConflict(false);
      return;
    }
    const newFloatMax = parseFloat(e.target.value);
    if (!isNaN(newFloatMax)) {
      setGainerFilter({ ...gainerFilter, floatMax: newFloatMax });
      if (localFloatMin !== null && localFloatMin >= newFloatMax) {
        setFloatConflict(true);
      } else {
        setFloatConflict(false);
      }
    }
  }

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
    setLocalPriceMin(DEFAULT_GAINER_FILTER.priceMin);
    setLocalPriceMax(DEFAULT_GAINER_FILTER.priceMax);
    setPriceConflict(false);
    setVolumeEmpty(false);
    setLocalVolumeMax(null);
    setVolumeConflict(false);
    setChangePctEmpty(false);
    setLocalChangePctMax(null);
    setChangePctConflict(false);
    setLocalMcapMin(null);
    setMcapConflict(false);
    setLocalFloatMin(null);
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
          <input
            id="price-min"
            type="number"
            min="0"
            step="0.01"
            value={localPriceMin}
            onChange={handlePriceMinChange}
            className={priceConflict ? inputConflict : inputBase}
          />
          <span className="text-meta text-text-muted shrink-0">–</span>
          <input
            id="price-max"
            type="number"
            min="0"
            step="0.01"
            value={localPriceMax}
            onChange={handlePriceMaxChange}
            aria-label="Price Max"
            className={priceConflict ? inputConflict : inputBase}
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
          <input
            id="volume-min"
            type="number"
            min="0"
            step="1"
            value={gainerFilter.volumeMin}
            onChange={handleVolumeChange}
            className={volumeEmpty || volumeConflict ? inputConflict : inputBase}
          />
          <span className="text-meta text-text-muted shrink-0">–</span>
          <input
            id="volume-max"
            type="number"
            min="0"
            step="1"
            value={localVolumeMax ?? ""}
            onChange={handleVolumeMaxChange}
            aria-label="Volume Max"
            className={volumeConflict ? inputConflict : inputBase}
          />
        </div>
        {volumeEmpty && (
          <span className="text-label text-negative">Required</span>
        )}
        {!volumeEmpty && volumeConflict && (
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
          <input
            id="change-pct-min"
            type="number"
            min="0"
            step="0.1"
            value={gainerFilter.changePctMin}
            onChange={handleChangePctChange}
            className={changePctEmpty || changePctConflict ? inputConflict : inputBase}
          />
          <span className="text-meta text-text-muted shrink-0">–</span>
          <input
            id="change-pct-max"
            type="number"
            min="0"
            step="0.1"
            value={localChangePctMax ?? ""}
            onChange={handleChangePctMaxChange}
            aria-label="% Change Max"
            className={changePctConflict ? inputConflict : inputBase}
          />
        </div>
        {changePctEmpty && (
          <span className="text-label text-negative">Required</span>
        )}
        {!changePctEmpty && changePctConflict && (
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
          <input
            id="mcap-min"
            type="number"
            min="0"
            step="1000000"
            value={localMcapMin ?? ""}
            onChange={handleMcapMinChange}
            aria-label="Market Cap Min"
            className={mcapConflict ? inputConflict : inputBase}
          />
          <span className="text-meta text-text-muted shrink-0">–</span>
          <input
            id="mcap-max"
            type="number"
            min="0"
            step="1000000"
            value={gainerFilter.mcapMax ?? ""}
            onChange={handleMcapMaxChange}
            aria-label="Market Cap Max"
            className={mcapConflict ? inputConflict : inputBase}
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
          <input
            id="float-min"
            type="number"
            min="0"
            step="1000000"
            value={localFloatMin ?? ""}
            onChange={handleFloatMinChange}
            aria-label="Float Min"
            className={floatConflict ? inputConflict : inputBase}
          />
          <span className="text-meta text-text-muted shrink-0">–</span>
          <input
            id="float-max"
            type="number"
            min="0"
            step="1000000"
            value={gainerFilter.floatMax ?? ""}
            onChange={handleFloatMaxChange}
            aria-label="Float Max"
            className={floatConflict ? inputConflict : inputBase}
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
