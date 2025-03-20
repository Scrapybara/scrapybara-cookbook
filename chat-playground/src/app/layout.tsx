import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Computer Use Playground",
  description: "Computer use chat playground powered by Scrapybara",
  icons: [{ rel: "icon", url: "/icon.png" }],
  openGraph: {
    type: "website",
    locale: "en_US",
    url: process.env.NEXT_PUBLIC_VERCEL_PROJECT_PRODUCTION_URL,
    siteName: "Computer Use Playground",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Computer Use Playground",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    site: "@scrapybara",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body className="antialiased dark">
        <Toaster richColors />
        {children}
      </body>
    </html>
  );
}
