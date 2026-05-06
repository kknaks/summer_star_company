"use client";

import Icon from "@/components/pixel/Icon";
import type { IconName } from "@/components/pixel/icons";

export interface TabItem {
  key: string;
  label: string;
  icon: IconName;
}

interface TabsProps {
  items: TabItem[];
  active: string | null;
  onSelect: (key: string) => void;
  rightSlot?: React.ReactNode;
}

export default function Tabs({
  items,
  active,
  onSelect,
  rightSlot,
}: TabsProps) {
  return (
    <div className="tabs" style={{ marginTop: 6 }}>
      {items.map((p) => (
        <div
          key={p.key}
          className={`tab ${active === p.key ? "active" : ""}`}
          onClick={() => onSelect(p.key)}
          role="tab"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              onSelect(p.key);
            }
          }}
        >
          <span
            style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
          >
            <Icon name={p.icon} scale={1} />
            {p.label}
          </span>
        </div>
      ))}
      {rightSlot && (
        <>
          <div style={{ flex: 1 }} />
          {rightSlot}
        </>
      )}
    </div>
  );
}
