import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Cold Start AI",
  description:
    "Autonomous GTM engine — positioning, ICP, channels, messaging, playbooks, sequences, and metrics.",
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
