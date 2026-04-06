"use client";

import { useEffect, useRef, useState } from "react";

declare global {
  interface Window {
    TradingView: any;
  }
}

interface TradingViewChartProps {
  ticker: string | null;
  selectCount: number;
  interval: string;
  label: string;
  overrideTicker: string | null;
  showDropdown: boolean;
  watchlistTickers: string[];
  onTickerOverride: (interval: string, ticker: string | null) => void;
}

export default function TradingViewChart({
  ticker,
  selectCount,
  interval,
  label,
  overrideTicker,
  showDropdown,
  watchlistTickers,
  onTickerOverride,
}: TradingViewChartProps) {
  const [status, setStatus] = useState<"idle" | "loading" | "ready" | "error">(
    "idle"
  );

  const containerIdRef = useRef<string>(
    `tradingview-chart-${Math.random().toString(36).slice(2)}`
  );
  const containerId = containerIdRef.current;

  const prevTickerRef = useRef<string | null>(null);
  const prevIntervalRef = useRef<string>(interval);
  const statusRef = useRef<"idle" | "loading" | "ready" | "error">("idle");

  // Sync statusRef to status on every render
  statusRef.current = status;

  // Derive effective symbol:
  // - Linked mode: always follow the active ticker
  // - Independent mode: use the pinned override, or hold the last displayed ticker
  //   (prevTickerRef) so clicking a gainer doesn't reset all charts
  const effectiveTicker = showDropdown
    ? (overrideTicker ?? prevTickerRef.current ?? ticker)
    : ticker;

  useEffect(() => {
    let mounted = true;

    if (!effectiveTicker) return;

    // Dedup check
    const tickerUnchanged = effectiveTicker === prevTickerRef.current;
    const intervalUnchanged = interval === prevIntervalRef.current;

    if (tickerUnchanged && intervalUnchanged) {
      if (statusRef.current === "ready") return;
      if (statusRef.current === "loading") return;
      // statusRef.current === "error" falls through (forced retry)
    }

    // Dedup passed — update refs and proceed
    prevTickerRef.current = effectiveTicker;
    prevIntervalRef.current = interval;

    setStatus("loading");

    // Clear previous chart DOM
    document.getElementById(containerId)?.replaceChildren();

    const createWidget = () => {
      try {
        new window.TradingView.widget({
          container_id: containerId,
          symbol: effectiveTicker,
          interval: interval,
          theme: "dark",
          autosize: true,
          backgroundColor: "#1b2230",
          gridColor: "#2a3447",
          hide_top_toolbar: false,
          allow_symbol_change: false,
          save_image: false,
          locale: "en",
          timezone: "America/New_York",
          extended_hours: true,
        });
        if (!mounted) return;
        setStatus("ready");
      } catch {
        if (!mounted) return;
        setStatus("error");
      }
    };

    // If TradingView is already loaded, create widget directly
    if (window.TradingView) {
      createWidget();
    } else {
      const script = document.createElement("script");
      script.src = "https://s3.tradingview.com/tv.js";
      script.type = "text/javascript";
      script.onload = createWidget;
      script.onerror = () => {
        if (!mounted) return;
        setStatus("error");
      };
      document.head.appendChild(script);
    }

    return () => {
      mounted = false;
    };
  }, [effectiveTicker, interval, selectCount]);

  if (ticker === null && overrideTicker === null) {
    return (
      <div className="flex-1 min-h-0 bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-2 flex items-center justify-center">
      </div>
    );
  }

  return (
    <div className="flex-1 min-h-0 bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-2 flex flex-col">
      {/* Chart header — dropdown only in independent mode */}
      {showDropdown && (
        <div className="shrink-0 mb-1 flex items-center">
          <select
            value={overrideTicker ?? ticker ?? ""}
            onChange={(e) => onTickerOverride(interval, e.target.value || null)}
            disabled={watchlistTickers.length === 0}
            className="text-xs text-[#eef1f8] bg-[#1b2230] border border-[#2a3447] rounded-[5px] px-2 py-0.5 cursor-pointer focus:outline-none focus:border-[#a78bfa] min-w-[80px] disabled:opacity-50"
          >
            {watchlistTickers.length === 0
              ? <option disabled value="">No tickers</option>
              : watchlistTickers.map(t => <option key={t} value={t}>{t}</option>)
            }
          </select>
        </div>
      )}

      {/* Chart area — container + overlays as siblings */}
      <div className="flex-1 min-h-0" style={{ position: "relative" }}>
        {/* TradingView mount target */}
        <div
          id={containerId}
          style={{ height: "100%", width: "100%" }}
        />

        {/* Skeleton overlay — loading state */}
        {status === "loading" && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              background: "#1b2230",
              borderRadius: "5px",
            }}
            className="animate-pulse"
          />
        )}

        {/* Error state */}
        {status === "error" && (
          <div
            className="flex flex-col items-center justify-center"
            style={{ position: "absolute", inset: 0 }}
          >
            <p className="text-[#9aa7c7] text-xs text-center">
              Chart unavailable
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
