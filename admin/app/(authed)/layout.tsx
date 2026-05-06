"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

import Icon from "@/components/pixel/Icon";
import type { IconName } from "@/components/pixel/icons";
import Clock from "@/components/win98/Clock";
import Mascot from "@/components/win98/Mascot";
import MenuBar from "@/components/win98/MenuBar";
import StartMenu, {
  StartMenuItem,
  StartMenuSeparator,
} from "@/components/win98/StartMenu";
import StatusBar from "@/components/win98/StatusBar";
import Tabs, { type TabItem } from "@/components/win98/Tabs";
import Taskbar from "@/components/win98/Taskbar";
import TitleBar from "@/components/win98/TitleBar";
import { getToken, clearToken } from "@/lib/api/client";

const TABS: TabItem[] = [
  { key: "logs", label: "출입 로그", icon: "log" },
  { key: "users", label: "사용자", icon: "user" },
  { key: "stats", label: "통계", icon: "chart" },
];

function resolveActive(pathname: string): {
  key: string;
  label: string;
  icon: IconName;
} {
  if (pathname.startsWith("/logs")) {
    return { key: "logs", label: "출입 로그", icon: "log" };
  }
  if (pathname.startsWith("/users")) {
    const isDetail = /^\/users\/[^/]+/.test(pathname);
    return {
      key: "users",
      label: isDetail ? "사용자 상세" : "사용자",
      icon: "user",
    };
  }
  if (pathname.startsWith("/stats")) {
    return { key: "stats", label: "통계", icon: "chart" };
  }
  return { key: "logs", label: "출입 로그", icon: "log" };
}

export default function AuthedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const [startOpen, setStartOpen] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
    } else {
      setReady(true);
    }
  }, [router]);

  if (!ready) return null;

  const active = resolveActive(pathname);
  const titleText = `Summer Star Admin — ${active.label}`;

  const onLogout = () => {
    clearToken();
    router.replace("/login");
  };

  const onSelectTab = (key: string) => {
    setStartOpen(false);
    router.push(`/${key}`);
  };

  return (
    <>
      <div className="desktop">
        <div className="app-window">
          <div className="window">
            <TitleBar
              title={titleText}
              icon={active.icon}
              onClose={onLogout}
            />
            <MenuBar items={["파일", "편집", "보기", "도구", "도움말"]} />
            <Tabs
              items={TABS}
              active={active.key}
              onSelect={onSelectTab}
              rightSlot={
                <div
                  className="tab hide-mobile"
                  onClick={onLogout}
                  role="button"
                  tabIndex={0}
                  style={{ cursor: "pointer" }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onLogout();
                    }
                  }}
                >
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 4,
                    }}
                  >
                    <Icon name="power" scale={1} />
                    로그아웃
                  </span>
                </div>
              }
            />
            <div className="tab-panel">{children}</div>
            <StatusBar
              left={<span>준비됨</span>}
              mid={
                <span className="mono hide-mobile">접속: admin</span>
              }
              right={<Clock />}
            />
          </div>
          <Mascot />
        </div>
      </div>

      <Taskbar
        onStart={() => setStartOpen((o) => !o)}
        startOpen={startOpen}
        activeTask={titleText}
      />

      {startOpen && (
        <StartMenu onClose={() => setStartOpen(false)}>
          {TABS.map((t) => (
            <StartMenuItem
              key={t.key}
              icon={t.icon}
              label={t.label}
              onClick={() => onSelectTab(t.key)}
            />
          ))}
          <StartMenuSeparator />
          <StartMenuItem icon="gear" label="설정" />
          <StartMenuSeparator />
          <StartMenuItem icon="power" label="로그아웃" onClick={onLogout} />
        </StartMenu>
      )}
    </>
  );
}
