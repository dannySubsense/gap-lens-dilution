"use client";

import { useEffect } from "react";
import { useAppSettings } from "@/context/AppSettingsContext";
import type { ChartMode } from "@/types/dilution";

export default function SettingsModal() {
  const {
    isSettingsOpen,
    closeSettings,
    settings,
    updateGainerColumns,
    setChartMode,
  } = useAppSettings();

  // Escape key handler
  useEffect(() => {
    if (!isSettingsOpen) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        closeSettings();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isSettingsOpen, closeSettings]);

  if (!isSettingsOpen) return null;

  const { gainerColumns, chartMode } = settings;

  const gainerToggleRows: { key: keyof typeof gainerColumns; label: string }[] = [
    { key: "tradingview", label: "TradingView" },
    { key: "massive", label: "Massive" },
    { key: "fmp", label: "FMP" },
  ];

  const chartModeOptions: { value: ChartMode; label: string }[] = [
    { value: "linked", label: "Linked" },
    { value: "independent", label: "Independent" },
  ];

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 z-50"
        onClick={closeSettings}
      />

      {/* Modal panel */}
      <div
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-[#1b2230] border border-[#2a3447] rounded-[9px] w-80 z-50"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#2a3447]">
          <span className="text-sm font-bold text-[#eef1f8]">Settings</span>
          <button
            className="text-[#9aa7c7] hover:text-[#eef1f8] text-sm p-1 rounded"
            onClick={closeSettings}
            aria-label="Close settings"
          >
            ✕
          </button>
        </div>

        {/* Section body */}
        <div className="px-5 py-4 space-y-6">
          {/* Section 1: Gainer Columns */}
          <div>
            <p className="text-xs font-bold text-[#9aa7c7] uppercase tracking-wide mb-3">
              Gainer Columns
            </p>
            {gainerToggleRows.map(({ key, label }) => {
              const isOn = gainerColumns[key];
              return (
                <div key={key} className="flex items-center justify-between py-1.5">
                  <span className="text-sm text-[#eef1f8]">{label}</span>
                  {/* Pill toggle */}
                  <button
                    role="switch"
                    aria-checked={isOn}
                    onClick={() => updateGainerColumns({ [key]: !isOn })}
                    className={`relative inline-flex items-center w-10 h-5 rounded-full transition-colors focus:outline-none ${
                      isOn ? "bg-[#a78bfa]" : "bg-[#2a3447]"
                    }`}
                  >
                    <span
                      className={`absolute w-4 h-4 rounded-full transition-transform ${
                        isOn
                          ? "translate-x-5 bg-white"
                          : "translate-x-0.5 bg-[#9aa7c7]"
                      }`}
                    />
                  </button>
                </div>
              );
            })}
          </div>

          {/* Section 2: Chart Mode */}
          <div>
            <p className="text-xs font-bold text-[#9aa7c7] uppercase tracking-wide mb-3">
              Chart Mode
            </p>
            {chartModeOptions.map(({ value, label }) => {
              const isSelected = chartMode === value;
              return (
                <div key={value}>
                  <div
                    className="flex items-center gap-3 py-1.5 cursor-pointer"
                    onClick={() => setChartMode(value)}
                  >
                    {/* Custom radio circle */}
                    <span
                      className={`flex items-center justify-center w-4 h-4 rounded-full border border-[#2a3447] shrink-0`}
                    >
                      {isSelected && (
                        <span className="w-2 h-2 rounded-full bg-[#a78bfa]" />
                      )}
                    </span>
                    <span className="text-sm text-[#eef1f8]">{label}</span>
                  </div>
                  {/* Helper text for Independent when selected */}
                  {value === "independent" && isSelected && (
                    <p className="text-xs text-[#9aa7c7] ml-7 mt-0.5">
                      Each chart can be pinned to a watchlist ticker
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </>
  );
}
