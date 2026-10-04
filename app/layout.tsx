import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BOUGHT Spotlight — Today's issue",
  description: "A daily global business and technology issue, with a public stage for the people building what comes next.",
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
