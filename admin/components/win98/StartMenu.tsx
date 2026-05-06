"use client";

import Icon from "@/components/pixel/Icon";
import type { IconName } from "@/components/pixel/icons";

interface StartMenuItemProps {
  icon: IconName;
  label: string;
  onClick?: () => void;
}

export function StartMenuItem({ icon, label, onClick }: StartMenuItemProps) {
  return (
    <div
      className="item"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick?.();
        }
      }}
    >
      <Icon name={icon} scale={1} />
      {label}
    </div>
  );
}

export function StartMenuSeparator() {
  return <div className="sep-h" />;
}

interface StartMenuProps {
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
}

export default function StartMenu({
  onClose,
  children,
  title = "SSC 98",
}: StartMenuProps) {
  return (
    <>
      <div
        onClick={onClose}
        style={{ position: "fixed", inset: 0, zIndex: 55 }}
      />
      <div className="start-menu">
        <div className="left-strip">{title}</div>
        <div className="items">{children}</div>
      </div>
    </>
  );
}
