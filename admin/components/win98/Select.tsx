"use client";

import { useEffect, useRef, useState } from "react";

interface SelectOption<T extends string> {
  value: T;
  label: React.ReactNode;
}

interface SelectProps<T extends string> {
  value: T;
  onChange: (value: T) => void;
  options: SelectOption<T>[];
  className?: string;
  style?: React.CSSProperties;
  ariaLabel?: string;
}

export default function Select<T extends string>({
  value,
  onChange,
  options,
  className,
  style,
  ariaLabel,
}: SelectProps<T>) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const current = options.find((o) => o.value === value);

  return (
    <div
      ref={ref}
      className={className}
      style={{ position: "relative", display: "inline-block", ...style }}
    >
      <button
        type="button"
        className="select"
        onClick={() => setOpen((o) => !o)}
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        style={{
          textAlign: "left",
          width: "100%",
          cursor: "pointer",
        }}
      >
        {current?.label ?? value}
      </button>
      {open && (
        <ul
          role="listbox"
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            zIndex: 40,
            margin: 0,
            padding: 2,
            listStyle: "none",
            background: "var(--win-bg)",
            boxShadow:
              "inset 1px 1px 0 var(--win-white), inset -1px -1px 0 var(--win-bg-darker), inset 2px 2px 0 var(--win-bg-light), inset -2px -2px 0 var(--win-bg-dark)",
          }}
        >
          {options.map((opt) => {
            const selected = opt.value === value;
            return (
              <li
                key={opt.value}
                role="option"
                aria-selected={selected}
                onClick={() => {
                  onChange(opt.value);
                  setOpen(false);
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--title-blue)";
                  e.currentTarget.style.color = "var(--win-white)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "var(--win-black)";
                }}
                style={{
                  padding: "4px 8px",
                  cursor: "pointer",
                  fontSize: 14,
                  whiteSpace: "nowrap",
                  background: "transparent",
                }}
              >
                {selected ? "✓ " : "  "}
                {opt.label}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
