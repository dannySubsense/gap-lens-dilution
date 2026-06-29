"use client";
import { useState, useEffect } from "react";
import {
  fetchAdminSummary,
  refreshBalance,
  errorCodeToMessage,
  RefreshBalanceApiError,
} from "../../services/adminApi";
import type { AdminSummaryResponse } from "../../types/admin";

type PageState = "loading" | "populated" | "error";
type RefreshState = "idle" | "pending" | "success" | "error";

const KNOWN_CONSUMERS = ["danny", "kenny", "jt", "market-data"];

/** Strips T separator, fractional seconds, and +00:00 / Z suffix. */
function formatTs(ts: string): string {
  return ts
    .replace("T", " ")
    .replace(/\.\d+/, "")
    .replace("+00:00", "")
    .replace(/Z$/, "")
    .trim();
}

// ── AlertBanner ──────────────────────────────────────────────────────────────

function AlertBanner({
  balance_dollars,
  alert_threshold_dollars,
}: {
  balance_dollars: number | null;
  alert_threshold_dollars: number;
}) {
  return (
    <div
      className="w-full border rounded p-3 mb-4"
      style={{
        borderColor: "var(--color-accent-magenta)",
        color: "var(--color-accent-magenta)",
      }}
    >
      <span className="text-section">
        Balance Alert: $
        {balance_dollars !== null ? balance_dollars.toFixed(2) : "—"}{" "}
        remaining — below threshold ($
        {alert_threshold_dollars.toFixed(2)})
      </span>
    </div>
  );
}

// ── BalancePanel ─────────────────────────────────────────────────────────────

interface BalancePanelProps {
  state: PageState;
  data: AdminSummaryResponse | null;
  refreshState: RefreshState;
  lastRefreshCost: number | null;
  refreshError: string | null;
  onRefresh: () => void;
}

function BalancePanel({
  state,
  data,
  refreshState,
  lastRefreshCost,
  refreshError,
  onRefresh,
}: BalancePanelProps) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      className="border rounded p-4 min-w-48"
      style={{
        borderColor: "var(--color-border-card)",
        background: "var(--color-bg-card)",
      }}
    >
      <div
        className="text-label mb-1"
        style={{ color: "var(--color-text-secondary)" }}
      >
        Current Balance
      </div>

      {data !== null && data.balance_dollars !== null ? (
        <>
          <button
            data-testid="balance-refresh-button"
            aria-label="Refresh balance, costs approximately $0.004"
            title="Click to refresh (~$0.004)"
            disabled={refreshState === "pending"}
            onClick={onRefresh}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            className="text-section mt-1"
            style={{
              cursor: refreshState === "pending" ? "not-allowed" : "pointer",
              opacity: refreshState === "pending" ? 0.5 : 1,
              background: "transparent",
              border: "none",
              padding: 0,
              color:
                hovered && refreshState !== "pending"
                  ? "var(--color-accent-violet)"
                  : "var(--color-text-primary)",
            }}
          >
            <span data-testid="balance-value">
              ${data.balance_dollars.toFixed(2)}
            </span>
            {refreshState !== "pending" && (
              <span aria-hidden="true"> ↻</span>
            )}
          </button>
          {data.balance_ts !== null && (
            <div
              data-testid="balance-timestamp"
              className="text-meta mt-1"
              style={{ color: "var(--color-text-muted)" }}
            >
              as of {formatTs(data.balance_ts)} UTC
            </div>
          )}
        </>
      ) : (
        <>
          <button
            data-testid="balance-refresh-button"
            aria-label="Refresh balance, costs approximately $0.004"
            title="Click to refresh (~$0.004)"
            disabled={refreshState === "pending"}
            onClick={onRefresh}
            style={{
              cursor: refreshState === "pending" ? "not-allowed" : "pointer",
              opacity: refreshState === "pending" ? 0.5 : 1,
              background: "transparent",
              border: "none",
              padding: 0,
              color: "var(--color-text-muted)",
            }}
          >
            <span aria-hidden="true">↻</span>
          </button>
          <div
            className="text-meta"
            style={{ color: "var(--color-text-muted)" }}
          >
            {state === "loading" ? "Loading…" : "No data"}
          </div>
        </>
      )}

      <div className="mt-3">
        {refreshState === "success" && (
          <div
            data-testid="refresh-cost"
            className="text-meta mt-1"
            style={{ color: "var(--color-text-muted)" }}
          >
            {lastRefreshCost !== null
              ? `Refresh cost: $${lastRefreshCost.toFixed(6)}`
              : "Refresh cost: unavailable"}
          </div>
        )}
        {refreshState === "error" && (
          <div
            data-testid="refresh-error"
            className="text-meta mt-1"
            style={{ color: "var(--color-accent-magenta)" }}
          >
            {refreshError}
          </div>
        )}
      </div>
    </div>
  );
}

// ── ConsumerSummaryTable ─────────────────────────────────────────────────────

function ConsumerSummaryTable({
  state,
  data,
}: {
  state: PageState;
  data: AdminSummaryResponse | null;
}) {
  const unknownRow =
    state === "populated" && data !== null
      ? (data.consumer_summary_7d.find(
          (r) => r.consumer === "unknown" && r.total_cost_dollars > 0
        ) ?? null)
      : null;

  return (
    <table className="w-full border-collapse">
      <thead>
        <tr>
          <th
            className="text-label text-left py-1 px-2 border-b"
            style={{
              color: "var(--color-text-secondary)",
              borderColor: "var(--color-border-card)",
            }}
          >
            Consumer
          </th>
          <th
            className="text-label text-left py-1 px-2 border-b"
            style={{
              color: "var(--color-text-secondary)",
              borderColor: "var(--color-border-card)",
            }}
          >
            7-Day Total
          </th>
          <th
            className="text-label text-left py-1 px-2 border-b"
            style={{
              color: "var(--color-text-secondary)",
              borderColor: "var(--color-border-card)",
            }}
          >
            By Endpoint
          </th>
        </tr>
      </thead>
      <tbody>
        {KNOWN_CONSUMERS.map((name) => {
          if (state === "loading") {
            return (
              <tr key={name}>
                <td
                  className="text-meta py-1 px-2"
                  style={{ color: "var(--color-text-primary)" }}
                >
                  {name}
                </td>
                <td
                  className="text-meta py-1 px-2"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  —
                </td>
                <td
                  className="text-meta py-1 px-2"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  —
                </td>
              </tr>
            );
          }
          const row = (data?.consumer_summary_7d ?? []).find(
            (r) => r.consumer === name
          ) ?? { consumer: name, total_cost_dollars: 0, by_endpoint: [] };
          return (
            <tr key={name}>
              <td
                className="text-meta py-1 px-2 align-top"
                style={{ color: "var(--color-text-primary)" }}
              >
                {row.consumer}
              </td>
              <td
                className="text-meta py-1 px-2 align-top"
                style={{ color: "var(--color-text-primary)" }}
              >
                ${row.total_cost_dollars.toFixed(4)}
              </td>
              <td
                className="text-meta py-1 px-2 align-top"
                style={{ color: "var(--color-text-primary)" }}
              >
                {row.by_endpoint.length === 0 ? (
                  <span
                    className="text-meta"
                    style={{ color: "var(--color-text-muted)" }}
                  >
                    No activity
                  </span>
                ) : (
                  row.by_endpoint.map((ep) => (
                    <div key={ep.endpoint} className="flex gap-4">
                      <span
                        className="text-meta"
                        style={{ color: "var(--color-text-primary)" }}
                      >
                        {ep.endpoint}
                      </span>
                      <span
                        className="text-meta"
                        style={{ color: "var(--color-text-muted)" }}
                      >
                        ${ep.total_cost_dollars.toFixed(4)}
                      </span>
                    </div>
                  ))
                )}
              </td>
            </tr>
          );
        })}
        {unknownRow !== null && (
          <tr>
            <td
              className="text-meta py-1 px-2 align-top"
              style={{ color: "var(--color-text-primary)" }}
            >
              Unattributed
            </td>
            <td
              className="text-meta py-1 px-2 align-top"
              style={{ color: "var(--color-text-primary)" }}
            >
              ${unknownRow.total_cost_dollars.toFixed(4)}
            </td>
            <td
              className="text-meta py-1 px-2 align-top"
              style={{ color: "var(--color-text-muted)" }}
            >
              (not attributable by endpoint)
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
}

// ── RecentRequestsSection ────────────────────────────────────────────────────

function RecentRequestsSection({
  state,
  data,
}: {
  state: PageState;
  data: AdminSummaryResponse | null;
}) {
  const heading = (
    <div
      className="text-section mb-2"
      style={{ color: "var(--color-text-primary)" }}
    >
      Recent Requests (last 50)
    </div>
  );

  if (state === "loading") {
    return (
      <div>
        {heading}
        <div className="text-meta" style={{ color: "var(--color-text-muted)" }}>
          Loading…
        </div>
      </div>
    );
  }

  if (state !== "populated" || data === null) return null;

  const requests = data.recent_requests;

  return (
    <div>
      {heading}
      {requests.length === 0 ? (
        <div className="text-meta" style={{ color: "var(--color-text-muted)" }}>
          No requests logged yet
        </div>
      ) : (
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th
                className="text-label text-left py-1 px-2 border-b"
                style={{
                  color: "var(--color-text-secondary)",
                  borderColor: "var(--color-border-card)",
                }}
              >
                Timestamp (UTC)
              </th>
              <th
                className="text-label text-left py-1 px-2 border-b"
                style={{
                  color: "var(--color-text-secondary)",
                  borderColor: "var(--color-border-card)",
                }}
              >
                Consumer
              </th>
              <th
                className="text-label text-left py-1 px-2 border-b"
                style={{
                  color: "var(--color-text-secondary)",
                  borderColor: "var(--color-border-card)",
                }}
              >
                Endpoint
              </th>
              <th
                className="text-label text-left py-1 px-2 border-b"
                style={{
                  color: "var(--color-text-secondary)",
                  borderColor: "var(--color-border-card)",
                }}
              >
                Ticker
              </th>
              <th
                className="text-label text-left py-1 px-2 border-b"
                style={{
                  color: "var(--color-text-secondary)",
                  borderColor: "var(--color-border-card)",
                }}
              >
                Cost
              </th>
            </tr>
          </thead>
          <tbody>
            {requests.map((req) => (
              <tr key={req.id}>
                <td
                  className="text-meta py-1 px-2"
                  style={{ color: "var(--color-text-primary)" }}
                >
                  {formatTs(req.ts)}
                </td>
                <td
                  className="text-meta py-1 px-2"
                  style={{ color: "var(--color-text-primary)" }}
                >
                  {req.consumer}
                </td>
                <td
                  className="text-meta py-1 px-2"
                  style={{ color: "var(--color-text-primary)" }}
                >
                  {req.endpoint}
                </td>
                <td
                  className="text-meta py-1 px-2"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  {req.ticker !== null ? req.ticker : "—"}
                </td>
                <td
                  className="text-meta py-1 px-2"
                  style={{ color: "var(--color-text-primary)" }}
                >
                  ${req.cost_dollars.toFixed(4)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ── ErrorState ───────────────────────────────────────────────────────────────

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center gap-4 py-8">
      <div className="text-meta" style={{ color: "var(--color-text-muted)" }}>
        Failed to load usage data.
      </div>
      <button
        className="text-label border rounded px-4 py-2"
        style={{
          borderColor: "var(--color-border-card)",
          color: "var(--color-text-primary)",
          background: "var(--color-bg-card)",
        }}
        onClick={onRetry}
      >
        Retry
      </button>
    </div>
  );
}

// ── AdminPage ────────────────────────────────────────────────────────────────

export default function AdminPage() {
  const [pageState, setPageState] = useState<PageState>("loading");
  const [data, setData] = useState<AdminSummaryResponse | null>(null);
  const [refreshState, setRefreshState] = useState<RefreshState>("idle");
  const [lastRefreshCost, setLastRefreshCost] = useState<number | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);

  const loadData = () => {
    setPageState("loading");
    fetchAdminSummary()
      .then((result) => {
        setData(result);
        setPageState("populated");
      })
      .catch(() => {
        setPageState("error");
      });
  };

  const silentUpdateSummary = () => {
    fetchAdminSummary()
      .then((result) => {
        setData(result);
      })
      .catch(() => {
        // Swallow error silently — new balance row already written to DB;
        // next full page load will display the updated balance.
      });
  };

  const handleRefresh = async () => {
    if (refreshState === "pending") return;
    setRefreshState("pending");
    setRefreshError(null);
    try {
      const result = await refreshBalance();
      setLastRefreshCost(result.cost_dollars);
      setRefreshState("success");
      silentUpdateSummary();
    } catch (err) {
      setRefreshState("error");
      setRefreshError(errorCodeToMessage(err));
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      className="min-h-screen p-6"
      style={{
        background: "var(--color-bg-primary)",
        color: "var(--color-text-primary)",
      }}
    >
      {pageState === "populated" &&
        data !== null &&
        data.alert_triggered && (
          <AlertBanner
            balance_dollars={data.balance_dollars}
            alert_threshold_dollars={data.alert_threshold_dollars}
          />
        )}

      <div className="flex items-start justify-between mb-6">
        <h1
          className="text-section"
          style={{ color: "var(--color-text-primary)" }}
        >
          AskEdgar Usage — Admin
        </h1>
        <BalancePanel
          state={pageState}
          data={data}
          refreshState={refreshState}
          lastRefreshCost={lastRefreshCost}
          refreshError={refreshError}
          onRefresh={handleRefresh}
        />
      </div>

      {pageState === "error" ? (
        <ErrorState onRetry={loadData} />
      ) : (
        <>
          <div
            className="border rounded p-4 mb-6"
            style={{
              borderColor: "var(--color-border-card)",
              background: "var(--color-bg-card)",
            }}
          >
            <div
              className="text-section mb-3"
              style={{ color: "var(--color-text-primary)" }}
            >
              7-Day Cost Summary
            </div>
            <ConsumerSummaryTable state={pageState} data={data} />
          </div>

          <div
            className="border rounded p-4"
            style={{
              borderColor: "var(--color-border-card)",
              background: "var(--color-bg-card)",
            }}
          >
            <RecentRequestsSection state={pageState} data={data} />
          </div>
        </>
      )}
    </div>
  );
}
