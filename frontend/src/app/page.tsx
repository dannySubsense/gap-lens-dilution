"use client";

import Header from "@/components/Header";
import Headlines from "@/components/Headlines";
import RiskBadges from "@/components/RiskBadges";
import OfferingAbility from "@/components/OfferingAbility";
import InPlayDilution from "@/components/InPlayDilution";
import JMT415Notes from "@/components/JMT415Notes";
import TickerSearch from "@/components/TickerSearch";
import type {
  HeaderData,
  Headline,
  RiskAssessment,
  OfferingAbilityData,
  InPlayDilutionData,
  JMT415Note,
} from "@/types/dilution";

const PLACEHOLDER_HEADER: HeaderData = {
  ticker: "EEIQ",
  float: "917K",
  outstandingShares: "1.48M",
  marketCap: "12.62M",
  sector: "Consumer Defensive",
  country: "US",
  overallRisk: "Low",
};

const PLACEHOLDER_HEADLINES: Headline[] = [
  {
    filingType: "6-K",
    filedAt: "2026-03-27T15:20:00Z",
    headline:
      "EpicQuest Education Group International Limited Announces 2026 Annual Meeting of Shareholders",
  },
  {
    filingType: "6-K",
    filedAt: "2026-03-27T15:20:00Z",
    headline:
      "EpicQuest Education Group International Limited Announces Annual Meeting of Shareholders",
  },
  {
    filingType: "GROK",
    filedAt: "2026-03-30T04:50:00Z",
    headline:
      '\u2022 **Momentum continuation from recent partnership announcement**: EEIQ surged last week (March 24-28) following news of an online education partnership with as highlighted in a Reddit pennystocks recap; today\'s 20.6% gai...',
  },
];

const PLACEHOLDER_RISK: RiskAssessment = {
  overallRisk: "Low",
  offering: "Low",
  dilution: "High",
  frequency: "Medium",
  cashNeed: "Low",
  warrants: "Low",
};

const PLACEHOLDER_OFFERING: OfferingAbilityData = {
  shelfCapacity: "$0.00M",
  shelfCapacityConcerning: true,
  hasATM: false,
  hasEquityLine: false,
  hasS1Offering: false,
};

const PLACEHOLDER_INPLAY: InPlayDilutionData = {
  warrants: [
    {
      description: "Warrants to purchase Ordinary Shares",
      issueDate: "May 2025",
      remaining: "844K",
      strikePrice: "$7.68",
      filedDate: "2025-05-30",
    },
  ],
};

const PLACEHOLDER_JMT415: JMT415Note[] = [
  {
    date: "2026-03-27",
    ticker: "ONCO",
    content: [
      "- Realbotix Corp. announced that one of its humanoid robots, which had been purchased by Ericsson \u2014 Realbotix's first enterprise client \u2014 was featured in Ericsson's recently completed live pre-standard 6G over-the-air (OTA) trial conducted at Ericsson's U.S. headquarters in Plano, Texas. Onconetix is sharing this development with its shareholders as it relates to the capabilities of Realbotix, the target of the pending acquisition.",
      "- was yesterday afternoon and no reaction so likely just low float (700k) sympathy to some of the others like UGRO and EEIQ",
      "- convertibles should have already reset 90 days following shareholder approval and can be converted at discount to vwap, as low as $3.70-$3.80 (around 4.2M shares total)",
      "- i think they can be reset even lower since they did a split but wasnt clear if the floor price also lowered following shareholder approval in december",
      "- mostly faders but has demonstrated early strength out the gate before fading",
    ],
  },
  {
    date: "2026-03-26",
    ticker: "EEIQ",
    content: [
      "- Partnership announcement with online education platform driving momentum",
      "- Low float play with 917K float, watch for volume spikes",
      "- No significant dilution risk from offerings but warrants at $7.68 strike are in play",
    ],
  },
];

export default function Home() {
  function handleSearch(ticker: string) {
    console.log("Search:", ticker);
  }

  return (
    <main className="max-w-4xl mx-auto p-4 space-y-4">
      <TickerSearch onSearch={handleSearch} />
      <Header data={PLACEHOLDER_HEADER} />
      <Headlines data={PLACEHOLDER_HEADLINES} />
      <RiskBadges data={PLACEHOLDER_RISK} />
      <OfferingAbility data={PLACEHOLDER_OFFERING} />
      <InPlayDilution data={PLACEHOLDER_INPLAY} />
      <JMT415Notes data={PLACEHOLDER_JMT415} />
    </main>
  );
}
