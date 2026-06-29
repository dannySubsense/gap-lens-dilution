import type { AdminSummaryResponse, UsageWriteRequest, RefreshBalanceResponse } from "../types/admin";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const ADMIN_KEY = process.env.NEXT_PUBLIC_ADMIN_API_KEY ?? "";

function adminHeaders(extra?: Record<string, string>): Record<string, string> {
  return {
    ...(ADMIN_KEY ? { Authorization: `Bearer ${ADMIN_KEY}` } : {}),
    ...extra,
  };
}

export async function fetchAdminSummary(): Promise<AdminSummaryResponse> {
  const response = await fetch(`${BASE_URL}/api/v1/admin/summary`, {
    headers: adminHeaders(),
  });
  if (!response.ok) {
    throw new Error(`Admin summary fetch failed: ${response.status}`);
  }
  return response.json() as Promise<AdminSummaryResponse>;
}

export async function postUsageRecord(body: UsageWriteRequest): Promise<{ ok: boolean }> {
  const response = await fetch(`${BASE_URL}/api/v1/admin/usage`, {
    method: "POST",
    headers: adminHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  return response.json() as Promise<{ ok: boolean }>;
}

export class RefreshBalanceApiError extends Error {
  code: string;
  constructor(code: string, message: string) {
    super(message);
    this.name = "RefreshBalanceApiError";
    this.code = code;
  }
}

export function errorCodeToMessage(err: unknown): string {
  if (err instanceof RefreshBalanceApiError) {
    switch (err.code) {
      case "null_usage":
        return "AskEdgar data unavailable — balance may be $0.00 or API key exhausted.";
      case "rate_limit":
        return "AskEdgar rate limit reached. Try again shortly.";
      case "timeout":
        return "AskEdgar request timed out. Try again.";
      case "network":
        return "Balance refresh failed. Check network connection.";
      case "capture_failed":
      case "api_error":
      default:
        return "AskEdgar returned an error. Balance not updated.";
    }
  }
  // fetch() threw before a response arrived (DNS failure, connection refused, etc.)
  return "Balance refresh failed. Check network connection.";
}

export async function refreshBalance(): Promise<RefreshBalanceResponse> {
  const response = await fetch(`${BASE_URL}/api/v1/admin/refresh-balance`, {
    method: "POST",
    headers: adminHeaders(),
  });
  if (!response.ok) {
    // Default values cover 401, 403, and any non-JSON body.
    let code = "api_error";
    let detail = `Balance refresh failed: ${response.status}`;
    try {
      const body = await response.json() as { code?: string; detail?: string };
      if (body.code) code = body.code;
      if (body.detail) detail = body.detail;
    } catch {
      // Body is not JSON (e.g., TailscaleGuardMiddleware 403 plain-text).
      // Defaults above are used.
    }
    throw new RefreshBalanceApiError(code, detail);
  }
  return response.json() as Promise<RefreshBalanceResponse>;
}
