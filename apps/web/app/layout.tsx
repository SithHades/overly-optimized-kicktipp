import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "WorldCupQuant",
  description: "Football prediction terminal and Tipp-Spiel optimizer"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
