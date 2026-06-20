import type { AdminSummaryResponse, UsageWriteRequest } from "../types/admin";

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
