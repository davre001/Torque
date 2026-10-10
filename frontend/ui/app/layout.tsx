import type { Metadata } from "next";
import { Space_Grotesk, Space_Mono } from "next/font/google";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const spaceMono = Space_Mono({
  variable: "--font-space-mono",
  subsets: ["latin"],
  weight: ["400", "700"],
});

export const metadata: Metadata = {
  title: "Torque — Turn Issues Into Pull Requests",
  description:
    "An autonomous multi-agent system that turns a GitHub issue into a verified pull request — and recovers when it fails.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${spaceMono.variable} dark`}
    >
      <body className="min-h-screen bg-[#0D1117] text-[#E6EDF3] antialiased">
        {children}
      </body>
    </html>
  );
}
