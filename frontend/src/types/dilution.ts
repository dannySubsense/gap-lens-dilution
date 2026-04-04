// frontend/src/types/dilution.ts  (full V2 replacement)

export type RiskLevel = "Low" | "Medium" | "High" | "N/A";

export type ChartRating = "green" | "yellow" | "orange" | "red";

// ── Existing types (unchanged) ────────────────────────────────────────────

export interface HeaderData {
  ticker: string;
  float: string;
  outstandingShares: string;
  marketCap: string;
  sector: string;
  country: string;
  overallRisk: RiskLevel;
  // V2 additions
  stockPrice: number | null;
  chartAnalysis: ChartAnalysis | null;
}

export type FilingType =
  | "6-K"
  | "8-K"
  | "S-1"
  | "10-K"
  | "10-Q"
  | "SC 13D"
  | "SC 13G"
  | "GROK"
  | "news"
  | "jmt415";

export interface Headline {
  filingType: FilingType;
  filedAt: string;
  headline: string;
}

export interface RiskAssessment {
  overallRisk: RiskLevel;
  offering: RiskLevel;
  dilution: RiskLevel;
  frequency: RiskLevel;
  cashNeed: RiskLevel;
  warrants: RiskLevel;
}

export interface JMT415Note {
  date: string;
  ticker: string;
  content: string[];
}

// ── V2: OfferingAbility rework ────────────────────────────────────────────

export interface OfferingAbilityData {
  /** Raw description string from AskEdgar, comma-separated segments */
  offeringAbilityDesc: string | null;
}

// ── V2: In-Play Dilution extension ───────────────────────────────────────

export interface WarrantItem {
  details: string;
  issueDate: string;        // formatted from filed_at
  remaining: number;        // warrants_remaining (raw number)
  strikePrice: number;      // warrants_exercise_price
  filedDate: string;        // filed_at YYYY-MM-DD
  registered: string;
  inTheMoney: boolean;      // computed: strikePrice <= stockPrice
}

export interface ConvertibleItem {
  details: string;
  sharesRemaining: number;  // underlying_shares_remaining
  conversionPrice: number;  // conversion_price
  filedDate: string;
  registered: string;
  inTheMoney: boolean;      // computed: conversionPrice <= stockPrice
}

export interface InPlayDilutionData {
  warrants: WarrantItem[];
  convertibles: ConvertibleItem[];
  stockPrice: number | null;
}

// ── V2: New panel types ───────────────────────────────────────────────────

export interface GapStatEntry {
  date: string;
  gap_percentage: number | null;
  market_open: number | null;
  high_price: number | null;
  low_price: number | null;
  market_close: number | null;
  high_time: string | null;
  closed_over_vwap: boolean | null;
  volume: number | null;
}

export interface GapStatsComputed {
  lastGapDate: string | null;
  numGaps: number;
  avgGapPct: number;
  avgOpenToHigh: number;
  avgOpenToLow: number;
  pctNewHighAfter11am: number;
  pctClosedBelowVwap: number;
  pctClosedBelowOpen: number;
}

export interface OfferingEntry {
  headline: string | null;
  offeringAmount: number | null;
  sharePrice: number | null;
  sharesAmount: number | null;
  warrantsAmount: number | null;
  filedAt: string | null;
  isAtmUsed: boolean;       // computed: headline contains "ATM USED" case-insensitive
  inTheMoney: boolean;      // computed: sharePrice <= stockPrice and both > 0
}

export interface OwnerEntry {
  ownerName: string;
  title: string;
  commonSharesAmount: number | null;
  documentUrl: string | null;
}

export interface OwnershipData {
  reportedDate: string;
  owners: OwnerEntry[];
}

export interface ChartAnalysis {
  rating: ChartRating;
  label: string;            // derived: "Strong" | "Semi-Strong" | "Mixed" | "Fader"
  badgeColor: string;       // derived from HISTORY_MAP
}

// ── V2: Gainers ────────────────────────────────────────────────────────────

export interface GainerEntry {
  ticker: string;
  todaysChangePerc: number;
  price: number;
  volume: number;
  float: number | null;
  marketCap: number | null;
  sector: string | null;
  country: string | null;
  risk: RiskLevel | null;
  chartRating: ChartRating | null;
  newsToday: boolean;
}

// ── V2: Full dilution response shape (from backend) ───────────────────────

export interface DilutionResponse {
  ticker: string;
  offeringRisk: string | null;
  offeringAbility: string | null;
  offeringAbilityDesc: string | null;
  dilutionRisk: string | null;
  dilutionDesc: string | null;
  offeringFrequency: string | null;
  cashNeed: string | null;
  cashNeedDesc: string | null;
  cashRunway: number | null;
  cashBurn: number | null;
  estimatedCash: number | null;
  warrantExercise: string | null;
  warrantExerciseDesc: string | null;
  float: number | string | null;
  outstanding: number | string | null;
  marketCap: number | string | null;
  industry: string | null;
  sector: string | null;
  country: string | null;
  insiderOwnership: number | null;
  institutionalOwnership: number | null;
  news: Headline[];
  registrations: unknown[];
  warrants: RawWarrantItem[];
  convertibles: RawConvertibleItem[];
  // V2 additions
  gapStats: GapStatEntry[];
  offerings: OfferingEntry[];
  ownership: OwnershipData | null;
  chartAnalysis: ChartAnalysis | null;
  stockPrice: number | null;
  mgmtCommentary: string | null;
}

// Raw backend shapes before frontend transformation
export interface RawWarrantItem {
  details: string | null;
  warrants_exercise_price: number | null;
  warrants_remaining: number | null;
  warrants_amount: number | null;
  filed_at: string | null;
  registered: string | null;
}

export interface RawConvertibleItem {
  details: string | null;
  conversion_price: number | null;
  underlying_shares_remaining: number | null;
  filed_at: string | null;
  registered: string | null;
}

// ── V2: API service result types ─────────────────────────────────────────

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; status: 404 | 429 | 500; message: string };
