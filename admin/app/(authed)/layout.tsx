"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { getToken, clearToken } from "@/lib/api/client";

const NAV = [
  { href: "/logs", label: "출입 로그" },
  { href: "/users", label: "사용자" },
  { href: "/stats", label: "통계" },
];

export default function AuthedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
    } else {
      setReady(true);
    }
  }, [router]);

  if (!ready) return null;

  const onLogout = () => {
    clearToken();
    router.replace("/login");
  };

  return (
    <div className="flex-1 flex flex-col">
      <header className="border-b bg-white">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="font-semibold">Summer Star Admin</h1>
          <nav className="flex gap-2 items-center">
            {NAV.map((item) => {
              const active =
                pathname === item.href || pathname.startsWith(item.href + "/");
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-1 rounded text-sm ${
                    active
                      ? "bg-neutral-900 text-white"
                      : "hover:bg-neutral-100"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
            <Button variant="outline" size="sm" onClick={onLogout}>
              로그아웃
            </Button>
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-6">
        {children}
      </main>
    </div>
  );
}
