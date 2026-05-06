import type { Metadata, Viewport } from "next";

import RegisterSW from "@/components/RegisterSW";

import "./globals.css";

export const metadata: Metadata = {
  title: "Summer Star Admin",
  description: "사무실 출입 관리",
  applicationName: "Summer Star Admin",
  icons: {
    icon: [
      { url: "/icons/favicon-32.png", sizes: "32x32", type: "image/png" },
      { url: "/icons/favicon-64.png", sizes: "64x64", type: "image/png" },
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
    ],
    apple: { url: "/icons/apple-touch-icon.png" },
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "SSC Admin",
  },
  formatDetection: {
    telephone: false,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
  themeColor: "#000080",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>
        {children}
        <RegisterSW />
      </body>
    </html>
  );
}
