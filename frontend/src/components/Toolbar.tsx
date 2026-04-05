"use client";

import { useState } from "react";
import { useAppSettings } from "@/context/AppSettingsContext";

interface ToolbarProps {
  activeTicker: string | null;
}

export default function Toolbar({ activeTicker }: ToolbarProps) {
  const { openSettings, addToWatchlist, isSettingsOpen } = useAppSettings();
  const [showFullMessage, setShowFullMessage] = useState<string | null>(null);

  function handleAddClick() {
    if (activeTicker !== null) {
      const result = addToWatchlist(activeTicker.toUpperCase());
      if (result.outcome === "full") {
        setShowFullMessage("Watchlist full");
        setTimeout(() => setShowFullMessage(null), 600);
      }
    }
  }

  return (
    <div className="flex h-12 items-center px-4 bg-[#1b2230] border-b border-[#2a3447] shrink-0">
      {/* Left: logo + branding */}
      <div className="flex items-center">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 32 32"
          width={24}
          height={24}
        >
          <rect x="4" y="18" width="5" height="10" fill="#ec4899" />
          <rect x="13" y="12" width="5" height="16" fill="#ec4899" />
          <rect x="22" y="4" width="5" height="24" fill="#ec4899" />
        </svg>
        <span className="text-sm font-bold text-[#eef1f8] ml-2">Gap Lens</span>
      </div>

      {/* Center spacer */}
      <div className="flex-1" />

      {/* Right: action buttons */}
      <div className="flex items-center gap-1">
        {showFullMessage && (
          <span className="text-xs text-[#ff6b6b] mr-2">{showFullMessage}</span>
        )}

        {/* Add to Watchlist button */}
        <button
          title="Add to Watchlist"
          onClick={handleAddClick}
          disabled={!activeTicker}
          className={[
            "p-2 rounded-[5px] transition-colors",
            activeTicker
              ? "text-[#9aa7c7] hover:text-[#eef1f8] hover:bg-[#2a3447]"
              : "text-[#9aa7c7] opacity-50 cursor-not-allowed",
          ].join(" ")}
        >
          {/* Bookmark / plus icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width={16}
            height={16}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
            <line x1="12" y1="9" x2="12" y2="15" />
            <line x1="9" y1="12" x2="15" y2="12" />
          </svg>
        </button>

        {/* Settings gear button */}
        <button
          title="Settings"
          onClick={openSettings}
          className={[
            "p-2 rounded-[5px] transition-colors",
            isSettingsOpen
              ? "text-[#a78bfa]"
              : "text-[#9aa7c7] hover:text-[#eef1f8] hover:bg-[#2a3447]",
          ].join(" ")}
        >
          {/* Gear icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width={16}
            height={16}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        </button>
      </div>
    </div>
  );
}
