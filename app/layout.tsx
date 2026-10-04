import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BOUGHT Spotlight — The daily issue",
  description: "One finite daily issue for the business and technology world.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
