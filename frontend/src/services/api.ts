import type { ApiResult, DilutionResponse, GainerEntry } from "../types/dilution";

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
