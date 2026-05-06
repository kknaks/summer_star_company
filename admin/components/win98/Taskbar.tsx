"use client";

import Icon from "@/components/pixel/Icon";

import Clock from "./Clock";

interface TaskbarProps {
  onStart: () => void;
  startOpen?: boolean;
  activeTask?: string;
}

export default function Taskbar({
  onStart,
  startOpen,
  activeTask,
}: TaskbarProps) {
  return (
    <div className="taskbar">
      <div
        className={`start-btn ${startOpen ? "active" : ""}`}
        onClick={onStart}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onStart();
          }
        }}
      >
        <Icon name="star" scale={1} />
        <span>시작</span>
      </div>
      {activeTask && (
        <div className="task-btn active">
          <Icon name="computer" scale={1} />
          <span>{activeTask}</span>
        </div>
      )}
      <div className="tray">
        <span style={{ fontSize: 12 }}>🔊</span>
        <Clock />
      </div>
    </div>
  );
}
