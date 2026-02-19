import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://asenda.ai"),
  title: "Asenda.ai - Intelligent Voice AI & Automation",
  description:
    "Transform customer interactions with intelligent voice AI agents. AI helpdesk, voice sales, marketing automation, and more. Enterprise-grade solutions for modern businesses.",
  keywords: [
    "voice AI",
    "AI agents",
    "customer service automation",
    "AI helpdesk",
    "voice automation",
    "sales automation",
    "conversational AI",
  ],
  authors: [{ name: "Asenda AI" }],
  creator: "Asenda AI",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://asenda.ai",
    siteName: "Asenda.ai",
    title: "Asenda.ai - Intelligent Voice AI & Automation",
    description:
      "Transform customer interactions with intelligent voice AI agents. AI helpdesk, voice sales, marketing automation, and more.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Asenda.ai - Voice AI Platform",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Asenda.ai - Intelligent Voice AI & Automation",
    description:
      "Transform customer interactions with intelligent voice AI agents.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        <Navbar />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
