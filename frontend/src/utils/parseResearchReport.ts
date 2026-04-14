import type { ReportSection, ReportRiskColor } from "@/types/dilution";

export function parseResearchReport(
  reportText: string | null | undefined
): ReportSection[] {
  // 1. If input is falsy or empty string after trim, return []
  if (!reportText || !reportText.trim()) {
    return [];
  }

  const text = reportText.trim();

  // 2. Use regex to find all **bold-header** boundaries
  const headerRegex = /\*\*([^*]+)\*\*/g;
  const headers: { title: string; index: number; matchLength: number }[] = [];
  let match: RegExpExecArray | null;

  while ((match = headerRegex.exec(text)) !== null) {
    headers.push({
      title: match[1],
      index: match.index,
      matchLength: match[0].length,
    });
  }

  // 5. Edge case: if no bold headers found, return single section
  if (headers.length === 0) {
    return [
      {
        title: "",
        body: text,
        riskColor: null,
      },
    ];
  }

  // 3. For each header: extract emoji prefix, strip emoji from title,
  //    capture body text between this header and next
  const emojiMap: Record<string, ReportRiskColor> = {
    "🔴": "red",
    "🟡": "yellow",
    "🟠": "orange",
    "🟢": "green",
  };

  const sections: ReportSection[] = [];

  for (let i = 0; i < headers.length; i++) {
    const header = headers[i];
    let title = header.title.trim();

    // Detect emoji prefix and map to risk color
    let riskColor: ReportRiskColor = null;
    for (const [emoji, color] of Object.entries(emojiMap)) {
      if (title.startsWith(emoji)) {
        riskColor = color;
        title = title.slice(emoji.length).trim();
        break;
      }
    }

    // Capture body: text from end of this header match to start of next header (or end)
    const bodyStart = header.index + header.matchLength;
    const bodyEnd = i + 1 < headers.length ? headers[i + 1].index : text.length;
    const body = text.slice(bodyStart, bodyEnd).trim();

    // 4. Skip entries where title or body is empty after trim
    if (!title && !body) {
      continue;
    }

    sections.push({ title, body, riskColor });
  }

  return sections;
}
