"use client";

import { useState } from "react";

interface TickerSearchProps {
  onSearch: (ticker: string) => void;
  isLoading?: boolean;
}

export default function TickerSearch({ onSearch, isLoading }: TickerSearchProps) {
  const [ticker, setTicker] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = ticker.trim().toUpperCase();
    if (trimmed) {
      onSearch(trimmed);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={ticker}
        onChange={(e) => setTicker(e.target.value.toUpperCase())}
        placeholder="Enter ticker symbol..."
        className="flex-1 bg-bg-input border border-border-card rounded-[var(--radius-sm)] px-3 py-2.5 text-text-primary text-sm font-[JetBrains_Mono,ui-monospace,monospace] placeholder:text-text-muted focus:outline-none focus:border-accent uppercase"
        disabled={isLoading}
      />
      <button
        type="submit"
        disabled={isLoading}
        className="bg-accent hover:bg-[#ff6fbf] disabled:bg-accent/50 disabled:cursor-not-allowed text-[#0a0c12] text-sm font-bold px-5 py-2.5 rounded-[var(--radius-sm)] transition-colors cursor-pointer"
      >
        {isLoading ? "Loading..." : "Search"}
      </button>
    </form>
  );
}
