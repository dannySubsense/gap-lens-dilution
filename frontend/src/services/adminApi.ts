import type { AdminSummaryResponse, UsageWriteRequest } from "../types/admin";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function fetchAdminSummary(): Promise<AdminSummaryResponse> {
  const response = await fetch(`${BASE_URL}/api/v1/admin/summary`);
  if (!response.ok) {
    throw new Error(`Admin summary fetch failed: ${response.status}`);
  }
  return response.json() as Promise<AdminSummaryResponse>;
}

export async function postUsageRecord(body: UsageWriteRequest): Promise<{ ok: boolean }> {
  const response = await fetch(`${BASE_URL}/api/v1/admin/usage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return response.json() as Promise<{ ok: boolean }>;
}
