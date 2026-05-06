"use client";

import { useEffect, useState } from "react";

export default function Clock() {
  const [t, setT] = useState<Date | null>(null);

  useEffect(() => {
    setT(new Date());
    const i = setInterval(() => setT(new Date()), 1000);
    return () => clearInterval(i);
  }, []);

  if (!t) return <span className="mono">--:--</span>;

  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    <span className="mono">
      {pad(t.getHours())}:{pad(t.getMinutes())}
    </span>
  );
}
