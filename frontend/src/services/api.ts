import type {
  ApiResult,
  DilutionResponse,
  GainerEntry,
  MarketStrengthData,
  PumpDumpData,
  ComplianceRecord,
  ReverseSplitRecord,
  FilingTitle,
  HistoricalFloatPoint,
  ResearchReportData,
  BatchEnrichmentResult,
  GainerEnrichment,
} from "../types/dilution";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function fetchDilution(
  ticker: string,
  signal?: AbortSignal
): Promise<ApiResult<DilutionResponse>> {
  try {
    const resp = await fetch(
      `${BASE_URL}/api/v1/dilution/${encodeURIComponent(ticker)}`,
      { signal }
    );
    if (resp.ok) {
      const data = await resp.json();
      return { ok: true, data };
    }
    if (resp.status === 404) {
      return { ok: false, status: 404, message: `No dilution data available for ${ticker}` };
    }
    if (resp.status === 429) {
      return { ok: false, status: 429, message: "Rate limit exceeded. Try again later." };
    }
    return { ok: false, status: 500, message: "API error. Please retry." };
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      return { ok: false, status: 500, message: "Request aborted" };
    }
    return { ok: false, status: 500, message: "API error. Please retry." };
  }
}

export async function fetchGainers(
  signal?: AbortSignal
): Promise<ApiResult<GainerEntry[]>> {
  try {
    const resp = await fetch(`${BASE_URL}/api/v1/gainers`, { signal });
    if (resp.ok) {
      const data = await resp.json();
      return { ok: true, data };
    }
    return { ok: false, status: 500, message: "Could not load gainers." };
  } catch {
    return { ok: false, status: 500, message: "Could not load gainers." };
  }
}

export async function fetchMassiveGainers(
  signal?: AbortSignal
): Promise<ApiResult<GainerEntry[]>> {
  try {
    const resp = await fetch(`${BASE_URL}/api/v1/gainers/massive`, { signal });
    if (resp.ok) {
      const data = await resp.json();
      return { ok: true, data };
    }
    return { ok: false, status: 500, message: "Could not load Massive gainers." };
  } catch {
    return { ok: false, status: 500, message: "Could not load Massive gainers." };
  }
}

export async function fetchFmpGainers(
  signal?: AbortSignal
): Promise<ApiResult<GainerEntry[]>> {
  try {
    const resp = await fetch(`${BASE_URL}/api/v1/gainers/fmp`, { signal });
    if (resp.ok) {
      const data = await resp.json();
      return { ok: true, data };
    }
    return { ok: false, status: 500, message: "Could not load FMP gainers." };
  } catch {
    return { ok: false, status: 500, message: "Could not load FMP gainers." };
  }
}

export async function fetchMarketStrength(
  signal?: AbortSignal
): Promise<ApiResult<MarketStrengthData>> {
  try {
    const resp = await fetch(`${BASE_URL}/api/v1/market-strength`, { signal });
    if (resp.ok) {
      const data = await resp.json();
      // Fields are already camelCase-compatible: date, analysis, performance
      return { ok: true, data };
    }
    return { ok: false, status: 500, message: "Could not load market strength." };
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      return { ok: false, status: 500, message: "Request aborted" };
    }
    return { ok: false, status: 500, message: "Could not load market strength." };
  }
}

export async function fetchPumpAndDump(
  ticker: string,
  signal?: AbortSignal
): Promise<ApiResult<PumpDumpData | null>> {
  try {
    const resp = await fetch(
      `${BASE_URL}/api/v1/pump-and-dump/${encodeURIComponent(ticker)}`,
      { signal }
    );
    if (resp.ok) {
      const raw = await resp.json();
      if (!raw) return { ok: true, data: null };
      const data: PumpDumpData = {
        ticker: raw.ticker,
        tradableFloat: raw.tradable_float ?? null,
        countryRisk: raw.country_risk ?? null,
        scamRisk: raw.scam_risk ?? null,
        floatRisk: raw.float_risk ?? null,
        underwriterRisk: raw.underwriter_risk ?? null,
        scamDescription: raw.scam_description ?? null,
        gain1Day: raw.gain_1_day ?? null,
        gain7Day: raw.gain_7_day ?? null,
      };
      return { ok: true, data };
    }
    if (resp.status === 404) return { ok: true, data: null };
    return { ok: false, status: 500, message: "Could not load P&D data." };
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      return { ok: false, status: 500, message: "Request aborted" };
    }
    return { ok: false, status: 500, message: "Could not load P&D data." };
  }
}

export async function fetchPumpAndDumpList(
  signal?: AbortSignal
): Promise<ApiResult<PumpDumpData[]>> {
  try {
    const resp = await fetch(`${BASE_URL}/api/v1/pump-and-dump-list`, { signal });
    if (resp.ok) {
      const rawList = await resp.json();
      const data: PumpDumpData[] = (rawList ?? []).map((raw: any) => ({
        ticker: raw.ticker,
        tradableFloat: raw.tradable_float ?? null,
        countryRisk: raw.country_risk ?? null,
        scamRisk: raw.scam_risk ?? null,
        floatRisk: raw.float_risk ?? null,
        underwriterRisk: raw.underwriter_risk ?? null,
        scamDescription: raw.scam_description ?? null,
        gain1Day: raw.gain_1_day ?? null,
        gain7Day: raw.gain_7_day ?? null,
      }));
      return { ok: true, data };
    }
    return { ok: false, status: 500, message: "Could not load P&D list." };
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      return { ok: false, status: 500, message: "Request aborted" };
    }
    return { ok: false, status: 500, message: "Could not load P&D list." };
  }
}

export async function fetchNasdaqCompliance(
  ticker: string,
  signal?: AbortSignal
): Promise<ApiResult<ComplianceRecord[]>> {
  try {
    const resp = await fetch(
      `${BASE_URL}/api/v1/nasdaq-compliance/${encodeURIComponent(ticker)}`,
      { signal }
    );
    if (resp.ok) {
      const rawList = await resp.json();
      // Fields are already camelCase-compatible (single words)
      return { ok: true, data: rawList ?? [] };
    }
    return { ok: false, status: 500, message: "Could not load compliance data." };
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      return { ok: false, status: 500, message: "Request aborted" };
    }
    return { ok: false, status: 500, message: "Could not load compliance data." };
  }
}

export async function fetchReverseSplits(
  ticker: string,
  signal?: AbortSignal
): Promise<ApiResult<ReverseSplitRecord[]>> {
  try {
    const resp = await fetch(
      `${BASE_URL}/api/v1/reverse-splits/${encodeURIComponent(ticker)}`,
      { signal }
    );
    if (resp.ok) {
      const rawList = await resp.json();
      const data: ReverseSplitRecord[] = (rawList ?? []).map((raw: any) => ({
        ticker: raw.ticker,
        executionDate: raw.execution_date,
        splitFrom: raw.split_from,
        splitTo: raw.split_to,
      }));
      return { ok: true, data };
    }
    return { ok: false, status: 500, message: "Could not load reverse splits." };
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      return { ok: false, status: 500, message: "Request aborted" };
    }
    return { ok: false, status: 500, message: "Could not load reverse splits." };
  }
}

export async function fetchFilingTitles(
  ticker: string,
  signal?: AbortSignal
): Promise<ApiResult<FilingTitle[]>> {
  try {
    const resp = await fetch(
      `${BASE_URL}/api/v1/filing-titles/${encodeURIComponent(ticker)}`,
      { signal }
    );
    if (resp.ok) {
      const rawList = await resp.json();
      const data: FilingTitle[] = (rawList ?? []).map((raw: any) => ({
        headline: raw.headline ?? "",
        formType: raw.form_type ?? "",
        filedAt: raw.filed_at ?? "",
        documentUrl: raw.document_url ?? null,
      }));
      return { ok: true, data };
    }
    return { ok: false, status: 500, message: "Could not load filing titles." };
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      return { ok: false, status: 500, message: "Request aborted" };
    }
    return { ok: false, status: 500, message: "Could not load filing titles." };
  }
}

export async function fetchHistoricalFloat(
  ticker: string,
  signal?: AbortSignal
): Promise<ApiResult<HistoricalFloatPoint[]>> {
  try {
    const resp = await fetch(
      `${BASE_URL}/api/v1/historical-float/${encodeURIComponent(ticker)}`,
      { signal }
    );
    if (resp.ok) {
      const rawList = await resp.json();
      const data: HistoricalFloatPoint[] = (rawList ?? []).map((raw: any) => ({
        reportedDate: raw.reported_date ?? "",
        filedAt: raw.filed_at ?? "",
        float: raw.float ?? null,
        tradableFloat: raw.tradable_float ?? null,
        outstandingShares: raw.outstanding_shares ?? null,
        marketCap: raw.market_cap ?? null,
      }));
      return { ok: true, data };
    }
    return { ok: false, status: 500, message: "Could not load float history." };
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      return { ok: false, status: 500, message: "Request aborted" };
    }
    return { ok: false, status: 500, message: "Could not load float history." };
  }
}

export async function fetchResearchReport(
  ticker: string,
  signal?: AbortSignal
): Promise<ApiResult<ResearchReportData | null>> {
  try {
    const resp = await fetch(
      `${BASE_URL}/api/v1/research-report/${encodeURIComponent(ticker)}`,
      { signal }
    );
    if (resp.ok) {
      const raw = await resp.json();
      if (!raw) return { ok: true, data: null };
      const data: ResearchReportData = {
        ticker: raw.ticker ?? ticker,
        gainPercentage: raw.gain_percentage ?? null,
        reportText: raw.report_text ?? "",
        sections: [],  // populated by caller using parseResearchReport
        createdAt: raw.created_at ?? null,
        tradableFloat: raw.tradable_float ?? null,
        outstanding: raw.outstanding ?? null,
        country: raw.country ?? null,
        industry: raw.industry ?? null,
      };
      return { ok: true, data };
    }
    if (resp.status === 404) return { ok: true, data: null };
    return { ok: false, status: 500, message: "Could not load research report." };
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      return { ok: false, status: 500, message: "Request aborted" };
    }
    return { ok: false, status: 500, message: "Could not load research report." };
  }
}

export async function fetchBatchEnrichment(
  tickers: string[],
  signal?: AbortSignal
): Promise<ApiResult<BatchEnrichmentResult>> {
  try {
    const resp = await fetch(
      `${BASE_URL}/api/v1/enrichment/batch?tickers=${tickers.join(",")}`,
      { signal }
    );
    if (resp.ok) {
      const raw = await resp.json();
      const result: BatchEnrichmentResult = {};
      for (const [ticker, value] of Object.entries(raw ?? {})) {
        const v = value as any;
        const enrichment: GainerEnrichment = {
          pumpdump: v.pumpdump ? {
            ticker: v.pumpdump.ticker,
            tradableFloat: v.pumpdump.tradable_float ?? null,
            countryRisk: v.pumpdump.country_risk ?? null,
            scamRisk: v.pumpdump.scam_risk ?? null,
            floatRisk: v.pumpdump.float_risk ?? null,
            underwriterRisk: v.pumpdump.underwriter_risk ?? null,
            scamDescription: v.pumpdump.scam_description ?? null,
            gain1Day: v.pumpdump.gain_1_day ?? null,
            gain7Day: v.pumpdump.gain_7_day ?? null,
          } : null,
          hasComplianceDeficiency: v.hasComplianceDeficiency ?? false,
          hasReverseSplits: v.hasReverseSplits ?? false,
        };
        result[ticker] = enrichment;
      }
      return { ok: true, data: result };
    }
    return { ok: false, status: 500, message: "Could not load enrichment data." };
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      return { ok: false, status: 500, message: "Request aborted" };
    }
    return { ok: false, status: 500, message: "Could not load enrichment data." };
  }
}
