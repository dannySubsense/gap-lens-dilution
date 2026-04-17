import type {
  DilutionResponse,
  PumpDumpData,
  ComplianceRecord,
  ReverseSplitRecord,
  FilingTitle,
  HistoricalFloatPoint,
  ResearchReportData,
} from "@/types/dilution";

export const TICKER_CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

export interface TickerCacheEntry {
  storedAt: number;
  dilution: DilutionResponse;
  pumpDump: PumpDumpData | null;
  complianceRecords: ComplianceRecord[];
  reverseSplits: ReverseSplitRecord[];
  filingTitles: FilingTitle[];
  historicalFloat: HistoricalFloatPoint[];
  researchReport: ResearchReportData | null;
}

export type TickerCacheMap = Map<string, TickerCacheEntry>;

export function getCacheEntry(
  cache: TickerCacheMap,
  ticker: string,
): TickerCacheEntry | null {
  const key = ticker.toUpperCase();
  const entry = cache.get(key);
  if (!entry) return null;
  if (Date.now() - entry.storedAt >= TICKER_CACHE_TTL_MS) return null;
  return entry;
}

export function setCacheEntry(
  cache: TickerCacheMap,
  ticker: string,
  entry: Omit<TickerCacheEntry, "storedAt">,
): void {
  const key = ticker.toUpperCase();
  cache.set(key, { ...entry, storedAt: Date.now() });
}
