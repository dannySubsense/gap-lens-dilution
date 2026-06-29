export interface RecentRequestRow {
  id: number;
  ts: string;
  consumer: string;
  endpoint: string;
  ticker: string | null;
  cost_dollars: number;
}

export interface ConsumerEndpointRow {
  endpoint: string;
  total_cost_dollars: number;
}

export interface ConsumerSummaryRow {
  consumer: string;
  total_cost_dollars: number;
  by_endpoint: ConsumerEndpointRow[];
}

export interface AdminSummaryResponse {
  balance_dollars: number | null;
  balance_ts: string | null;
  alert_triggered: boolean;
  alert_threshold_dollars: number;
  consumer_summary_7d: ConsumerSummaryRow[];
  recent_requests: RecentRequestRow[];
}

export interface UsageWriteRequest {
  consumer: string;
  endpoint: string;
  ticker?: string | null;
  cost_microdollars?: number | null;
  credits_remaining_dollars: number;
  ts?: string | null;
}

export interface RefreshBalanceResponse {
  balance_dollars: number;
  balance_ts: string;          // ISO 8601 UTC — same format as AdminSummaryResponse.balance_ts
  cost_dollars: number | null; // null when cost_microdollars absent from dilution-rating response
}
