import type {
  DilutionResponse,
  HeaderData,
  Headline,
  RiskAssessment,
  RiskLevel,
  InPlayDilutionData,
  WarrantItem,
  ConvertibleItem,
  JMT415Note,
  FilingType,
  OfferingEntry,
  OwnershipData,
  OwnerEntry,
  ChartAnalysis,
  ChartRating,
} from "@/types/dilution";

// ── Number formatting helpers ─────────────────────────────────────────────

export function formatNum(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2).replace(/\.?0+$/, "")}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2).replace(/\.?0+$/, "")}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

export function parseNumericString(s: string | null): number | null {
  if (!s) return null;
  // Strip leading $ and trailing multiplier letters, then parse
  const cleaned = s.replace(/[$,]/g, "").trim();
  const match = cleaned.match(/^([\d.]+)([KkMmBb]?)$/);
  if (!match) return null;
  const base = parseFloat(match[1]);
  const suffix = match[2].toUpperCase();
  if (suffix === "K") return base * 1_000;
  if (suffix === "M") return base * 1_000_000;
  if (suffix === "B") return base * 1_000_000_000;
  return base;
}

export function safeRiskLevel(value: string | null): RiskLevel {
  const allowed: RiskLevel[] = ["Low", "Medium", "High", "N/A"];
  if (value && (allowed as string[]).includes(value)) return value as RiskLevel;
  return "N/A";
}

// ── Helper: map raw API news item to Headline ─────────────────────────────

// The backend may return news with snake_case fields; map them to Headline shape.
export interface RawNewsItem {
  form_type?: string;
  filed_at?: string;
  created_at?: string;
  title?: string;
  summary?: string;
  // Already-mapped fields (if backend already conforms)
  filingType?: string;
  filedAt?: string;
  headline?: string;
}

export const VALID_FILING_TYPES: FilingType[] = [
  "6-K", "8-K", "S-1", "10-K", "10-Q", "SC 13D", "SC 13G", "GROK", "news", "jmt415",
];

export function toFilingType(raw: string | undefined): FilingType {
  if (!raw) return "news";
  if ((VALID_FILING_TYPES as string[]).includes(raw)) return raw as FilingType;
  return "news";
}

export function mapNewsItem(item: RawNewsItem): Headline {
  const filingType = toFilingType(item.filingType ?? item.form_type);
  const filedAt = item.filedAt ?? item.filed_at ?? item.created_at ?? new Date().toISOString();
  const headline = item.headline ?? item.title ?? item.summary ?? "";
  return { filingType, filedAt, headline };
}

// ── buildHeaderData ───────────────────────────────────────────────────────

export function toDisplayNum(val: any): string {
  if (val === null || val === undefined) return "—";
  if (typeof val === "number") return formatNum(val);
  if (typeof val === "string") {
    const parsed = parseNumericString(val);
    return parsed !== null ? formatNum(parsed) : val;
  }
  return "—";
}

// ── mapChartAnalysis ─────────────────────────────────────────────────────

export const HISTORY_MAP: Record<string, { label: string; badgeColor: string }> = {
  green: { label: "Strong", badgeColor: "#2F7D57" },
  yellow: { label: "Semi-Strong", badgeColor: "#B9A816" },
  orange: { label: "Mixed", badgeColor: "#B96A16" },
  red: { label: "Fader", badgeColor: "#A93232" },
};

export function mapChartAnalysis(raw: any | null): ChartAnalysis | null {
  if (!raw) return null;
  const rating = raw.rating;
  if (!rating || !HISTORY_MAP[rating]) return null;
  const { label, badgeColor } = HISTORY_MAP[rating];
  return { rating, label, badgeColor };
}

export function buildHeaderData(d: DilutionResponse): HeaderData {
  return {
    ticker: d.ticker,
    float: toDisplayNum(d.float),
    outstandingShares: toDisplayNum(d.outstanding),
    marketCap: toDisplayNum(d.marketCap),
    sector: d.sector ?? d.industry ?? "—",
    country: d.country ?? "—",
    overallRisk: safeRiskLevel(d.offeringRisk),
    stockPrice: d.stockPrice ?? null,
    chartAnalysis: mapChartAnalysis(d.chartAnalysis),
  };
}

// ── buildRiskData ─────────────────────────────────────────────────────────

export function buildRiskData(d: DilutionResponse): RiskAssessment {
  return {
    overallRisk: safeRiskLevel(d.offeringRisk),
    offering: safeRiskLevel(d.offeringAbility),
    dilution: safeRiskLevel(d.dilutionRisk),
    frequency: safeRiskLevel(d.offeringFrequency),
    cashNeed: safeRiskLevel(d.cashNeed),
    warrants: safeRiskLevel(d.warrantExercise),
  };
}

// ── buildInPlayData ───────────────────────────────────────────────────────

export function buildInPlayData(d: DilutionResponse): InPlayDilutionData {
  const stockPrice = d.stockPrice ?? null;

  const warrants: WarrantItem[] = (d.warrants ?? []).map((w) => {
    const strike = w.warrants_exercise_price ?? 0;
    return {
      details: w.details ?? "",
      issueDate: w.filed_at ? w.filed_at.slice(0, 7) : "—",
      remaining: w.warrants_remaining ?? 0,
      strikePrice: strike,
      filedDate: w.filed_at ? w.filed_at.slice(0, 10) : "—",
      registered: w.registered ?? "—",
      inTheMoney: stockPrice !== null && strike > 0 ? strike <= stockPrice : false,
    };
  });

  const convertibles: ConvertibleItem[] = (d.convertibles ?? []).map((c) => {
    const convPrice = c.conversion_price ?? 0;
    return {
      details: c.details ?? "",
      sharesRemaining: c.underlying_shares_remaining ?? 0,
      conversionPrice: convPrice,
      filedDate: c.filed_at ? c.filed_at.slice(0, 10) : "—",
      registered: c.registered ?? "—",
      inTheMoney: stockPrice !== null && convPrice > 0 ? convPrice <= stockPrice : false,
    };
  });

  return { warrants, convertibles, stockPrice };
}

// ── extractJMT415 ─────────────────────────────────────────────────────────

export function extractJMT415(news: Headline[] | RawNewsItem[]): JMT415Note[] {
  const rawItems = news as RawNewsItem[];
  const jmtItems = rawItems.filter(
    (item) => (item.form_type ?? item.filingType) === "jmt415"
  );

  return jmtItems.map((item) => {
    const date = (item.filed_at ?? item.filedAt ?? "").slice(0, 10);
    const rawText = item.title ?? item.headline ?? item.summary ?? "";
    const content = rawText ? rawText.split("\n").filter(Boolean) : [];
    return {
      date,
      ticker: "",
      content,
    };
  });
}

// ── mapNewsToHeadlines ────────────────────────────────────────────────────

export function mapNewsToHeadlines(news: Headline[] | RawNewsItem[]): Headline[] {
  return (news as RawNewsItem[]).map(mapNewsItem);
}

// ── mapOfferings ─────────────────────────────────────────────────────────
// API returns snake_case; component expects camelCase + computed fields

export function mapOfferings(raw: any[], stockPrice: number | null): OfferingEntry[] {
  return raw.map((o) => {
    const sp = o.share_price ?? o.sharePrice ?? null;
    const headline = o.headline ?? "—";
    return {
      headline,
      offeringAmount: o.offering_amount ?? o.offeringAmount ?? null,
      sharePrice: sp,
      sharesAmount: o.shares_amount ?? o.sharesAmount ?? null,
      warrantsAmount: o.warrants_amount ?? o.warrantsAmount ?? null,
      filedAt: o.filed_at ?? o.filedAt ?? null,
      isAtmUsed: headline.toUpperCase().includes("ATM USED"),
      inTheMoney: sp !== null && stockPrice !== null && sp > 0 && stockPrice > 0 && sp <= stockPrice,
    };
  });
}

// ── mapOwnership ─────────────────────────────────────────────────────────

export function mapOwnership(raw: any | null): OwnershipData | null {
  if (!raw) return null;
  const owners: OwnerEntry[] = (raw.owners ?? []).map((o: any) => ({
    ownerName: o.owner_name ?? o.ownerName ?? "—",
    title: o.title ?? o.owner_type ?? "—",
    commonSharesAmount: o.common_shares_amount ?? o.commonSharesAmount ?? null,
    documentUrl: o.document_url ?? o.documentUrl ?? null,
  }));
  if (owners.length === 0) return null;
  return {
    reportedDate: raw.reported_date ?? raw.reportedDate ?? "—",
    owners,
  };
}
