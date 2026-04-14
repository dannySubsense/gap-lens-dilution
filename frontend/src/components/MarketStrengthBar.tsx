"use client";

import { useState, useEffect, useRef } from "react";
import type { MarketStrengthData, PumpDumpData } from "@/types/dilution";
import { fetchMarketStrength, fetchPumpAndDumpList } from "@/services/api";
import PumpDumpHotList from "./PumpDumpHotList";

// ── Emoji code replacements ──────────────────────────────────────────────

const EMOJI_MAP: Record<string, string> = {
  ":arrow_up:": "↑",
  ":arrow_down:": "↓",
  ":orange_circle:": "●",
  ":red_circle:": "●",
  ":green_circle:": "●",
};

function replaceEmojis(text: string): string {
  let result = text;
  for (const [code, symbol] of Object.entries(EMOJI_MAP)) {
    result = result.replaceAll(code, symbol);
  }
  return result.trim();
}

// ── Performance text parser ──────────────────────────────────────────────

interface ParsedPerformance {
  header: string;
  stats: { label: string; value: string }[];
  tableHeader: string;
  tableRows: string[][];
}

function parsePerformance(text: string): ParsedPerformance {
  const lines = text.split("\n");
  const result: ParsedPerformance = { header: "", stats: [], tableHeader: "", tableRows: [] };

  let inTable = false;
  let headerSkipped = false;

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;

    // Bold header: **...**
    if (line.startsWith("**") && line.endsWith("**") && !inTable) {
      const text = line.replace(/\*\*/g, "").trim();
      if (text.toLowerCase().includes("listed below")) {
        result.tableHeader = text;
      } else {
        result.header = text;
      }
      continue;
    }

    // Code block markers
    if (line === "```") {
      inTable = !inTable;
      headerSkipped = false;
      continue;
    }

    if (inTable) {
      // Skip the header row and separator
      if (!headerSkipped) {
        if (line.startsWith("---") || line.startsWith("Sym")) {
          if (line.startsWith("---")) headerSkipped = true;
          continue;
        }
      }
      // Parse table row: split on 2+ spaces
      const cells = line.split(/\s{2,}/).map(c => c.trim()).filter(Boolean);
      if (cells.length >= 4) {
        result.tableRows.push(cells);
      }
      continue;
    }

    // Stats line: "Label: Value :emoji:"
    const colonIdx = line.indexOf(":");
    if (colonIdx > 0 && colonIdx < line.length - 1) {
      const label = line.slice(0, colonIdx).trim();
      const value = replaceEmojis(line.slice(colonIdx + 1));
      result.stats.push({ label, value });
    }
  }

  return result;
}

// ── Arrow color helper ───────────────────────────────────────────────────

function arrowColor(value: string): string {
  if (value.includes("↑")) return "text-[#5ce08a]";
  if (value.includes("↓")) return "text-[#ff6b6b]";
  return "text-[#9aa7c7]";
}

function closeColor(close: string): string {
  if (close.toLowerCase() === "green") return "text-[#5ce08a]";
  if (close.toLowerCase() === "red") return "text-[#ff6b6b]";
  return "text-[#9aa7c7]";
}

// ── Component ────────────────────────────────────────────────────────────

export default function MarketStrengthBar() {
  const [marketStrength, setMarketStrength] = useState<MarketStrengthData | null>(null);
  const [pdList, setPdList] = useState<PumpDumpData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      const [msResult, pdResult] = await Promise.all([
        fetchMarketStrength(),
        fetchPumpAndDumpList(),
      ]);

      if (msResult.ok) setMarketStrength(msResult.data);
      else setError(msResult.message);

      if (pdResult.ok) setPdList(pdResult.data);

      setIsLoading(false);
    }

    load();

    intervalRef.current = setInterval(async () => {
      const result = await fetchPumpAndDumpList();
      if (result.ok) setPdList(result.data);
    }, 5 * 60 * 1000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const parsed = marketStrength?.performance ? parsePerformance(marketStrength.performance) : null;

  return (
    <div className="flex flex-col gap-4 p-3">
      {/* Market Strength — Analysis */}
      <div>
        <div className="text-[#9aa7c7] text-[10px] uppercase tracking-widest mb-1">Market Strength</div>
        {isLoading ? (
          <>
            <div className="bg-[#2a3447] animate-pulse h-4 rounded mb-2 w-3/4" />
            <div className="bg-[#2a3447] animate-pulse h-3 rounded w-1/2" />
          </>
        ) : error && !marketStrength ? (
          <p className="text-[#9aa7c7] text-xs italic">Market data unavailable</p>
        ) : marketStrength && !marketStrength.analysis && !marketStrength.performance ? (
          <p className="text-[#9aa7c7] text-xs italic">No market analysis today</p>
        ) : marketStrength ? (
          <p className="text-[#9aa7c7] text-xs leading-relaxed whitespace-pre-wrap">{marketStrength.analysis}</p>
        ) : null}
      </div>

      {/* Gap Scanner Stats */}
      {parsed && parsed.stats.length > 0 && (
        <div>
          {parsed.header && (
            <div className="text-[#eef1f8] text-xs font-semibold mb-2">{parsed.header}</div>
          )}
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            {parsed.stats.map((stat, i) => (
              <div key={i} className="flex justify-between text-[10px]">
                <span className="text-[#9aa7c7]">{stat.label}</span>
                <span className={`font-mono ${arrowColor(stat.value)}`}>{stat.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Gapper Table */}
      {parsed && parsed.tableRows.length > 0 && (
        <div>
          {parsed.tableHeader && (
            <div className="text-[#9aa7c7] text-[10px] uppercase tracking-widest mb-1">{parsed.tableHeader}</div>
          )}
          <table className="w-full text-[10px]">
            <thead>
              <tr className="text-[#9aa7c7] uppercase tracking-widest">
                <th className="text-left py-0.5 pr-2">Sym</th>
                <th className="text-left py-0.5 pr-2">Date</th>
                <th className="text-right py-0.5 pr-2">Gap%</th>
                <th className="text-center py-0.5 pr-2">Close</th>
                <th className="text-right py-0.5 pr-2">Vol</th>
                <th className="text-right py-0.5 pr-2">Float</th>
                <th className="text-left py-0.5 pr-2">Range</th>
                <th className="text-left py-0.5">Ctry</th>
              </tr>
            </thead>
            <tbody>
              {parsed.tableRows.map((row, i) => {
                // row: [Sym, Date, Gap%, Close, Vol, Float, Range, Ind, Ctry]
                const [sym, date, gap, close, vol, float_, range, , ctry] = row;
                return (
                  <tr key={i} className="border-t border-[#2a3447]/50">
                    <td className="text-[#63D3FF] font-mono font-bold py-0.5 pr-2">{sym}</td>
                    <td className="text-[#9aa7c7] py-0.5 pr-2">{date?.slice(5)}</td>
                    <td className="text-[#eef1f8] text-right font-mono py-0.5 pr-2">{gap}</td>
                    <td className={`text-center py-0.5 pr-2 ${closeColor(close ?? "")}`}>{close}</td>
                    <td className="text-[#9aa7c7] text-right py-0.5 pr-2">{vol}</td>
                    <td className="text-[#9aa7c7] text-right py-0.5 pr-2">{float_}</td>
                    <td className="text-[#9aa7c7] py-0.5 pr-2">{range}</td>
                    <td className="text-[#9aa7c7] py-0.5">{ctry}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* P&D Hot List */}
      <PumpDumpHotList items={pdList.slice(0, 10)} isLoading={isLoading} error={error} />
    </div>
  );
}
