/** Maps to AskEdgar API field names for straightforward backend wiring */

export type RiskLevel = "Low" | "Medium" | "High";

export interface HeaderData {
  /** Ticker symbol, e.g. "EEIQ" */
  ticker: string;
  /** Company float shares, e.g. "917K" */
  float: string;
  /** Outstanding shares, e.g. "1.48M" */
  outstandingShares: string;
  /** Market capitalization, e.g. "12.62M" */
  marketCap: string;
  /** Sector classification, e.g. "Consumer Defensive" */
  sector: string;
  /** Country of incorporation, e.g. "US" */
  country: string;
  /** Overall dilution risk level */
  overallRisk: RiskLevel;
}

export type FilingType =
  | "6-K"
  | "8-K"
  | "S-1"
  | "10-K"
  | "10-Q"
  | "SC 13D"
  | "SC 13G"
  | "GROK";

export interface Headline {
  /** SEC filing type or source */
  filingType: FilingType;
  /** ISO timestamp of the filing/post */
  filedAt: string;
  /** Headline or summary text */
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

export interface OfferingAbilityData {
  /** Shelf registration capacity in dollars, e.g. "$0.00M" */
  shelfCapacity: string;
  /** Whether shelf capacity is zero/concerning */
  shelfCapacityConcerning: boolean;
  /** Has active ATM (At-The-Market) offering */
  hasATM: boolean;
  /** Has equity line of credit */
  hasEquityLine: boolean;
  /** Has S-1 registration */
  hasS1Offering: boolean;
}

export interface Warrant {
  /** Description, e.g. "Warrants to purchase Ordinary Shares" */
  description: string;
  /** Issue date, e.g. "May 2025" */
  issueDate: string;
  /** Remaining warrant count, e.g. "844K" */
  remaining: string;
  /** Strike price, e.g. "$7.68" */
  strikePrice: string;
  /** Filing date, e.g. "2025-05-30" */
  filedDate: string;
}

export interface InPlayDilutionData {
  warrants: Warrant[];
}

export interface JMT415Note {
  /** Date of the note, e.g. "2026-03-27" */
  date: string;
  /** Referenced ticker(s) */
  ticker: string;
  /** Note content lines */
  content: string[];
}

export interface DilutionReport {
  header: HeaderData;
  headlines: Headline[];
  riskAssessment: RiskAssessment;
  offeringAbility: OfferingAbilityData;
  inPlayDilution: InPlayDilutionData;
  jmt415Notes: JMT415Note[];
}
