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

const FMP_COUNTRIES = [
  "US",
  "CN",
  "CA",
  "IL",
  "AU",
  "GB",
  "HK",
  "SG",
  "NL",
  "IE",
  "KY",
  "BM",
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
      return;
    }
    setVolumeEmpty(false);
    const val = parseFloat(e.target.value);
    if (!isNaN(val)) {
      setGainerFilter({ ...gainerFilter, volumeMin: val });
    }
  }

  function handleChangePctChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === "") {
      setChangePctEmpty(true);
      return;
    }
    setChangePctEmpty(false);
    const val = parseFloat(e.target.value);
    if (!isNaN(val)) {
      setGainerFilter({ ...gainerFilter, changePctMin: val });
    }
  }

  function handleMcapMaxChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === "") {
      setGainerFilter({ ...gainerFilter, mcapMax: null });
      return;
    }
    const val = parseFloat(e.target.value);
    if (!isNaN(val)) {
      setGainerFilter({ ...gainerFilter, mcapMax: val });
    }
  }

  function handleFloatMaxChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === "") {
      setGainerFilter({ ...gainerFilter, floatMax: null });
      return;
    }
    const val = parseFloat(e.target.value);
    if (!isNaN(val)) {
      setGainerFilter({ ...gainerFilter, floatMax: val });
    }
  }

  function handleReset() {
    setGainerFilter(DEFAULT_GAINER_FILTER);
    setLocalPriceMin(DEFAULT_GAINER_FILTER.priceMin);
    setLocalPriceMax(DEFAULT_GAINER_FILTER.priceMax);
    setPriceConflict(false);
    setVolumeEmpty(false);
    setChangePctEmpty(false);
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

      {/* Volume Min */}
      <div className="mb-3">
        <label
          htmlFor="volume-min"
          className="text-meta text-text-muted mb-1 block"
        >
          Volume Min
        </label>
        <input
          id="volume-min"
          type="number"
          min="0"
          step="1"
          value={gainerFilter.volumeMin}
          onChange={handleVolumeChange}
          className={volumeEmpty ? inputConflict : inputBase}
        />
        {volumeEmpty && (
          <span className="text-label text-negative">Required</span>
        )}
      </div>

      {/* % Change Min */}
      <div className="mb-3">
        <label
          htmlFor="change-pct-min"
          className="text-meta text-text-muted mb-1 block"
        >
          % Change Min
        </label>
        <input
          id="change-pct-min"
          type="number"
          min="0"
          step="0.1"
          value={gainerFilter.changePctMin}
          onChange={handleChangePctChange}
          className={changePctEmpty ? inputConflict : inputBase}
        />
        {changePctEmpty && (
          <span className="text-label text-negative">Required</span>
        )}
      </div>

      {/* Market Cap Max */}
      <div className="mb-3">
        <label
          htmlFor="mcap-max"
          className="text-meta text-text-muted mb-1 block"
        >
          Market Cap Max ($)
        </label>
        <input
          id="mcap-max"
          type="number"
          min="0"
          step="1000000"
          value={gainerFilter.mcapMax ?? ""}
          onChange={handleMcapMaxChange}
          className={inputBase}
        />
      </div>

      {/* Float Max */}
      <div className="mb-3">
        <label
          htmlFor="float-max"
          className="text-meta text-text-muted mb-1 block"
        >
          Float Max (shares)
        </label>
        <input
          id="float-max"
          type="number"
          min="0"
          step="1000000"
          value={gainerFilter.floatMax ?? ""}
          onChange={handleFloatMaxChange}
          className={inputBase}
        />
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
        <label className="text-meta text-text-muted mb-2 block">
          Country Exclude
        </label>
        <div className="flex flex-wrap gap-1.5">
          {FMP_COUNTRIES.map((country) => {
            const isActive = gainerFilter.countryExclude.includes(country);
            return (
              <button
                key={country}
                type="button"
                role="checkbox"
                aria-checked={isActive}
                onClick={() => {
                  const next = isActive
                    ? gainerFilter.countryExclude.filter((c) => c !== country)
                    : [...gainerFilter.countryExclude, country];
                  setGainerFilter({ ...gainerFilter, countryExclude: next });
                }}
                className={
                  isActive
                    ? "text-label text-text-inverse bg-accent-purple border border-accent-purple rounded-full px-2 py-0.5 cursor-pointer"
                    : "text-label text-text-muted border border-border-card rounded-full px-2 py-0.5 cursor-pointer"
                }
              >
                {country}
              </button>
            );
          })}
        </div>
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
