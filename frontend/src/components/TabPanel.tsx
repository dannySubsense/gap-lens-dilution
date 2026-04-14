"use client";

import type { TabId, TabDefinition } from "@/types/dilution";

interface TabPanelProps {
  tabs: TabDefinition[];
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  panels: Record<TabId, React.ReactNode>;
}

export default function TabPanel({ tabs, activeTab, onTabChange, panels }: TabPanelProps) {
  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Tab bar */}
      <div className="flex border-b border-[#2a3447] shrink-0">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={
              tab.id === activeTab
                ? "px-4 py-2 text-sm text-[#eef1f8] border-b-2 border-[#a78bfa] cursor-default"
                : "px-4 py-2 text-sm text-[#9aa7c7] cursor-pointer hover:text-[#eef1f8] transition-colors"
            }
            onClick={() => {
              if (tab.id !== activeTab) onTabChange(tab.id);
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Active panel content */}
      <div className="flex-1 overflow-y-auto">
        {panels[activeTab]}
      </div>
    </div>
  );
}
